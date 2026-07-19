#!/usr/bin/env python3
"""Reads notifications.jsonl and writes src/data.js for the static UI."""
import json, os, glob

DATA_DIR = os.path.expanduser("~/.local/share/notistory")
LOG_PATH = os.path.join(DATA_DIR, "notifications.jsonl")
OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.js")

CONFIG_DIR = os.path.expanduser("~/.config/notistory")
NAME_MAP_PATH = os.path.join(CONFIG_DIR, "app-names.json")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
DEFAULT_MAX_DISPLAYED = 8000


def load_display_limit():
    """Read max_displayed_entries from the shared config.json (written by notify-logger.py).
    Falls back to the default if the config is missing/invalid — never fails the run."""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        val = cfg.get("max_displayed_entries", DEFAULT_MAX_DISPLAYED)
        if isinstance(val, (int, float)) and val > 0:
            return int(val)
    except Exception:
        pass
    return DEFAULT_MAX_DISPLAYED


MAX_ROWS = load_display_limit()  # cap the newest N notifications rendered

# App names that carry no useful identity — prefer the desktop-entry hint instead.
GENERIC_APPS = {"", "notify-send", "notify_send", "notify", "unknown",
                "gio", "kdialog", "zenity", "dunstify", "python", "python3", "bash", "sh"}

# Seed mappings (raw app name / desktop-entry, lowercased) -> friendly display name.
# The user's ~/.config/notification-history/app-names.json overlays and overrides these.
DEFAULT_NAME_MAP = {
    "google-chrome": "Google Chrome",
    "google-chrome-stable": "Google Chrome",
    "chrome": "Google Chrome",
    "chromium": "Chromium",
    "firefox": "Firefox",
    "org.mozilla.firefox": "Firefox",
    "code": "VS Code",
    "code - insiders": "VS Code Insiders",
    "code-insiders": "VS Code Insiders",
    "spotify": "Spotify",
    "discord": "Discord",
    "slack": "Slack",
    "thunderbird": "Thunderbird",
    "telegram-desktop": "Telegram",
    "org.telegram.desktop": "Telegram",
    "org.kde.dolphin": "Dolphin",
    "konsole": "Konsole",
    "org.kde.konsole": "Konsole",
    "notify-send": "notify-send",   # kept as-is: generic CLI used by many scripts
}

_icon_cache = {}
_HICOLOR_SIZES = ("48x48", "64x64", "32x32", "128x128", "256x256", "scalable")


def load_name_map():
    """Return the merged name map. Seeds an editable JSON file on first run."""
    merged = dict(DEFAULT_NAME_MAP)
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        if not os.path.exists(NAME_MAP_PATH):
            seed = {"_comment": "Map a raw app name or desktop-entry (any case) to the display "
                                "name you want. Edit freely; re-open the app to apply.",
                    **DEFAULT_NAME_MAP}
            with open(NAME_MAP_PATH, "w", encoding="utf-8") as f:
                json.dump(seed, f, indent=2, ensure_ascii=False)
        with open(NAME_MAP_PATH, "r", encoding="utf-8") as f:
            user = json.load(f)
        for k, v in user.items():
            if k.startswith("_") or not isinstance(v, str):
                continue
            merged[k.strip().lower()] = v
    except Exception:
        pass  # fall back to defaults on any config error
    return merged


# Trailing reverse-DNS segments that don't identify the app (com.spotify.Client -> Spotify).
_RDNS_STOP = {"client", "desktop", "app", "gui", "bin", "application", "core", "electron"}


def prettify(name):
    """Turn a raw id like 'org.mozilla.firefox' / 'google-chrome' into 'Firefox' / 'Google Chrome'."""
    name = (name or "").strip()
    if not name:
        return "Unknown"
    # reverse-DNS app ids: pick the last meaningful segment (skip filler like .Client/.desktop)
    if "." in name and " " not in name and "/" not in name:
        parts = [p for p in name.split(".") if p]
        seg = parts[-1]
        for p in reversed(parts):
            if p.lower() not in _RDNS_STOP:
                seg = p
                break
        name = seg
    name = name.replace("-", " ").replace("_", " ").strip()
    if not name:
        return "Unknown"
    return " ".join(w.capitalize() if w.islower() else w for w in name.split())


def normalize_app(raw_app, desktop_entry, name_map):
    raw_app = (raw_app or "").strip()
    desktop_entry = (desktop_entry or "").strip()
    # A generic app name (e.g. notify-send) carries no identity — prefer the desktop-entry hint.
    if raw_app.lower() in GENERIC_APPS and desktop_entry:
        candidate = desktop_entry
    else:
        candidate = raw_app
    # explicit mapping wins; try the chosen candidate, then both raw sources as backup
    for key in (candidate, raw_app, desktop_entry):
        if key and key.lower() in name_map:
            return name_map[key.lower()]
    return prettify(candidate or raw_app)


def resolve_icon(app_icon, desktop_entry, app_name):
    key = (app_icon, desktop_entry, app_name)
    if key in _icon_cache:
        return _icon_cache[key]
    result = None
    # 1) app_icon may already be an absolute file path
    if app_icon and app_icon.startswith("/") and os.path.exists(app_icon):
        result = app_icon
    else:
        candidates = []
        for n in (app_icon, desktop_entry, (app_name or "").lower().replace(" ", "-")):
            if n and not n.startswith("/"):
                candidates.append(n)
        for name in candidates:
            for size in _HICOLOR_SIZES:
                for ext in ("png", "svg"):
                    hits = glob.glob(f"/usr/share/icons/hicolor/{size}/apps/{name}.{ext}")
                    if hits:
                        result = hits[0]
                        break
                if result:
                    break
            if result:
                break
            for ext in ("png", "svg", "xpm"):
                p = f"/usr/share/pixmaps/{name}.{ext}"
                if os.path.exists(p):
                    result = p
                    break
            if result:
                break
    _icon_cache[key] = result
    return result


def main():
    name_map = load_name_map()
    rows = []
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                raw_app = rec.get("app", "")
                display = normalize_app(raw_app, rec.get("desktop_entry", ""), name_map)
                rec["app_raw"] = raw_app
                rec["app"] = display
                rec["icon_path"] = resolve_icon(
                    rec.get("app_icon", ""), rec.get("desktop_entry", ""), display
                )
                rows.append(rec)
    rows.sort(key=lambda r: r.get("ts", 0), reverse=True)
    rows = rows[:MAX_ROWS]
    import datetime as _dt
    payload = (
        "window.NOTIFICATIONS = " + json.dumps(rows, ensure_ascii=False) + ";\n"
        + 'window.GENERATED_AT = "' + _dt.datetime.now().astimezone().isoformat() + '";\n'
    )
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(payload)
    print(f"Wrote {len(rows)} notifications to {OUT_PATH}")


if __name__ == "__main__":
    main()
