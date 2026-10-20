import runpy
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "create_artifact.py"


def test_writes_netid_to_artifact(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["create_artifact.py", "nb4180"])
    runpy.run_path(str(SCRIPT), run_name="__main__")

    assert (tmp_path / "artifact.md").read_text() == "nb4180\n"


def test_requires_exactly_one_argument(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["create_artifact.py"])
    with pytest.raises(SystemExit, match="Usage"):
        runpy.run_path(str(SCRIPT), run_name="__main__")
