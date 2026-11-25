"""The decomposer's library list is built from corpus/sources.yaml (S146): every held topic tag has plain words,
every not-held source has a group, and the rendered draft matches its template."""
import importlib.util
import pathlib

HERE = pathlib.Path(__file__).resolve().parents[1] / "evals/experiments/decomposer"
spec = importlib.util.spec_from_file_location("decomposer_library", HERE / "library.py")
library = importlib.util.module_from_spec(spec)
spec.loader.exec_module(library)


def test_block_builds_and_names_planning_as_held():
    b = library.block()
    held, missing = b.split("It does not hold:")
    assert "permitted development" in held
    assert "British Standards" in missing and "planning permission rules" not in b


def test_rendered_draft_is_current():
    tmpl = (HERE / "prompt-d3.tmpl.md").read_text()
    assert (HERE / "prompt-d3.md").read_text() == tmpl.replace("{LIBRARY}", library.block())
