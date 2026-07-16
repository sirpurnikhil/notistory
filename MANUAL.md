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
- Background service: `notistory.service` (user service).

## Common fixes
| Symptom | Fix |
|---|---|
| Nothing being recorded | `systemctl --user status notistory.service` — if not running: `systemctl --user restart notistory.service` |
| Icon does nothing | Run `bin/open-notistory.sh` in a terminal to see the error |
| Page empty but data exists | Re-run `python3 src/generate-data.py` |
| An app shows an ugly name | Edit `~/.config/notistory/app-names.json` (see README → Configuration) |
| Want to wipe history | Stop the service, empty/trim the `.jsonl` file, start the service |

## Uninstall
```bash
./install.sh --uninstall
```
Removes the service and launchers. Your recorded history is kept.

## Notes
- Only notifications fired **while the service is running** are captured (nothing retroactive).
- The recorder is a passive D-Bus monitor: negligible CPU, no network, all data stays local.
