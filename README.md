# PayBack - Automated Payment Recovery Agent

Built for the Razorpay AI Builder Buildathon 2026 (Track 03).

## What it does

When a payment fails, someone usually has to manually check why and decide what to do about it - retry it, remind the customer, or just give up and send it to support. This project tries to automate that.

The agent:
1. Grabs failed payments from Razorpay (test mode)
2. Sends each one to an LLM to figure out why it failed
3. Decides what to do about it - retry, send a reminder, or escalate to a human
4. If it's not confident in its own decision, or the payment's already been retried too many times, it overrides itself and escalates instead of blindly acting
5. If something gets escalated, it takes one more look before giving up on it completely (a "second opinion" pass)
6. "Executes" the final action (simulated for now, see limitations below)
7. Logs everything and spits out a report, including a breakdown of which failure types are actually recoverable

## Why

Failed payments = lost revenue. Most of the time it's not fraud or anything scary, it's just a timeout or an expired card, and a quick retry or reminder fixes it. Doing this by hand doesn't scale.

## Results from a test run

Since the mock data is randomly generated, numbers change a bit each run, but here's one actual run:

- 5 failed payments processed
- 4 recovered (80%)
- ₹5,496 recovered out of ₹6,995 that was stuck
- 1 payment escalated after a second opinion pass didn't find a safe way to recover it

Check `report.html` after running it yourself for the numbers from that run.

## How it's built

```
fetch_payments.py    -> pulls payments from Razorpay, saves to payments_data.json
diagnose_agent.py    -> sends failed ones to Groq (LLM), decides action, logs to recovery_log.json
generate_report.py   -> turns the log into report.html (dashboard you can open in a browser)
```

`diagnose_agent.py` is the core of it. For each failed payment:
- Ask the LLM what happened and what to do about it
- If confidence is low, override to escalate (don't act on a shaky guess)
- If it already hit the retry limit (2 attempts), override to escalate instead of retrying forever
- If it ends up escalated, ask the LLM again with more context before fully giving up on it
- Simulate executing the final action and log the outcome

## Stack

- Razorpay API (test mode)
- Groq API for the LLM part (using GPT-OSS 120B, it's free and fast)
- Python, no fancy framework
- Chart.js for the chart in the report (loaded from a CDN)

## Limitations / what I'd fix with more time

- Test mode accounts don't have any real failed payments sitting around, so most of my demo data is mock data I generated myself (same format as real Razorpay responses though)
- The "execute" step is simulated - it doesn't actually call Razorpay to retry a payment or send a real reminder email. Wiring that up for real would be the next step
- No memory across runs - the agent doesn't track whether its past decisions actually worked and adjust its behavior over time
- The confidence check and retry cap are simple rule overrides, not anything the agent learns on its own

## Running it

```bash
pip install razorpay groq python-dotenv
```

Make a `.env` file with:
```
RAZORPAY_KEY_ID=your_key
RAZORPAY_KEY_SECRET=your_secret
GROQ_API_KEY=your_key
```

Then:
```bash
python fetch_payments.py
python diagnose_agent.py
python generate_report.py
```

Open `report.html` in your browser.