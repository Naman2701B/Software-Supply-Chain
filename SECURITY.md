# Security Policy

## Supported versions

Only the latest release and the `main` branch receive security fixes.

| Version | Supported |
|---------|-----------|
| `main` / latest release | Yes |
| Older releases | No |

## Reporting a vulnerability

**Please do not open a public issue for security problems.**

Report vulnerabilities privately through GitHub's private vulnerability reporting:
go to the repository's **Security** tab and click **Report a vulnerability**.

Please include:

- A description of the issue and its impact
- Steps to reproduce, or a proof of concept
- The affected version or commit

## What to expect

- **Acknowledgement** within 3 business days.
- **Assessment**: we confirm the issue and decide on a fix within 7 days.
- **Fix and release**: fixes are developed in a private security advisory, released
  as a new version, and the advisory is published once the fix is available.
  Reporters are credited unless they ask not to be.

## Handling security updates

- Dependencies are pinned in `poetry.lock`; security updates are applied with
  `poetry update <package>` and released promptly.
- Every commit is scanned for leaked secrets by a TruffleHog pre-commit hook.
- Code is scanned with Bandit (SAST) before release.
