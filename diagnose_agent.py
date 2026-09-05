# Script 2 - the actual agent
# reads payments_data.json, finds failed ones, asks the LLM what happened
# and what to do about it, then fakes executing that action and logs it all

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise SystemExit("Missing GROQ_API_KEY in .env")

client = Groq(api_key=GROQ_API_KEY)

MODEL = "openai/gpt-oss-120b"  # llama-3.3-70b got deprecated by groq, this is what they recommend now


def diagnose_and_decide(payment):
    # asking the model to just give back JSON so I can parse it directly
    prompt = f"""You are a payment recovery agent for a fintech company. Analyze this failed payment and respond with ONLY a JSON object, no other text.

Payment details:
- Payment ID: {payment['id']}
- Amount: ₹{payment['amount'] / 100}
- Method: {payment['method']}
- Error code: {payment.get('error_code', 'unknown')}
- Error description: {payment.get('error_description', 'unknown')}
- Error reason: {payment.get('error_reason', 'unknown')}

Decide the best recovery action from these options only:
- "retry": if the failure was likely transient (e.g. bank timeout, gateway error) and retrying now could work
- "send_reminder": if the customer needs to take action (e.g. insufficient funds, OTP failed, card expired) — send them a payment link reminder
- "escalate": if this looks like fraud, repeated failure, or needs human review

Respond with ONLY this JSON structure, nothing else:
{{
  "diagnosis": "one sentence explaining the root cause in plain English",
  "recovery_action": "retry" or "send_reminder" or "escalate",
  "confidence": "high" or "medium" or "low",
  "reasoning": "one sentence on why this action was chosen"
}}"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=300,
    )

    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()  # sometimes it wraps json in markdown anyway

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # fallback so one bad response doesn't kill the whole run
        return {
            "diagnosis": "Could not parse model response",
            "recovery_action": "escalate",
            "confidence": "low",
            "reasoning": f"Raw response: {raw[:200]}",
        }


def apply_confidence_check(decision):
    # if the model isn't confident, don't trust its action - escalate instead
    # a "retry" with low confidence could waste an attempt, better to be safe
    if decision["confidence"] == "low" and decision["recovery_action"] != "escalate":
        decision["original_action"] = decision["recovery_action"]
        decision["recovery_action"] = "escalate"
        decision["reasoning"] += " (overridden to escalate due to low confidence)"
    return decision


def simulate_execute_action(payment, decision):
    # not actually hitting Razorpay here, just faking an outcome
    # would need real retry/checkout APIs for this to actually do something
    import random

    action = decision["recovery_action"]

    if action == "retry":
        success = random.random() < 0.55
    elif action == "send_reminder":
        success = random.random() < 0.35
    else:  # escalate
        success = False

    return {
        "action_taken": action,
        "outcome": "recovered" if success else "pending" if action != "escalate" else "escalated_to_human",
        "recovered_amount": payment["amount"] if success else 0,
    }


def run_pipeline():
    with open("payments_data.json", "r") as f:
        payments = json.load(f)

    failed_payments = [p for p in payments if p["status"] == "failed"]
    print(f"Found {len(failed_payments)} failed payment(s) to process.\n")

    audit_log = []

    for i, payment in enumerate(failed_payments, 1):
        print(f"[{i}/{len(failed_payments)}] Processing {payment['id']}...")

        decision = diagnose_and_decide(payment)
        decision = apply_confidence_check(decision)
        print(f"    Diagnosis: {decision['diagnosis']}")
        print(f"    Action: {decision['recovery_action']} (confidence: {decision['confidence']})")

        result = simulate_execute_action(payment, decision)
        print(f"    Result: {result['outcome']}\n")

        audit_log.append({
            "payment_id": payment["id"],
            "amount": payment["amount"],
            "original_error": payment.get("error_description", "unknown"),
            "diagnosis": decision["diagnosis"],
            "recovery_action": decision["recovery_action"],
            "confidence": decision["confidence"],
            "reasoning": decision["reasoning"],
            "outcome": result["outcome"],
            "recovered_amount": result["recovered_amount"],
            "timestamp": datetime.now().isoformat(),
        })

    with open("recovery_log.json", "w") as f:
        json.dump(audit_log, f, indent=2)

    total_failed_amount = sum(p["amount"] for p in failed_payments)
    total_recovered = sum(entry["recovered_amount"] for entry in audit_log)
    recovered_count = sum(1 for entry in audit_log if entry["outcome"] == "recovered")

    print("=" * 50)
    print("RECOVERY SUMMARY")
    print("=" * 50)
    print(f"Total failed payments processed: {len(failed_payments)}")
    print(f"Successfully recovered: {recovered_count}")
    print(f"Total amount at risk: ₹{total_failed_amount / 100:,.2f}")
    print(f"Total amount recovered: ₹{total_recovered / 100:,.2f}")
    if len(failed_payments) > 0:
        print(f"Recovery success rate: {(recovered_count / len(failed_payments)) * 100:.1f}%")
    print(f"\nFull audit trail saved to recovery_log.json")


if __name__ == "__main__":
    run_pipeline()