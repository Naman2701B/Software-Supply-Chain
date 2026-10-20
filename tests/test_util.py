import base64
import json
from pathlib import Path
from typing import Any

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from util import extract_public_key, verify_artifact_signature


def signature_and_cert(entry: dict[str, Any]) -> tuple[bytes, bytes]:
    body = json.loads(base64.b64decode(entry["body"]))
    signature = base64.b64decode(body["spec"]["signature"]["content"])
    certificate = base64.b64decode(body["spec"]["signature"]["publicKey"]["content"])
    return signature, certificate


def test_extract_public_key_returns_pem(rekor_entry: dict[str, Any]) -> None:
    _, certificate = signature_and_cert(rekor_entry)
    pem = extract_public_key(certificate)
    assert pem.startswith(b"-----BEGIN PUBLIC KEY-----")


def test_valid_signature_prints_nothing(
    rekor_entry: dict[str, Any],
    artifact_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    signature, certificate = signature_and_cert(rekor_entry)
    verify_artifact_signature(
        signature, extract_public_key(certificate), str(artifact_path)
    )
    assert capsys.readouterr().out == ""


def test_tampered_artifact_is_reported_invalid(
    rekor_entry: dict[str, Any],
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    tampered = tmp_path / "artifact.md"
    tampered.write_bytes(b"someoneelse1\n")
    signature, certificate = signature_and_cert(rekor_entry)
    verify_artifact_signature(signature, extract_public_key(certificate), str(tampered))
    assert "Signature is invalid" in capsys.readouterr().out


def test_non_ecdsa_key_is_rejected(
    artifact_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ed_key = ed25519.Ed25519PrivateKey.generate().public_key()
    pem = ed_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    verify_artifact_signature(b"sig", pem, str(artifact_path))
    assert "not ECDSA" in capsys.readouterr().out
