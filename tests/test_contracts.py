"""Agent contracts: the schema file is current, plugin examples are valid, verify_answer output fits Verdict."""

import json
import re
from pathlib import Path

import pytest

from builders_api import contracts

ROOT = Path(__file__).resolve().parents[1]


def _json_blocks(path: Path) -> list[dict]:
    return [json.loads(b) for b in re.findall(r"```json\n(.*?)\n```", path.read_text(), flags=re.S)]


def test_schema_file_is_current():
    assert contracts.SCHEMA_FILE.read_text() == contracts.render(), \
        "Run: python -m builders_api.contracts --write (from system/api) and commit the schema file."


SPECIALISTS = sorted(p for p in (ROOT / "plugin" / "agents").glob("*.md") if p.stem != "translator")


@pytest.mark.parametrize("agent", SPECIALISTS, ids=lambda p: p.stem)
def test_agent_examples_are_valid_findings(agent):
    blocks = _json_blocks(agent)
    assert blocks, f"{agent.name} has no JSON example"
    for b in blocks:
        f = contracts.Findings.model_validate(b)
        assert f.kind == agent.stem.replace("inbox-clerk", "inbox") or f.kind in agent.read_text()


def test_translator_examples():
    question, answer = _json_blocks(ROOT / "plugin" / "agents" / "translator.md")
    q = contracts.TranslatedQuestion.model_validate(question)
    a = contracts.TranslatedAnswer.model_validate(answer)
    assert q.language == "ro" and q.terms and "£2,400" in a.chunks[0]


def test_workflow_examples():
    blocks = _json_blocks(ROOT / "plugin" / "skills" / "builders-workflow" / "SKILL.md")
    task, answer = blocks[0], blocks[1]
    contracts.SpecialistTask.model_validate(task)
    contracts.Answer.model_validate(answer)


def test_contract_rejects_unknown_fields_and_types():
    with pytest.raises(Exception):
        contracts.Findings.model_validate({"kind": "variations", "claims": [], "extra": 1})
    with pytest.raises(Exception):
        contracts.AnswerClaim.model_validate({"id": "c1", "source": {"type": "website", "id": "x"}})


def test_verify_output_fits_verdict(seeded):
    from builders_api.service import jobs, verify
    out = verify.verify_answer(jobs.firm_id("oakline"), "No asbestos here.", [])
    v = contracts.Verdict.model_validate(out)
    assert v.pass_ is False and {p.code for p in v.problems} >= {"BANNED_PHRASE"}
