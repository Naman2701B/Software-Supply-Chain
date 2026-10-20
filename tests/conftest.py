"""Shared fixtures.

The Rekor fixtures in tests/data were recorded from the public Rekor instance:
rekor_entry.json is the log entry for this repo's own signed artifact.md
(log index 3093171635), and consistency.json holds two real checkpoints of the
same tree plus the consistency proof between them. Tests replay these instead
of calling the network.
"""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any
from unittest import mock

import pytest

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent
DATA_DIR = TESTS_DIR / "data"


def load_json(name: str) -> Any:
    with open(DATA_DIR / name, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def rekor_response() -> dict[str, Any]:
    """Raw /log/entries response: {uuid: entry}."""
    data: dict[str, Any] = load_json("rekor_entry.json")
    return data


@pytest.fixture
def rekor_entry(rekor_response: dict[str, Any]) -> dict[str, Any]:
    entry: dict[str, Any] = next(iter(rekor_response.values()))
    return entry


@pytest.fixture
def consistency_data() -> dict[str, Any]:
    data: dict[str, Any] = load_json("consistency.json")
    return data


@pytest.fixture
def artifact_path() -> Path:
    return REPO_ROOT / "artifact.md"


@pytest.fixture
def make_response() -> Callable[[Any], mock.Mock]:
    """Build a stand-in for requests.Response returning the given JSON."""

    def _make(payload: Any) -> mock.Mock:
        response = mock.Mock()
        response.json.return_value = payload
        response.raise_for_status.return_value = None
        return response

    return _make
