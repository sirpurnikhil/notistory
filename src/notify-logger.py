#!/usr/bin/env python3
"""Records every desktop notification (org.freedesktop.Notifications.Notify) to JSONL."""
import json, os, time
from datetime import datetime
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

DATA_DIR = os.path.expanduser("~/.local/share/notistory")
LOG_PATH = os.path.join(DATA_DIR, "notifications.jsonl")
os.makedirs(DATA_DIR, exist_ok=True)


def _s(v):
    try:
        return str(v)
    except Exception:
        return ""


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
            "summary": summary,
            "body": body,
            "urgency": urgency,
        }
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        # A logging daemon must never crash on a single bad message.
        pass


def main():
    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus(private=True)
    dbus_daemon = bus.get_object("org.freedesktop.DBus", "/org/freedesktop/DBus")
    monitoring = dbus.Interface(dbus_daemon, "org.freedesktop.DBus.Monitoring")
    rules = ["interface='org.freedesktop.Notifications',member='Notify'"]
    monitoring.BecomeMonitor(rules, dbus.UInt32(0))
    bus.add_message_filter(handle_message)
    GLib.MainLoop().run()


if __name__ == "__main__":
    main()
