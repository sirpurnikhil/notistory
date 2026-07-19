# Manual — Notistory

A plain-language guide to running and maintaining Notistory. Assumes no prior context.

## What it is
Notistory records every desktop notification and lets you browse the full history in your browser —
newest first, split into **Today** / **Earlier**, filterable per app.

## One-time setup
From the cloned repository:
```bash
./install.sh
```
This enables the background recorder (a `systemd --user` service) and adds a **Notistory** icon to
your Desktop and app menu.

## Daily use
- Open **Notistory** from the Desktop or app menu (or run `bin/open-notistory.sh`).
- It opens a web page with your history, latest at the top.
- Left sidebar = filter by app · search box = filter by text · tabs = Today vs Earlier.
- The page is a **snapshot** taken when you open it. To see newer notifications, close it and open
  it again.

## Where things live
- Recorded data: `~/.local/share/notistory/notifications.jsonl` (one JSON line per notification).
- App-name overrides: `~/.config/notistory/app-names.json`.
- Limits/config: `~/.config/notistory/config.json`.
- Background service: `notistory.service` (user service).

## Storage limits (automatic)
The log can't grow unbounded — `~/.config/notistory/config.json` (seeded on first run) controls:

| Key | Default | Effect |
|---|---|---|
| `max_stored_mb` | 25 | Once the log file exceeds this size, it's trimmed automatically |
| `max_stored_entries` | 20000 | How many newest notifications survive a trim |
| `max_field_length` | 4000 | Longer summary/body text is truncated per-notification |
| `max_displayed_entries` | 8000 | How many of the stored notifications the viewer renders |

Edit the file, then `systemctl --user restart notistory.service` to apply.

## Common fixes
| Symptom | Fix |
|---|---|
| Nothing being recorded | `systemctl --user status notistory.service` — if not running: `systemctl --user restart notistory.service` |
| Icon does nothing | Run `bin/open-notistory.sh` in a terminal to see the error (it also now shows a desktop notification on failure) |
| Page empty but data exists | Re-run `python3 src/generate-data.py` |
| An app shows an ugly name | Edit `~/.config/notistory/app-names.json` (see README → Configuration) |
| Want to wipe history | Stop the service, empty/trim the `.jsonl` file, start the service |
| Anything else / filing a bug | Run `bin/notistory-diagnose.sh` — it writes a local report (no notification content) and opens the GitHub issue form |

## Uninstall
```bash
./install.sh --uninstall
```
Removes the service and launchers. Your recorded history is kept.

## Notes
- Only notifications fired **while the service is running** are captured (nothing retroactive).
- The recorder is a passive D-Bus monitor: negligible CPU, no network, all data stays local.
- If the recorder can't connect to D-Bus (e.g. right at login) it retries with backoff on its own;
  if it can't start at all after repeated attempts, systemd stops retrying rather than looping
  forever — check `journalctl --user -u notistory` or run `bin/notistory-diagnose.sh`.
