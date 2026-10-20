import json
from collections.abc import Callable
from pathlib import Path
from typing import Any
from unittest import mock

import pytest

import main
from merkle_proof import compute_leaf_hash


def test_get_log_entry_returns_entry(
    monkeypatch: pytest.MonkeyPatch,
    rekor_response: dict[str, Any],
    rekor_entry: dict[str, Any],
    make_response: Callable[[Any], mock.Mock],
) -> None:
    get = mock.Mock(return_value=make_response(rekor_response))
    monkeypatch.setattr("main.requests.get", get)

    assert main.get_log_entry(3093171635) == rekor_entry
    assert get.call_args.kwargs["params"] == {"logIndex": 3093171635}


def test_get_log_entry_rejects_negative_index() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        main.get_log_entry(-1)


def test_get_verification_proof_fields(
    monkeypatch: pytest.MonkeyPatch,
    rekor_response: dict[str, Any],
    rekor_entry: dict[str, Any],
    make_response: Callable[[Any], mock.Mock],
) -> None:
    monkeypatch.setattr(
        "main.requests.get", mock.Mock(return_value=make_response(rekor_response))
    )
    proof = main.get_verification_proof(3093171635, debug=True)

    inclusion_proof = rekor_entry["verification"]["inclusionProof"]
    assert proof["index"] == inclusion_proof["logIndex"]
    assert proof["tree_size"] == inclusion_proof["treeSize"]
    assert proof["root_hash"] == inclusion_proof["rootHash"]
    assert proof["leaf_hash"] == compute_leaf_hash(rekor_entry["body"])


def test_inclusion_verifies_signed_artifact(
    monkeypatch: pytest.MonkeyPatch,
    rekor_response: dict[str, Any],
    artifact_path: Path,
    make_response: Callable[[Any], mock.Mock],
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        "main.requests.get", mock.Mock(return_value=make_response(rekor_response))
    )
    main.inclusion(3093171635, str(artifact_path))

    out = capsys.readouterr().out
    assert "Signature is invalid" not in out
    assert "Offline root hash calculation for inclusion verified." in out


def test_inclusion_rejects_missing_artifact(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="not a valid file"):
        main.inclusion(1, str(tmp_path / "missing.md"))


def test_checkpoint_debug_saves_checkpoint_json(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    consistency_data: dict[str, Any],
    make_response: Callable[[Any], mock.Mock],
) -> None:
    latest = consistency_data["latest"]
    monkeypatch.setattr(
        "main.requests.get", mock.Mock(return_value=make_response(latest))
    )
    monkeypatch.chdir(tmp_path)

    assert main.get_latest_checkpoint(debug=True) == latest
    saved = json.loads((tmp_path / "checkpoint.json").read_text(encoding="utf-8"))
    assert saved == latest


def test_consistency_verifies_recorded_checkpoints(
    monkeypatch: pytest.MonkeyPatch,
    consistency_data: dict[str, Any],
    make_response: Callable[[Any], mock.Mock],
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_get(url: str, **kwargs: Any) -> mock.Mock:
        if url.endswith("/log/proof"):
            return make_response(consistency_data["proof"])
        return make_response(consistency_data["latest"])

    monkeypatch.setattr("main.requests.get", fake_get)
    main.consistency(dict(consistency_data["previous"]))

    assert "Consistency verification successful." in capsys.readouterr().out


def test_consistency_rejects_empty_checkpoint() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        main.consistency({})


def test_main_checkpoint_flag_prints_json(
    monkeypatch: pytest.MonkeyPatch,
    consistency_data: dict[str, Any],
    make_response: Callable[[Any], mock.Mock],
    capsys: pytest.CaptureFixture[str],
) -> None:
    latest = consistency_data["latest"]
    monkeypatch.setattr(
        "main.requests.get", mock.Mock(return_value=make_response(latest))
    )
    monkeypatch.setattr("sys.argv", ["main.py", "-c"])
    main.main()

    assert json.loads(capsys.readouterr().out) == latest


def test_main_consistency_requires_tree_id(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.argv", ["main.py", "--consistency"])
    main.main()

    assert "please specify tree id" in capsys.readouterr().out
