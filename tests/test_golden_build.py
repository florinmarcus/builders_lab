"""Golden set build (evals/golden/build.py): copy filter, stable holdout, unknown ids fail."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals" / "golden"))
import build as B  # noqa: E402


def test_shared_run_finds_the_longest_common_word_run():
    assert B.shared_run("Do I need a licence to remove asbestos insulating board?",
                        "Work with asbestos insulating board is licensable") == ["asbestos", "insulating", "board"]
    assert B.shared_run("FD30 doors", "fd30 doors") == ["fd30", "doors"]
    assert B.words("Table 7.6.3 and 20%") == ["table", "7.6.3", "and", "20%"]


def test_holdout_is_stable_and_about_a_fifth():
    ids = [f"q-{i:04d}" for i in range(2000)]
    share = sum(B.is_holdout(i) for i in ids) / len(ids)
    assert 0.15 < share < 0.25
    assert [B.is_holdout(i) for i in ids[:50]] == [B.is_holdout(i) for i in ids[:50]]


def test_build_drops_copies_and_fails_on_unknown_ids(tmp_path, monkeypatch):
    g = tmp_path / "golden"
    (g / "business").mkdir(parents=True)
    (g / "labelled").mkdir()
    qs = [{"id": "a-001", "kind": "answerable", "question": "Can my lads drill an Artex ceiling?"},
          {"id": "a-002", "kind": "answerable", "question": "the employer must ensure that any person who"},
          {"id": "a-003", "kind": "out_of_scope", "question": "What does a survey cost?"}]
    (g / "business" / "asbestos.jsonl").write_text("".join(json.dumps(q) + "\n" for q in qs))
    labs = [{"id": "a-001", "expected_sections": ["car2012:regulation-7"]},
            {"id": "a-002", "expected_sections": ["car2012:regulation-10"]}]
    (g / "labelled" / "asbestos.jsonl").write_text("".join(json.dumps(l) + "\n" for l in labs))
    monkeypatch.setattr(B, "GOLDEN", g)
    index = {"car2012:regulation-7": {"text": "Plan of work for asbestos work.", "heading_path": ["CAR", "Reg 7"]},
             "car2012:regulation-10": {"text": "Every employer must ensure that any person who is employed", "heading_path": []}}
    r = B.build(index)
    assert r["problems"] == []
    assert [q["id"] for q in r["kept"]] == ["a-001", "a-003"]
    assert r["dropped"][0]["id"] == "a-002" and r["dropped"][0]["shared_run"] >= 5
    labs.append({"id": "a-003", "expected_sections": ["car2012:regulation-99"]})
    (g / "labelled" / "asbestos.jsonl").write_text("".join(json.dumps(l) + "\n" for l in labs))
    assert any("unknown section car2012:regulation-99" in p for p in B.build(index)["problems"])


def test_pool_judge_yes_becomes_also_acceptable_on_dev_only(tmp_path, monkeypatch):
    g = tmp_path / "golden"
    for d in ("business", "labelled", "pooled"):
        (g / d).mkdir(parents=True)
    ids = [f"a-{i:03d}" for i in range(40)]
    dev = next(i for i in ids if not B.is_holdout(i))
    hold = next(i for i in ids if B.is_holdout(i))
    (g / "business" / "a.jsonl").write_text("".join(json.dumps({"id": i, "kind": "answerable", "question": "Q?"}) + "\n" for i in (dev, hold)))
    (g / "labelled" / "a.jsonl").write_text("".join(json.dumps({"id": i, "expected_sections": ["s:1"]}) + "\n" for i in (dev, hold)))
    (g / "pooled" / "judgments.jsonl").write_text("".join(json.dumps({"id": i, "section": "s:2", "verdict": "yes"}) + "\n" for i in (dev, hold))
                                                  + json.dumps({"id": dev, "section": "s:3", "verdict": "no"}) + "\n")
    monkeypatch.setattr(B, "GOLDEN", g)
    r = B.build({"s:1": {"text": "x"}, "s:2": {"text": "y"}, "s:3": {"text": "z"}})
    got = {q["id"]: q["also_acceptable"] for q in r["kept"]}
    assert got[dev] == ["s:2"] and got[hold] == []
