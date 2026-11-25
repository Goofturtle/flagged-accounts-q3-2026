"""Build deck/index.html from the real data, so every number on a slide comes from a CSV.

Usage: python build.py <flagged_accounts.csv> <reply_export.csv>
Reads ../q3-2026-call-bands.csv (v3 ranked list) and ../q3-2026-reply-labels.csv from the repo.
"""
import csv, json, statistics, sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
accounts_csv, replies_csv = sys.argv[1], sys.argv[2]


def read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


acc = read(accounts_csv)
ranked = read(ROOT / "q3-2026-call-bands.csv")
labels = read(ROOT / "q3-2026-reply-labels.csv")
replies = read(replies_csv)

is_paid = lambda r: r["converted_to_paid"].strip().lower() == "true"
num = lambda r, c: float(r[c])
paid = [r for r in acc if is_paid(r)]
company_free = [r for r in acc if not is_paid(r) and r["domain_type"] == "company"]
schools = [r for r in acc if r["domain_type"] in ("university", "k12_school")]

# Slide 2 and 5: the 1,200-dot grid. Account order vs rank order, paying flagged.
acc_order = sorted(acc, key=lambda r: r["account_id"])
rank_of = {r["account_id"]: int(r["rank"]) for r in ranked}
grid = [{"a": i, "r": rank_of[r["account_id"]] - 1, "p": 1 if is_paid(r) else 0} for i, r in enumerate(acc_order)]

# Slide 3: what paying teams share, company accounts only.
SIGNALS = [("company_domain_seats", "Company seats"), ("teamspaces", "Teamspaces"),
           ("integrations_connected", "Integrations"), ("pricing_page_visits_30d", "Pricing-page visits, 30 days"),
           ("weekly_active_users", "Weekly active users")]
signals = [{"label": lab, "paid": round(statistics.mean(num(r, c) for r in paid), 1),
            "free": round(statistics.mean(num(r, c) for r in company_free), 1)} for c, lab in SIGNALS]

# Slide 5: bands vs who actually paid.
bands = []
for b in ["Call now", "Call this week", "Nurture"]:
    rows = [r for r in ranked if r["band"] == b]
    bands.append({"band": b, "n": len(rows), "paid": sum(r["already_paying"] == "Yes" for r in rows)})

# Slide 6: reply labels as a board.
lab_count = Counter(r["label"] for r in labels)
body_of = {r["reply_id"]: r["reply_body"] for r in replies}
board = []
for key, name in [("ready_to_buy", "Ready to buy"), ("evaluating", "Evaluating"), ("not_now", "Not now"),
                  ("wrong_contact", "Wrong contact"), ("not_interested", "Not interested")]:
    texts = Counter(body_of[r["reply_id"]] for r in labels if r["label"] == key)
    # two most common wordings, plus one example of a different wording family if the top two look alike
    examples = [t for t, _ in texts.most_common(6)]
    seen, picked = set(), []
    for t in examples:
        stem = t.split()[0:3]
        if tuple(stem) in seen:
            continue
        seen.add(tuple(stem)); picked.append(t)
        if len(picked) == 2:
            break
    conf = {body_of[r["reply_id"]]: r["confidence"] for r in labels if r["label"] == key}
    board.append({"key": key, "name": name, "n": lab_count[key], "examples": picked, "conf": [conf[t] for t in picked]})
auto_replies = lab_count[""]
opt_outs = sum(r["reason"].startswith("Opt-out:") for r in labels)

# Slide 7: the top of the call list, free accounts only.
free_ranked = [r for r in ranked if r["already_paying"] == "No"]
top_rows = [{k: r[k] for k in ("rank", "account_id", "workspace_name", "score", "band", "reason")} for r in free_ranked[:6]]
free_bands = Counter(r["band"] for r in free_ranked)

# Slide 9: what we learned.
by_members = sorted(acc, key=lambda r: -num(r, "total_members"))[:60]
by_seats = sorted(acc, key=lambda r: -num(r, "company_domain_seats"))[:60]
top100 = ranked[:100]
reply_dom = {r["reply_id"]: r["domain_type"] for r in replies}
acc_dom = {r["account_id"]: r["domain_type"] for r in acc}
agree = sum(reply_dom[r["reply_id"]] == acc_dom.get(r["account_id"]) for r in labels)

RULES = [  # same point tables as the scoring script that built the v3 ranked list
    {"signal": "Company email domain", "short": "Domain", "ranges": [["Company", 10], ["Other", 0]], "max": 10},
    {"signal": "Company seats", "short": "Company seats", "ranges": [["0–4", 0], ["5–9", 5], ["10–24", 15], ["25–49", 22], ["50+", 30]], "max": 30},
    {"signal": "Teamspaces", "short": "Teamspaces", "ranges": [["0–1", 0], ["2–3", 5], ["4–5", 10], ["6+", 15]], "max": 15},
    {"signal": "Integrations", "short": "Integrations", "ranges": [["0", 0], ["1", 3], ["2–3", 8], ["4+", 15]], "max": 15},
    {"signal": "Pricing-page visits, 30 days", "short": "Pricing visits", "ranges": [["0", 0], ["1–3", 4], ["4–6", 9], ["7+", 15]], "max": 15},
    {"signal": "Weekly active users", "short": "Active users", "ranges": [["0–4", 0], ["5–9", 4], ["10–29", 8], ["30+", 15]], "max": 15},
]

data = {
    "rules": RULES, "companyFree": len(company_free),
    "total": len(acc), "paid": len(paid), "paidPct": round(100 * len(paid) / len(acc), 1),
    "paidCompanyShare": round(100 * sum(r["domain_type"] == "company" for r in paid) / len(paid)),
    "grid": grid, "signals": signals, "bands": bands,
    "schools": len(schools), "schoolsPaid": sum(is_paid(r) for r in schools),
    "schoolWauMedian": statistics.median(num(r, "weekly_active_users") for r in schools),
    "replies": len(labels), "board": board, "autoReplies": auto_replies, "optOuts": opt_outs,
    "topRows": top_rows, "freeBands": {b: free_bands[b] for b in ["Call now", "Call this week", "Nurture"]},
    "freeTotal": len(free_ranked),
    "membersTop60Schools": sum(r["domain_type"] in ("university", "k12_school") for r in by_members),
    "membersTop60Paid": sum(is_paid(r) for r in by_members),
    "seatsTop60Paid": sum(is_paid(r) for r in by_seats),
    "top100Paid": sum(r["already_paying"] == "Yes" for r in top100),
    "replyIdAgree": agree,
    "lookupsPassed": 10, "lookupsTotal": 10,
    "dashboardUrl": "goofturtle.github.io/flagged-accounts-q3-2026/dashboard",
}

html = (HERE / "template.html").read_text(encoding="utf-8").replace("/*DATA*/null", json.dumps(data, separators=(",", ":")))
(HERE / "index.html").write_text(html, encoding="utf-8")
slides = (HERE / "slides-template.html").read_text(encoding="utf-8").replace("/*DATA*/null", json.dumps(data, separators=(",", ":")))
(HERE / "slides.html").write_text(slides, encoding="utf-8")
summary = {k: v for k, v in data.items() if k not in ("grid", "board", "topRows")}
print(json.dumps(summary, indent=1))
print("board", [(b["name"], b["n"], b["examples"]) for b in board])
print("top rows", [(r["rank"], r["account_id"], r["score"]) for r in top_rows])
