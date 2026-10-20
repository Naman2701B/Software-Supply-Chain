import base64
import hashlib
from typing import Any

import pytest

from merkle_proof import (
    DefaultHasher,
    RootMismatchError,
    compute_leaf_hash,
    root_from_inclusion_proof,
    verify_consistency,
    verify_inclusion,
)


def test_hash_leaf_uses_rfc6962_leaf_prefix() -> None:
    assert DefaultHasher.hash_leaf(b"abc") == hashlib.sha256(b"\x00abc").digest()


def test_hash_children_uses_rfc6962_node_prefix() -> None:
    left, right = b"L" * 32, b"R" * 32
    expected = hashlib.sha256(b"\x01" + left + right).digest()
    assert DefaultHasher.hash_children(left, right) == expected


def test_compute_leaf_hash_matches_hasher(rekor_entry: dict[str, Any]) -> None:
    body = rekor_entry["body"]
    expected = DefaultHasher.hash_leaf(base64.b64decode(body)).hex()
    assert compute_leaf_hash(body) == expected


def test_verify_inclusion_accepts_real_proof(rekor_entry: dict[str, Any]) -> None:
    proof = rekor_entry["verification"]["inclusionProof"]
    verify_inclusion(
        DefaultHasher,
        proof["logIndex"],
        proof["treeSize"],
        compute_leaf_hash(rekor_entry["body"]),
        proof["hashes"],
        proof["rootHash"],
    )


def test_verify_inclusion_rejects_tampered_root(rekor_entry: dict[str, Any]) -> None:
    proof = rekor_entry["verification"]["inclusionProof"]
    with pytest.raises(RootMismatchError) as excinfo:
        verify_inclusion(
            DefaultHasher,
            proof["logIndex"],
            proof["treeSize"],
            compute_leaf_hash(rekor_entry["body"]),
            proof["hashes"],
            "00" * 32,
        )
    assert "00" * 32 in str(excinfo.value)


def test_root_from_inclusion_proof_rejects_index_beyond_size() -> None:
    with pytest.raises(ValueError, match="index is beyond size"):
        root_from_inclusion_proof(DefaultHasher, 5, 5, b"\x00" * 32, [])


def test_verify_consistency_accepts_real_proof(
    consistency_data: dict[str, Any],
) -> None:
    prev, latest = consistency_data["previous"], consistency_data["latest"]
    verify_consistency(
        DefaultHasher,
        prev["treeSize"],
        latest["treeSize"],
        consistency_data["proof"]["hashes"],
        prev["rootHash"],
        latest["rootHash"],
    )


def test_verify_consistency_rejects_wrong_old_root(
    consistency_data: dict[str, Any],
) -> None:
    prev, latest = consistency_data["previous"], consistency_data["latest"]
    with pytest.raises(RootMismatchError):
        verify_consistency(
            DefaultHasher,
            prev["treeSize"],
            latest["treeSize"],
            consistency_data["proof"]["hashes"],
            "11" * 32,
            latest["rootHash"],
        )


def test_verify_consistency_rejects_shrinking_tree() -> None:
    with pytest.raises(ValueError, match="size2"):
        verify_consistency(DefaultHasher, 10, 5, ["aa"], "00" * 32, "00" * 32)


def test_verify_consistency_same_size_requires_equal_roots() -> None:
    verify_consistency(DefaultHasher, 7, 7, [], "ab" * 32, "ab" * 32)
    with pytest.raises(RootMismatchError):
        verify_consistency(DefaultHasher, 7, 7, [], "ab" * 32, "cd" * 32)
