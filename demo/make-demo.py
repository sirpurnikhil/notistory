#!/usr/bin/env python3
"""Builds a fully synthetic demo dataset for screenshots and the GitHub Pages demo.

Outputs:
  demo/demo-notifications.jsonl   raw sanitized sample data (committed)
  src/data.js                     populated for local screenshots (git-ignored)
  docs/index.html                 self-contained live demo for GitHub Pages

No real notifications are ever touched.
"""
import json, os, importlib.util, time
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "src")
DOCS = os.path.join(ROOT, "docs")

# Import the real generator so the demo goes through identical normalization/icon logic.
spec = importlib.util.spec_from_file_location("gen", os.path.join(SRC, "generate-data.py"))
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

# (minutes_ago, app, desktop_entry, summary, body, urgency)
DEMO = [
    (2,    "Slack",         "",                    "Alex Rivera",          "Can you review the PR when you get a sec?", 1),
    (8,    "Google Chrome", "google-chrome",       "Calendar",             "Design sync in 15 minutes — Meet link ready", 1),
    (15,   "Spotify",       "spotify",             "Now Playing",          "Midnight City — M83", 0),
    (34,   "Thunderbird",   "thunderbird",         "GitHub",               "Your Actions workflow run succeeded", 1),
    (52,   "KDE Connect",   "org.kde.kdeconnect",  "Pixel 9 Pro",          "Battery low: 18% remaining", 2),
    (70,   "VS Code",       "code",                "Extension updated",    "Python extension updated to v2026.6.0", 0),
    (95,   "Terminal",      "",                    "Build finished",       "npm run build completed in 42s", 1),
    (130,  "Google Chrome", "google-chrome",       "YouTube",              "Fireship uploaded: '100 Seconds of Rust'", 1),
    (200,  "Slack",         "",                    "CI / CD",              "Deployment to staging succeeded ✅", 1),
    (260,  "Firefox",       "firefox",             "Download complete",    "ubuntu-24.04.iso finished downloading", 1),
    (1500, "Discord",       "discord",             "#dev-team",            "3 new messages in dev-team", 1),
    (1580, "System",        "",                    "Software Updates",     "14 package updates available", 1),
    (1800, "Thunderbird",   "thunderbird",         "Newsletter",           "This Week in Open Source is here", 0),
    (2880, "Spotify",       "spotify",             "Discover Weekly",      "Your new mixtape is ready", 0),
]


def build_records():
    now = time.time()
    recs = []
    for minutes, app, de, summary, body, urgency in DEMO:
        ts = now - minutes * 60
        recs.append({
            "ts": ts,
            "mins_ago": minutes,
            "iso": datetime.fromtimestamp(ts).astimezone().isoformat(),
            "app": app,
            "app_icon": "",
            "desktop_entry": de,
            "summary": summary,
            "body": body,
            "urgency": urgency,
        })
    return recs


def process(recs, resolve_icons):
    name_map = gen.load_name_map()
    out = []
    for r in recs:
        r = dict(r)
        display = gen.normalize_app(r["app"], r["desktop_entry"], name_map)
        r["app_raw"] = r["app"]
        r["app"] = display
        r["icon_path"] = gen.resolve_icon(r["app_icon"], r["desktop_entry"], display) if resolve_icons else None
        out.append(r)
    out.sort(key=lambda x: x["ts"], reverse=True)
    return out


def write_data_js(rows, path):
    payload = ("window.NOTIFICATIONS = " + json.dumps(rows, ensure_ascii=False) + ";\n"
               + 'window.GENERATED_AT = "' + datetime.now().astimezone().isoformat() + '";\n')
    with open(path, "w", encoding="utf-8") as f:
        f.write(payload)


def write_docs(rows):
    os.makedirs(DOCS, exist_ok=True)
    css = open(os.path.join(SRC, "style.css"), encoding="utf-8").read()
    appjs = open(os.path.join(SRC, "app.js"), encoding="utf-8").read()
    index = open(os.path.join(SRC, "index.html"), encoding="utf-8").read()
    # Timestamps are recomputed in the browser from `mins_ago` so the public demo always
    # reads as "just now / today" instead of ageing away from the build date.
    data = ("window.NOTIFICATIONS = " + json.dumps(rows, ensure_ascii=False) + ";\n"
            + "(function () {\n"
            + "  var now = Date.now() / 1000;\n"
            + "  window.NOTIFICATIONS.forEach(function (n) {\n"
            + "    n.ts = now - n.mins_ago * 60;\n"
            + "    n.iso = new Date(n.ts * 1000).toISOString();\n"
            + "  });\n"
            + "  window.GENERATED_AT = new Date().toISOString();\n"
            + "})();")
    # Inline everything so the page is self-contained (GitHub Pages, no server).
    index = index.replace('<link rel="stylesheet" href="style.css">', f"<style>\n{css}\n</style>")
    index = index.replace('<script src="data.js"></script>', f"<script>\n{data}\n</script>")
    index = index.replace('<script src="app.js"></script>', f"<script>\n{appjs}\n</script>")
    banner = ('<div style="background:#3b82f6;color:#fff;text-align:center;'
              'padding:6px;font:600 13px system-ui">Live demo — synthetic sample data. '
              'Runs locally on Linux via the recorder.</div>')
    index = index.replace("<body>", "<body>\n" + banner)
    with open(os.path.join(DOCS, "index.html"), "w", encoding="utf-8") as f:
        f.write(index)


def main():
    recs = build_records()
    # raw sample (committed, no machine-specific icon paths)
    with open(os.path.join(HERE, "demo-notifications.jsonl"), "w", encoding="utf-8") as f:
        for r in recs:
            row = {k: v for k, v in r.items() if k != "mins_ago"}  # keep the sample schema-identical to real data
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    # local screenshot build — resolve real icons for a richer shot
    write_data_js(process(recs, resolve_icons=True), os.path.join(SRC, "data.js"))
    # GitHub Pages demo — no file:// icon paths (won't exist off this machine)
    write_docs(process(recs, resolve_icons=False))
    print("Demo built: demo-notifications.jsonl, src/data.js (screenshot), docs/index.html (pages)")


if __name__ == "__main__":
    main()
