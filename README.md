# Python Rekor Monitor

A command-line tool that verifies entries in [Sigstore's Rekor](https://docs.sigstore.dev/logging/overview/)
transparency log. It can:

- **Verify inclusion**: fetch a log entry by index, verify the artifact's signature
  against the signing certificate in the entry, and check the entry's Merkle
  inclusion proof.
- **Fetch the latest checkpoint**: print the log's current signed tree head.
- **Verify consistency**: confirm that an older checkpoint is consistent with the
  latest one, i.e. the log has only been appended to.

Built for NYU CS-GY 9223 Software Supply Chain Security.

## Installation

Requires Python 3.10+ and [Poetry](https://python-poetry.org/).

```bash
git clone https://github.com/Naman2701B/Software-Supply-Chain.git
cd Software-Supply-Chain
poetry install
```

## Usage

```bash
# Verify that a log entry is in Rekor and that its signature matches an artifact
poetry run python main.py --inclusion <logIndex> --artifact artifact.md

# Print the latest checkpoint (add -d to also save it to checkpoint.json)
poetry run python main.py -c

# Verify an older checkpoint is consistent with the latest one
poetry run python main.py --consistency --tree-id <treeID> --tree-size <treeSize> --root-hash <rootHash>
```

Add `-d` / `--debug` to any command for verbose output.

### Signing an artifact

`artifact.md` is created with `scripts/create_artifact.py` and signed with
[cosign](https://docs.sigstore.dev/cosign/system_config/installation/), which
uploads the signature to Rekor:

```bash
python scripts/create_artifact.py <netid>
cosign sign-blob artifact.md --bundle artifact.bundle
```

`artifact.md` must stay byte-for-byte identical after signing, including its line
ending; `.gitattributes` stops git from converting it.

## Development

Install the dev tools with `poetry install` (they are in the `dev` dependency group),
then:

| Task | Command |
|------|---------|
| Format | `poetry run ruff format .` |
| Lint | `poetry run ruff check .` |
| Type check | `poetry run mypy main.py merkle_proof.py util.py` |
| Security scan (SAST) | `poetry run bandit -r .` |
| Tests + coverage | `poetry run pytest` |

Tests run offline against Rekor responses recorded in `tests/data/`, and the run
fails if coverage drops below 75%.

### Pre-commit secret scanning

Commits are scanned for secrets with [TruffleHog](https://github.com/trufflesecurity/trufflehog)
through [pre-commit](https://pre-commit.com/). Install both on your machine, then
enable the hook once per clone:

```bash
pre-commit install
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the contribution workflow and
[SECURITY.md](SECURITY.md) for reporting vulnerabilities.

## Project layout

```
main.py                     CLI: inclusion, checkpoint and consistency commands
merkle_proof.py             RFC 6962 Merkle inclusion and consistency proofs
util.py                     Certificate and signature helpers
scripts/create_artifact.py  Creates artifact.md
tests/                      pytest suite and recorded Rekor fixtures
```

## License

[MIT](LICENSE)
