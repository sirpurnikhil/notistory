# Contributing to Notistory

Notistory is intentionally small: no build step, no framework, no dependencies beyond
`python3-dbus` and `python3-gi`. Please keep contributions in that spirit.

## Reporting bugs

Run the diagnostic script first and attach its output to your issue — it contains no notification
content, only versions, service status, and log size/counts:

```bash
./bin/notistory-diagnose.sh
```

Then open a [bug report](https://github.com/sirpurnikhil/notistory/issues/new/choose).

## Submitting changes

1. Fork and branch off `main`.
2. Keep changes focused — this project favors small, readable diffs over abstractions.
3. Before opening a PR, sanity-check your changes locally:
   ```bash
   python3 -m py_compile src/*.py demo/*.py
   shellcheck install.sh bin/*.sh   # if you have shellcheck installed
   ./install.sh && ./bin/open-notistory.sh   # verify it still runs end-to-end
   ```
4. Update `CHANGELOG.md` under "Unreleased" with a one-line summary of your change.
5. Open a PR describing what changed and why.

## Code style

- Python: stdlib + `dbus-python`/`PyGObject` only, no new dependencies without discussion.
- JS: vanilla, no build tooling, no frameworks.
- Shell: `set -euo pipefail`, quote all variables, prefer explicit error messages over silent
  failure — this app runs unattended as a login service, so anything that can fail silently will
  eventually fail silently on someone's machine.
