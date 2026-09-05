# PayBack — Autonomous Revenue Recovery Agent

An AI agent that finds failed payments, diagnoses why they failed, decides the right recovery action, executes it, and reports the results — end to end, no human in the loop until escalation.

## The problem

Every failed payment is lost (or delayed) revenue. Most businesses handle this manually or with rigid rule-based systems ("if error code X, retry once"). That misses nuance — a bank timeout and an expired card need completely different responses, and a human has to notice, classify, and act.

## What this agent does

1. **Fetch** — pulls payment data from Razorpay's test-mode API (falls back to realistic mock data matching Razorpay's exact schema when the test account has no transaction history, since test mode doesn't get organic traffic).
2. **Diagnose** — for every failed payment, sends the failure details to an LLM (Groq, running GPT-OSS 120B) which identifies the likely root cause in plain English.
3. **Decide** — the same model picks one of three recovery actions based on the diagnosis:
   - `retry` — for transient failures (bank timeout, gateway error)
   - `send_reminder` — for failures requiring customer action (insufficient funds, expired card, failed OTP)
   - `escalate` — for anything that looks like fraud or needs human review
4. **Execute** — simulates carrying out the chosen action and records the outcome.
5. **Report** — logs every decision to an audit trail (`recovery_log.json`) and renders a dashboard (`report.html`) with recovery rate, amount recovered, and a full audit table.

## Why this matters

This mirrors how real fintech recovery systems work: automated triage that gets the easy cases resolved instantly and routes only the hard cases to a human. In this run: **7 failed payments processed, 3 recovered (42.9%), ₹2,997 recovered out of ₹8,493 at risk** — with the model making context-aware decisions instead of static rules.

## Architecture

```
fetch_payments.py     → payments_data.json     (Razorpay test API + mock fallback)
diagnose_agent.py     → recovery_log.json       (Groq LLM diagnosis + decision + simulated execution)
generate_report.py    → report.html             (dashboard: summary cards, chart, audit trail)
```

## Tech stack

- **Razorpay API** (test mode) — payment data source
- **Groq API** (GPT-OSS 120B) — diagnosis and decision-making
- **Python** — orchestration
- **Chart.js** — dashboard visualization (self-contained HTML, no server needed)

## Honest limitations (things I'd build next with more time)

- Recovery execution is simulated with probabilistic outcomes, not wired to Razorpay's live retry/notification APIs — a real deployment would call Razorpay's actual payment-link and webhook APIs to execute retries and send reminders.
- Test mode has no organic failed-payment traffic, so most demo data is realistic mock data rather than payments that failed in a live checkout flow.
- No feedback loop yet — the agent doesn't learn from which of its own decisions actually worked over time.

## Running it

```bash
pip install razorpay groq python-dotenv
# add RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, GROQ_API_KEY to a .env file
python fetch_payments.py
python diagnose_agent.py
python generate_report.py
# open report.html in your browser
```