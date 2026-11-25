# Q3 2026 flagged accounts and reply labels

| File | What it is |
|---|---|
| `q3-2026-reply-labels.csv` | Buying-intent label for each of the 840 replies in the Q3 2026 Outbound Email Reply Export |
| `q3-2026-conversion-analysis.html` | Converted vs not-converted comparison and the 0–100 lead-scoring rules |
| `dashboard/index.html` | Call list dashboard: a rep types or picks an account and sees its rank, score, band and reason |
| `dashboard/paying-account-lookup.png` | The dashboard showing a paying account (ACC-10070) |
| `.env.example` | Copy to `.env` and add `OPENROUTER_API_KEY`. `.env` is git-ignored. |

## Call list dashboard

Open `dashboard/index.html` from any web server, for example `python -m http.server 3590` in this folder, then go to `http://localhost:3590/dashboard/`. It needs an internet connection, because it reads the data from Google Sheets.

**Where the numbers come from:** the page reads the "Ranked call list" tab of the [Q3 2026 Ranked Call List v3](https://docs.google.com/spreadsheets/d/1iGSvshfq0duZX7YIIByxbNwJYSdMqWXHZJoRLZ7vsmw/edit) Google Sheet as CSV every time it loads. No rank, score, band, reason or count is typed into the page. If the sheet can't be loaded, the page says so instead of showing anything. The header line confirms how many accounts loaded and that none is missing a score or reason.

**Bands** (from the rep lookup brief): Call now 80–100, Call this week 50–79, Nurture 0–49. All 1,200 accounts are ranked by score. The 60 paying accounts keep their score rank and show an "Already paying" badge.

**The 10 rep lookups, checked in the browser against the sheet:**

| # | Lookup | Result |
|---|---|---|
| 1 | `ACC-10001` | Rank 1,114 of 1,200, score 0, Nurture |
| 2 | `ACC-10587` | Rank 404, score 27, Nurture |
| 3 | `ACC-11200` | Rank 1,200, score 0, Nurture (the last account loads) |
| 4 | ` ACC-10342` (leading space) | Same card as `ACC-10342`: rank 1,023 |
| 5 | `acc-10918` (lower case) | Same card as `ACC-10918`: rank 606 |
| 6 | `ACC-11347` | "isn't in the Q3 ranked call list … so it has no score yet" |
| 7 | Pick by workspace name | Dropdown of all 1,200 accounts grouped by workspace name, with ID and rank; picking one shows the same card |
| 8 | Domain type = Schools | Top school is ACC-10575 at rank 591, and its reason gives the student sign-up count |
| 9 | Band = Call now | 63 accounts, ranks 1 to 63, all scoring 80 or more |
| 10 | A paying account (ACC-10070) | Rank 1, score 100, Call now, "Already paying" badge and banner; no row on the page has a blank score or reason |

### Main prompt

```text
Build a one-page call list dashboard at flagged-accounts-q3-2026/dashboard/index.html for Sales Development reps. Plain HTML, CSS and JavaScript in one file, no framework and no build step.

Data: on every load, fetch the "Ranked call list" tab of the Q3 2026 Ranked Call List v3 Google Sheet as CSV (gviz endpoint). Columns: Rank, account_id, workspace_name, Score, Band, Reason, Already paying, domain_type, rep_owner. Never type or hard-code a rank, score, band, reason or count. Every value on the page comes from that fetch. If the fetch fails or a column is missing, say so plainly instead of showing anything. Show how many accounts loaded and whether any row is missing a score or reason.

Lookup: a text box for the account ID. Remove spaces and upper-case it before matching, so " ACC-10342" and "acc-10918" find the account. Show rank "of 1,200", score out of 100, band and the one-line reason, plus the account ID, workspace name, domain type and rep. If the ID isn't in the list, show a plain message that it isn't in the Q3 list and has no score. Never crash or show a blank card.

Picker: a dropdown of every account grouped by workspace name, each option showing the name, ID and rank. Picking one shows the same card as typing the ID.

Paying accounts: when Already paying is Yes, show an "Already paying" badge and a line telling the rep it is already a customer.

Ranked list: a table under the card, sorted by rank, with filters for band, domain type (including "Schools: university + K-12") and paying status. Show every row when a filter leaves 100 or fewer; otherwise show 50 with a "Show all" button. Clicking a row opens its card.

Design: flat and readable at a glance, Inter, one blue accent, band pills, 44 px touch targets, keyboard focus visible, works at 375 px wide.

Before finishing, run all 10 lookups from "Rep Lookup Requests for the Call List Dashboard Demo" in a browser and check every answer against the account's row in the Google Sheet.
```

**Note on the prompt:** the key line is the data rule. Every number comes from the live Google Sheet, so the dashboard and the sheet can't disagree. The bands in the sheet were changed to the brief's 80/50 cut-offs first, so the page only has to display them, not work them out.

## Reply labels

`q3-2026-reply-labels.csv` columns: `reply_id, account_id, label, confidence, reason`. One row per reply, in source order.

| Label | Meaning | Replies |
|---|---|---|
| `ready_to_buy` | Asks for a price, quote, order form, contract or volume discount, or how to upgrade the team | 66 |
| `evaluating` | Actively considering it: comparing with a competitor, trialling tools, or asking a product, security, SSO, import or integration question | 198 |
| `not_now` | Open to it later: timing, budget, reorg, planning cycle, or happy on the free plan for now | 202 |
| `not_interested` | A firm no, chose another tool, asked to stop emailing, or a student or personal pricing question | 193 |
| `wrong_contact` | The sender isn't the decision-maker and names or forwards to someone else | 112 |
| blank | Auto-reply (out of office, travelling, on leave, unmonitored mailbox). No person has answered yet. | 69 |

- **Opt-outs:** the 89 replies asking to unsubscribe or stop emailing are labelled `not_interested`, with a reason starting `Opt-out:`. Filter on that prefix to suppress those addresses.
- **Auto-replies:** these have a blank label and a reason starting `Auto-reply:`.
- **Confidence:** 571 replies are `high` and 269 are `medium`. `medium` marks the awkward calls listed in the prompt below. No reply is `low`.

## Model

The labels were assigned by **Claude Opus 5.5 (`claude-opus-5-5`)** running in Claude Code. The 840 replies use only 141 distinct wordings, which fall into 38 families that differ only by a number (such as a seat count). Claude labelled each family once, and a script applied that label to every matching row. The script checks that each reply matches exactly one family.

The free OpenRouter model `google/gemma-4-31b-it:free` was tried first. It was rate-limited upstream (HTTP 429) and returned no labels, so none of the labels here come from it.

## Prompt

```text
Label every reply in this file with one buying-intent label:
C:\Users\arjun\Downloads\Q3 2026 Outbound Email Reply Export.csv
(840 rows; columns reply_id, account_id, domain_type, outbound_sender, outbound_campaign, reply_received_date, reply_subject, reply_body)

Labels (use these exact names; the next stage joins on them):
- ready_to_buy: asks for a price, quote, order form, contract or volume discount, or asks how to upgrade the team.
- evaluating: actively considering it; compares with a competitor, is trialling tools, or asks a product, security, SSO, import or integration question.
- not_now: open to it later; timing, budget, reorg, planning cycle, or happy on the free plan for now.
- not_interested: a firm no or a request to stop emailing.
- wrong_contact: the sender isn't the decision-maker and names or forwards to someone else.

Calls for awkward replies:
- "Unsubscribe", "Please remove me from this list", "We don't plan to pay for a docs tool. Please stop emailing.": not_interested. Start the reason with "Opt-out:" so these addresses can be suppressed.
- "We just signed with Confluence…" and "We're consolidating on Microsoft Loop…": not_interested (they chose another tool).
- Out-of-office, travelling, on leave, "This mailbox is not monitored": leave label blank, confidence high, reason starting "Auto-reply:". No person has answered yet.
- Student or personal pricing questions (student discount, Education plan per student, free Plus for a club, price after graduating): not_interested, reason "Student/personal pricing, not a team buyer".
- "Is there a volume discount above N seats? We're comparing your quote to Confluence's.": ready_to_buy (they already hold a quote), not evaluating.
- "We have N people in the workspace already. What's the process to upgrade everyone and get SSO?": ready_to_buy.
- "Love the product, happy on free for the moment.": not_now, not not_interested.
- "Forwarding to our head of engineering…" and "Procurement decides on anything with more than N users": wrong_contact.
- Label from the reply_body text only. Don't change a label because of domain_type, and don't join to the flagged-accounts file; its account_id link doesn't line up with this export.

Confidence:
- high: the wording clearly matches one label.
- medium: one of the awkward calls above, or two labels were close.
- low: unclear; flag it for a person to check.

Save the result in the repo as flagged-accounts-q3-2026/q3-2026-reply-labels.csv with exactly these columns, in this order:
reply_id, account_id, label, confidence, reason
- One row per reply_id, all 840, in the same order as the source file.
- reason: one short sentence (under 15 words) saying why.
- Never write the .env file or the OpenRouter key into the output, and don't commit .env.

Before finishing, check: 840 rows, no duplicate or missing reply_id, every label is one of the five names or blank (blank only for auto-replies), and report the count per label.
```

## What changed or was rejected

**Changed**
- **Eight labels became five.** The first draft had eight: Ready to buy, Evaluating, Referred, Not now, Student pricing, Not interested, Opt-out and Auto-reply. They were mapped onto the team's five names because the next stage joins on them.
- **Opt-outs:** folded into `not_interested`. They're kept visible with the `Opt-out:` reason prefix rather than a separate `do_not_contact` column, because the output is fixed at five columns.
- **Auto-replies:** given a blank label instead of being forced into `not_now`, which would count 69 people who never answered.
- **Student pricing:** put in `not_interested` rather than `wrong_contact`, so reps don't go looking for a decision-maker a student club doesn't have.

**Rejected**
- **Checking labels against the Q3 conversions.** The account_id link between the two files doesn't hold: domain type agrees for only 343 of 840 replies, and the sender matches the account's rep for only 294.
- **Adjusting labels by domain_type.** Six `ready_to_buy` replies come from personal-domain accounts (for example RPL-0840, which asks for a 56-seat order form). They keep the label their text earned. Check who sent them before quoting.
- **The free OpenRouter run.** It was rate-limited and produced nothing. Its script (`label_replies.py`) isn't committed.
