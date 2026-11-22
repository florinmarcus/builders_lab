"""Crop check: packets, saved verdicts keyed by the crop's hash, and the status of current crops."""
import json

from PIL import Image

from system.rag import cropcheck


def test_overlay_draws_red_box_and_keeps_page():
    page = Image.new("RGB", (300, 400), "white")
    out = cropcheck.overlay(page, {"x0": 10, "top": 20, "x1": 100, "bottom": 120}, 2.0)
    assert out.size == page.size
    assert out.getpixel((20, 100)) == (230, 0, 0)  # left edge of the box at x0*scale
    assert out.getpixel((100, 100)) == (255, 255, 255)  # inside stays as it was
    assert page.getpixel((20, 100)) == (255, 255, 255)  # the page itself is not drawn on


def test_save_and_status(tmp_path, monkeypatch):
    corpus = tmp_path / "corpus"
    monkeypatch.setattr(cropcheck, "CORPUS_DIR", corpus)
    monkeypatch.setattr(cropcheck, "ROOT", tmp_path)
    src = "demo"
    figdir = corpus / "parsed" / src / "v1" / "figures"
    figdir.mkdir(parents=True)
    paths = []
    for i, colour in enumerate(["red", "blue"]):
        p = figdir / f"figure-{i + 1}.png"
        Image.new("RGB", (20, 20), colour).save(p)
        paths.append(p.relative_to(tmp_path).as_posix())
    tree = {"version_id": "v1", "sections": [
        {"id": f"figure-{i + 1}", "type": "figure", "title": f"Fig {i + 1}", "image_path": p,
         "area": {"page": 3, "top": 0, "bottom": 10, "x0": 0, "x1": 10}} for i, p in enumerate(paths)]}
    (corpus / "parsed" / src / "v1.json").write_text(json.dumps(tree))
    import system.rag.checks as checks
    monkeypatch.setattr(checks, "CORPUS_DIR", corpus)

    keys = [cropcheck._sha(tmp_path / p)[:16] for p in paths]
    out = corpus / "parsed" / src / "cropcheck"
    out.mkdir(parents=True)
    for k, f in zip(keys, ["figure-1", "figure-2"]):
        (out / f"001-crop-{k}.json").write_text(json.dumps(
            {"key": k, "version_id": "v1", "target": f"{f}: x", "page": 3}))
    answers = tmp_path / "a.jsonl"
    answers.write_text("\n".join([
        json.dumps({"key": keys[0], "kind": "crop", "verdict": "ok", "problem": "", "caption_inside": "false"}),
        json.dumps({"key": keys[1], "kind": "crop", "verdict": "cut", "problem": "top missing"}),
        json.dumps({"key": "nope", "kind": "crop", "verdict": "ok"})]))
    assert cropcheck.save(src, answers, "test", today="2026-11-22") == 1  # one unknown key refused
    saved = json.loads((corpus / "cropchecks" / f"{src}.json").read_text())["verdicts"]
    assert saved[keys[0]]["caption_inside"] is False and saved[keys[1]]["verdict"] == "cut"

    st = cropcheck.status(src)
    assert st["crops"] == 2 and st["ok"] == 1 and len(st["bad"]) == 1 and not st["unjudged"]

    assert cropcheck.accept(src, "figure-2", "notes kept as a paragraph", "test") == 0
    st = cropcheck.status(src)
    assert st["ok"] == 2 and not st["bad"]
    Image.new("RGB", (20, 20), "green").save(tmp_path / paths[1])  # the parser cut a new crop: judged afresh
    st = cropcheck.status(src)
    assert st["ok"] == 1 and not st["bad"] and len(st["unjudged"]) == 1  # a changed crop is judged again
