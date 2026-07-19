# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed
- `install.sh` was committed without the executable bit, so a fresh `git clone` +
  `./install.sh` (exactly what the README instructs) failed with "Permission denied" on every
  new user's machine since the initial release. Fixed the bit in git.

### Added
- Hard storage limits: `~/.config/notistory/config.json` caps the log at `max_stored_mb`
  (default 25MB), self-trimming down to the newest `max_stored_entries` (default 20,000) whenever
  the cap is crossed. Individual summary/body fields are truncated at `max_field_length`
  (default 4000 chars) so one runaway notification can't bloat the log.
- `bin/notistory-diagnose.sh` — collects a local diagnostic report (versions, service/journal
  status, log size, config) for bug reports. Never includes notification content.
- GitHub issue templates (bug report, feature request) and this changelog, `CONTRIBUTING.md`,
  `SECURITY.md`.
- CI workflow: syntax-checks all Python files and lints shell scripts on every push/PR.

### Changed
- `notify-logger.py` now retries the D-Bus connection with exponential backoff (2s → 60s) and
  logs failures to stderr (visible via `journalctl --user -u notistory`) instead of relying
  solely on systemd's restart loop.
- `notistory.service` adds `StartLimitIntervalSec=300` / `StartLimitBurst=10` so an unrecoverable
  failure stops retrying instead of crash-looping forever.
- `install.sh` now checks for `python3-dbus`/`python3-gi` before installing and verifies the
  service actually started, instead of reporting success on a service that will never run.
- `bin/open-notistory.sh` now shows a desktop notification/dialog on failure instead of silently
  doing nothing when launched from the desktop icon.
- `app.js` wraps rendering in a try/catch and shows a friendly error screen (with a link to file
  an issue) instead of a blank page if `data.js` is malformed.

## [1.0.1] - 2026-07-19
### Fixed
- Live GitHub Pages demo now computes sample timestamps at page load instead of baking them in
  at build time, so it no longer drifts into showing "Earlier" / empty "Today" after a few days.

## [1.0.0] - 2026-07-17
### Added
- Initial public release as **Notistory**: D-Bus notification recorder (systemd --user service),
  append-only JSONL storage, static HTML/JS viewer with Today/Earlier tabs, per-app filtering,
  search, light/dark theme, and app-name normalization.
- MIT license, portfolio README, live GitHub Pages demo.
