"""
Script 1: Razorpay Test Payment Generator + Fetcher
-----------------------------------------------------
This does two things:
1. Creates a batch of test "Payment Links" on Razorpay (some will succeed, some will fail,
   simulated using Razorpay's test mode behavior).
2. Fetches back the list of recent payments so we can see which ones failed and why.

Why Payment Links and not raw orders?
Razorpay's test mode doesn't let us programmatically force a payment to "fail" via the API directly
for card payments (that requires actual checkout UI interaction with test card numbers).
So for the hackathon demo, we'll do this in two parts:
  - Part A (this script): Pull whatever real payment data exists in your test account.
  - Part B: If your account has no payments yet, we generate REALISTIC MOCK payment data
    that matches Razorpay's exact response schema, so the rest of the agent pipeline
    can be built and tested immediately without blocking on manual checkout clicks.

Run this first to see what's in your account.
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
import razorpay

load_dotenv()

KEY_ID = os.getenv("RAZORPAY_KEY_ID")
KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

if not KEY_ID or not KEY_SECRET:
    raise SystemExit("Missing RAZORPAY_KEY_ID or RAZORPAY_KEY_SECRET in .env — check your .env file.")

client = razorpay.Client(auth=(KEY_ID, KEY_SECRET))


def fetch_real_payments(count=20):
    """Pull the most recent payments from your Razorpay test account."""
    try:
        payments = client.payment.all({"count": count})
        return payments.get("items", [])
    except Exception as e:
        print(f"Error fetching payments: {e}")
        return []


def generate_mock_payments(n=15):
    """
    Generate realistic mock payment records matching Razorpay's schema.
    Used when the test account has no real payment history yet.
    This lets us build/test the diagnosis + recovery agent without
    needing to manually click through checkout n times.
    """
    import random

    fail_reasons = [
        {"error_code": "BAD_REQUEST_ERROR", "error_description": "Payment failed due to insufficient funds in the customer's account.", "error_reason": "insufficient_funds"},
        {"error_code": "GATEWAY_ERROR", "error_description": "Card issuing bank declined the transaction.", "error_reason": "card_declined"},
        {"error_code": "GATEWAY_ERROR", "error_description": "The transaction timed out due to bank server delay.", "error_reason": "bank_timeout"},
        {"error_code": "BAD_REQUEST_ERROR", "error_description": "Payment failed due to incorrect OTP entered.", "error_reason": "otp_failed"},
        {"error_code": "GATEWAY_ERROR", "error_description": "Card expired.", "error_reason": "card_expired"},
    ]

    mock_payments = []
    for i in range(n):
        is_failed = random.random() < 0.4  # ~40% fail rate for a realistic demo
        payment_id = f"pay_MOCK{1000+i}"
        base = {
            "id": payment_id,
            "entity": "payment",
            "amount": random.choice([49900, 99900, 149900, 199900, 299900]),  # in paise
            "currency": "INR",
            "status": "failed" if is_failed else "captured",
            "order_id": f"order_MOCK{2000+i}",
            "method": random.choice(["card", "upi", "netbanking"]),
            "email": f"customer{i}@example.com",
            "contact": f"+91900000{1000+i}",
            "created_at": int(datetime.now().timestamp()) - (i * 3600),
        }
        if is_failed:
            reason = random.choice(fail_reasons)
            base.update(reason)
        mock_payments.append(base)

    return mock_payments


if __name__ == "__main__":
    print("Fetching real payments from your Razorpay test account...\n")
    real = fetch_real_payments()

    if real:
        print(f"Found {len(real)} real payment(s) in your account.")
        data_to_use = real
    else:
        print("No real payments found (expected, since test mode has no organic traffic).")
        print("Generating 15 realistic mock payments instead...\n")
        data_to_use = generate_mock_payments(15)

    # Save to a local JSON file so the next script (diagnosis agent) can read it
    output_path = "payments_data.json"
    with open(output_path, "w") as f:
        json.dump(data_to_use, f, indent=2)

    failed_count = sum(1 for p in data_to_use if p["status"] == "failed")
    print(f"Saved {len(data_to_use)} payments to {output_path}")
    print(f"  -> {failed_count} failed, {len(data_to_use) - failed_count} captured/successful")
    print("\nNext: run the diagnosis agent script on this data.")