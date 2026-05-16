# ticket_watcher.py
# Single-shot fetcher for GitHub Actions cron.
# - Reads DISCORD_WEBHOOK from env
# - Loads previous state from last_state.json (committed in repo)
# - Saves new state for next run
import re, os, json, sys, random, urllib.request, urllib.error

URL = "https://webket.jp/pc/ticket/itemdetail?fc=00396&ac=8001&igc=0030&lang=0"

# 감시 대상: (날짜, 최소 시작시각 "HH:MM" — None이면 시간 조건 없음)
TARGETS = [
    ("20260525", None),
    ("20260526", "20:20"),
    ("20260527", "20:20"),
]

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "last_state.json")
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK", "")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
]


def fetch_html():
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
        "Accept-Encoding": "identity",
        "Cache-Control": "no-cache",
        "Sec-Ch-Ua": '"Chromium";v="131", "Not_A Brand";v="24"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "Referer": "https://webket.jp/",
    }
    req = urllib.request.Request(URL, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def parse_slots(html, date):
    raw = re.findall(rf'name="{date}t" value="([^"]+)"', html)
    return [tuple(s.split(",")) for s in raw]


def status_symbol(code):
    return {"00": "x", "01": "△"}.get(code, "○")


def fmt_date_label(date):
    return f"{int(date[4:6])}/{int(date[6:8])}"


def filter_open(slots, min_start):
    out = []
    for s in slots:
        start, _end, stat, _no = s
        if stat == "00":
            continue
        if min_start is not None and start < min_start:
            continue
        out.append(s)
    return out


def discord_send(message):
    if not DISCORD_WEBHOOK:
        print("[discord skip] DISCORD_WEBHOOK env not set")
        return
    data = json.dumps({"content": message}).encode()
    req = urllib.request.Request(
        DISCORD_WEBHOOK, data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(req, timeout=10).read()
        print("[discord ok]")
    except Exception as e:
        print(f"[discord err] {e}")


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def main():
    state = load_state()
    try:
        html = fetch_html()
    except urllib.error.HTTPError as e:
        print(f"[http err] {e.code} {e.reason}")
        sys.exit(0)
    except Exception as e:
        print(f"[fetch err] {e}")
        sys.exit(0)

    new_open_by_date = {}
    log_parts = []

    for date, min_start in TARGETS:
        slots = parse_slots(html, date)
        open_slots = filter_open(slots, min_start)
        open_ids = [f"{s[0]}~{s[1]}" for s in open_slots]

        prev_ids = set(state.get(date, []))
        new_ones = [s for s in open_slots if f"{s[0]}~{s[1]}" not in prev_ids]
        if new_ones:
            new_open_by_date[date] = new_ones

        state[date] = open_ids
        log_parts.append(f"{fmt_date_label(date)}:{len(open_slots)}")

    print("status: " + " ".join(log_parts))

    if new_open_by_date:
        blocks = []
        for date, slots in new_open_by_date.items():
            label = fmt_date_label(date)
            lines = [f"  {s[0]}~{s[1]} {status_symbol(s[2])}" for s in slots]
            blocks.append(f"{label}\n" + "\n".join(lines))
        body = "예약 가능 시간 오픈\n" + "\n".join(blocks) + f"\n\n{URL}"
        print(">>> NOTIFY:\n" + body)
        discord_send(f"**SHIBUYA SKY 예약 오픈**\n```\n{body}\n```")
    else:
        print("no new openings")

    save_state(state)


if __name__ == "__main__":
    main()
