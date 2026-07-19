#!/usr/bin/env python3
"""Records every desktop notification (org.freedesktop.Notifications.Notify) to JSONL."""
import json, os, sys, time
from collections import deque
from datetime import datetime
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

DATA_DIR = os.path.expanduser("~/.local/share/notistory")
LOG_PATH = os.path.join(DATA_DIR, "notifications.jsonl")
os.makedirs(DATA_DIR, exist_ok=True)

CONFIG_DIR = os.path.expanduser("~/.config/notistory")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

# Hard limits so the log can never grow unbounded and slow the app down.
DEFAULT_CONFIG = {
    "_comment": "Notistory limits. Edit and restart the recorder (systemctl --user restart "
                "notistory) to apply. max_stored_mb triggers a trim down to max_stored_entries "
                "newest notifications; max_field_length truncates any single summary/body.",
    "max_stored_entries": 20000,
    "max_stored_mb": 25,
    "max_field_length": 4000,
    "max_displayed_entries": 8000,
}


def load_config():
    """Return the merged config. Seeds an editable JSON file on first run."""
    cfg = dict(DEFAULT_CONFIG)
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        if not os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            user = json.load(f)
        for k, v in user.items():
            if k in ("max_stored_entries", "max_stored_mb", "max_field_length") and isinstance(v, (int, float)) and v > 0:
                cfg[k] = v
    except Exception:
        pass  # fall back to defaults on any config error
    return cfg


CONFIG = load_config()
MAX_STORED_ENTRIES = int(CONFIG["max_stored_entries"])
MAX_STORED_BYTES = int(CONFIG["max_stored_mb"] * 1024 * 1024)
MAX_FIELD_LENGTH = int(CONFIG["max_field_length"])


def _s(v):
    try:
        return str(v)
    except Exception:
        return ""


def _truncate(text):
    if len(text) > MAX_FIELD_LENGTH:
        return text[:MAX_FIELD_LENGTH] + "…[truncated]"
    return text


def _trim_log_if_needed():
    """Keep the log from growing unbounded: past MAX_STORED_BYTES, keep only the newest
    MAX_STORED_ENTRIES lines. Runs a full read+rewrite only when the threshold is crossed,
    not on every write, so normal appends stay O(1)."""
    try:
        if os.path.getsize(LOG_PATH) <= MAX_STORED_BYTES:
            return
        kept = deque(maxlen=MAX_STORED_ENTRIES)
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    kept.append(line)
        tmp_path = LOG_PATH + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.writelines(kept)
        os.replace(tmp_path, LOG_PATH)
        print(f"notistory: trimmed log to newest {len(kept)} entries "
              f"(exceeded {CONFIG['max_stored_mb']}MB)", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"notistory: log trim failed: {e}", file=sys.stderr, flush=True)


def handle_message(_bus, message):
    try:
        if message.get_member() != "Notify":
            return
        if message.get_interface() != "org.freedesktop.Notifications":
            return
        args = list(message.get_args_list())
        # Notify(app_name, replaces_id, app_icon, summary, body, actions, hints, expire_timeout)
        app_name = _s(args[0]) if len(args) > 0 else ""
        app_icon = _s(args[2]) if len(args) > 2 else ""
        summary  = _s(args[3]) if len(args) > 3 else ""
        body     = _s(args[4]) if len(args) > 4 else ""
        hints    = args[6] if len(args) > 6 else {}

        urgency = 1
        desktop_entry = ""
        try:
            if "urgency" in hints:
                urgency = int(hints["urgency"])
        except Exception:
            pass
        try:
            if "desktop-entry" in hints:
                desktop_entry = _s(hints["desktop-entry"])
        except Exception:
            pass

        if not summary and not body:
            return

        rec = {
            "ts": time.time(),
            "iso": datetime.now().astimezone().isoformat(),
            "app": app_name or "Unknown",
            "app_icon": app_icon,
            "desktop_entry": desktop_entry,
            "summary": _truncate(summary),
            "body": _truncate(body),
            "urgency": urgency,
        }
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        _trim_log_if_needed()
    except Exception as e:
        # A logging daemon must never crash on a single bad message, but the failure
        # should still be visible in the journal instead of vanishing silently.
        print(f"notistory: failed to record a notification: {e}", file=sys.stderr, flush=True)


def main():
    DBusGMainLoop(set_as_default=True)
    backoff = 2
    while True:
        try:
            bus = dbus.SessionBus(private=True)
            dbus_daemon = bus.get_object("org.freedesktop.DBus", "/org/freedesktop/DBus")
            monitoring = dbus.Interface(dbus_daemon, "org.freedesktop.DBus.Monitoring")
            rules = ["interface='org.freedesktop.Notifications',member='Notify'"]
            monitoring.BecomeMonitor(rules, dbus.UInt32(0))
            bus.add_message_filter(handle_message)
            print("notistory: connected to session bus, monitoring notifications",
                  file=sys.stderr, flush=True)
            backoff = 2  # reset once we've connected successfully
            GLib.MainLoop().run()
            return  # MainLoop only returns via an explicit quit(); treat as a clean exit
        except Exception as e:
            print(f"notistory: D-Bus connection failed ({e}); retrying in {backoff}s",
                  file=sys.stderr, flush=True)
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)


if __name__ == "__main__":
    main()
