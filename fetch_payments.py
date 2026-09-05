# Script 1 - get payment data from Razorpay
# Test mode accounts start empty so this also has a fallback that
# generates fake payments if there's nothing real to pull

import os
import json
from datetime import datetime
from dotenv import load_dotenv
import razorpay

load_dotenv()

KEY_ID = os.getenv("RAZORPAY_KEY_ID")
KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

if not KEY_ID or not KEY_SECRET:
    raise SystemExit("Missing RAZORPAY_KEY_ID or RAZORPAY_KEY_SECRET in .env")

client = razorpay.Client(auth=(KEY_ID, KEY_SECRET))


def fetch_real_payments(count=20):
    # just pulls whatever's in the test account
    try:
        payments = client.payment.all({"count": count})
        return payments.get("items", [])
    except Exception as e:
        print(f"Error fetching payments: {e}")
        return []


def generate_mock_payments(n=15):
    # test mode has no real traffic so I made this to fake some data
    # same fields as real Razorpay payments so the rest of the pipeline
    # doesn't care if it's real or not
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
        is_failed = random.random() < 0.4  # roughly 40% fail, felt realistic enough
        payment_id = f"pay_MOCK{1000+i}"
        base = {
            "id": payment_id,
            "entity": "payment",
            "amount": random.choice([49900, 99900, 149900, 199900, 299900]),  # paise
            "currency": "INR",
            "status": "failed" if is_failed else "captured",
            "order_id": f"order_MOCK{2000+i}",
            "method": random.choice(["card", "upi", "netbanking"]),
            "email": f"customer{i}@example.com",
            "contact": f"+91900000{1000+i}",
            "created_at": int(datetime.now().timestamp()) - (i * 3600),
            "retry_count": random.choice([0, 0, 0, 1, 1, 2]),  # most payments haven't been retried yet, a few have
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
        print(f"Found {len(real)} real payment(s).")
        data_to_use = real
    else:
        print("Nothing in the test account (expected). Generating fake data instead...\n")
        data_to_use = generate_mock_payments(15)

    output_path = "payments_data.json"
    with open(output_path, "w") as f:
        json.dump(data_to_use, f, indent=2)

    failed_count = sum(1 for p in data_to_use if p["status"] == "failed")
    print(f"Saved {len(data_to_use)} payments to {output_path}")
    print(f"  -> {failed_count} failed, {len(data_to_use) - failed_count} captured")
    print("\nNext: run diagnose_agent.py")