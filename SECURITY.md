# Security Policy

Notistory is a local-only application: it has no network calls, no server, no accounts, and no
telemetry. Its entire attack surface is the local D-Bus session, a flat file on disk
(`~/.local/share/notistory/notifications.jsonl`), and a static HTML page opened via `file://`.

## Reporting a vulnerability

If you find a security issue (e.g. a way for a malicious local app to corrupt the log, escape the
HTML sandbox in the viewer, or escalate privileges through the installer/service files), please
open a [GitHub issue](https://github.com/sirpurnikhil/notistory/issues/new/choose) or, if it's
sensitive, use GitHub's private [Security Advisory](https://github.com/sirpurnikhil/notistory/security/advisories/new)
form instead of a public issue.

Please include:
- A description of the issue and its impact
- Steps to reproduce
- Your distro/desktop environment

## Data handling

- Notification content (title/body) can contain sensitive information (2FA codes, personal
  messages). It is stored **only** in plain text on your own machine and is never transmitted
  anywhere by this application.
- The diagnostic tool (`bin/notistory-diagnose.sh`) deliberately excludes notification content —
  it collects only versions, service/journal status, and log size/entry counts.
