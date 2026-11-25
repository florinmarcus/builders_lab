"""The outside-citation rules of the library-map experiment (M1)."""
import importlib.util
import pathlib

spec = importlib.util.spec_from_file_location(
    "library_map_build", pathlib.Path(__file__).resolve().parents[1] / "evals/experiments/library-map/build.py")
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)


def test_binding_mention_and_list():
    assert B.refs_in("these systems should comply with BS 5839-1.") == [("standard", "BS 5839", "binding")]
    assert B.refs_in("See BS EN 1634-1 for more information.")[0][2] == "mention"
    assert B.refs_in("BS 476-22 Methods for determination of the fire resistance of elements [1987]")[0][2] == "list"
    assert B.refs_in("BS 5839-1", ["ADB", "Appendix F: Standards referred to"])[0][2] == "list"


def test_names_are_normalised():
    assert [r[1] for r in B.refs_in("tested to BSEN13501-1 and to HSG 248")] == ["BS EN 13501", "HSG248"]
    assert B.refs_in("installed in accordance with the manufacturer’s instructions")[0][1] == "manufacturer's instructions"
