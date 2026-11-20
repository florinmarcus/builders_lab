"""Agent contracts: the JSON passed between the main agent, specialists and verify_answer.

This file is the source of truth (architecture/design/agent-contracts.md explains it).
Changing a model here means a new CONTRACT_VERSION, a regenerated schema file and valid agent examples:
  python -m builders_api.contracts --write     # writes plugin/shared/contracts.schema.json
tests/test_contracts.py checks the schema file is current and the examples in plugin/ are valid.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

CONTRACT_VERSION = "contracts.v3"  # v2: translator messages; v3 (20 Nov 2026): kind "delays"
SCHEMA_FILE = Path(__file__).resolve().parents[3] / "plugin" / "shared" / "contracts.schema.json"

Kind = Literal["inbox", "variations", "payments", "paperwork", "regulations", "delays"]
SourceType = Literal["email", "document", "regulation", "calculation"]
ClaimStatus = Literal["approved", "not_approved", "missing", "present", "expired", "expiring_soon",
                      "deadline", "rule", "info", "action"]
ProblemCode = Literal["SOURCE_NOT_FOUND", "QUOTE_NOT_IN_SOURCE", "NUMBER_NOT_IN_SOURCES", "BANNED_PHRASE",
                      "PERSONAL_DATA", "MISSING_AI_NOTICE", "NO_CLAIMS"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Source(Strict):
    type: SourceType
    id: str = Field(description="email or document uuid; regulation passage key or section; job ref for calculation")
    label: str | None = None
    date: str | None = Field(None, description="YYYY-MM-DD")
    page: int | None = None
    section: str | None = None
    edition_date: str | None = None
    url: str | None = None


class SpecialistTask(Strict):
    contract: Literal["contracts.v3"] = CONTRACT_VERSION
    question: str
    kind: Kind
    job: str | None = None
    as_of_date: str | None = None


class FindingClaim(Strict):
    id: str
    text: str
    status: ClaimStatus
    quote: str = Field("", description="Exact words from the source; empty only for calculation sources")
    source: Source
    values: dict[str, Any] = Field(default_factory=dict)


class Findings(Strict):
    contract: Literal["contracts.v3"] = CONTRACT_VERSION
    kind: Kind
    job: str | None = None
    claims: list[FindingClaim]
    gaps: list[str] = Field(default_factory=list)
    tool_trace_ids: list[str] = Field(default_factory=list)


class ClaimSource(Strict):
    type: SourceType
    id: str


class AnswerClaim(Strict):
    id: str
    quote: str = ""
    source: ClaimSource


class Answer(Strict):
    contract: Literal["contracts.v3"] = CONTRACT_VERSION
    text: str
    claims: list[AnswerClaim] = Field(default_factory=list)


Language = Literal["ro", "en"]


class TranslationIn(Strict):
    """Main agent to translator, start of a turn: the user's own words."""
    contract: Literal["contracts.v3"] = CONTRACT_VERSION
    direction: Literal["in"] = "in"
    text: str


class Term(Strict):
    romanian: str
    english: str
    mismatch: bool = False
    note: str = ""


class TranslatedQuestion(Strict):
    """Translator to main agent: the question in English for the tools."""
    contract: Literal["contracts.v3"] = CONTRACT_VERSION
    language: Language
    english_question: str
    terms: list[Term] = Field(default_factory=list)
    clarifying_question: str | None = Field(None, description="In the user's language, only if the question is unclear")


class TranslationOut(Strict):
    """Main agent to translator, end of a turn: the English answer to put in the user's language."""
    contract: Literal["contracts.v3"] = CONTRACT_VERSION
    direction: Literal["out"] = "out"
    language: Language
    chunks: list[str] = Field(description="English answer chunks: answer, details, sources")
    keep_english: list[str] = Field(default_factory=list, description="Quotes and official terms to keep in English")


class TranslatedAnswer(Strict):
    """Translator to main agent: chunks in the user's language, quotes kept in English with a translation."""
    contract: Literal["contracts.v3"] = CONTRACT_VERSION
    language: Language
    chunks: list[str]


class Problem(Strict):
    code: ProblemCode
    severity: Literal["error", "warning"]
    message: str
    claim: str | None = None


class Verdict(Strict):
    contract: Literal["contracts.v3"] = CONTRACT_VERSION
    pass_: bool = Field(alias="pass")
    problems: list[Problem]
    checked: dict[str, int]

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


MODELS = {m.__name__: m for m in (Source, SpecialistTask, FindingClaim, Findings, AnswerClaim, Answer, Problem, Verdict,
                                  TranslationIn, Term, TranslatedQuestion, TranslationOut, TranslatedAnswer)}


def schema() -> dict[str, Any]:
    return {
        "$comment": "Generated from system/api/builders_api/contracts.py. Do not edit by hand.",
        "contract": CONTRACT_VERSION,
        "definitions": {name: m.model_json_schema(by_alias=True) for name, m in MODELS.items()},
    }


def render() -> str:
    return json.dumps(schema(), indent=2, sort_keys=True) + "\n"


if __name__ == "__main__":
    if "--write" in sys.argv:
        SCHEMA_FILE.write_text(render())
        print(f"wrote {SCHEMA_FILE}")
    else:
        print(render())
