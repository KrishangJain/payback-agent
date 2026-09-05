# Script 3 - turns recovery_log.json into an actual html report
# nothing fancy, just cards + a chart + a table, all in one html file
# opens straight in a browser, no server needed

import json
from datetime import datetime

with open("recovery_log.json", "r") as f:
    log = json.load(f)

with open("payments_data.json", "r") as f:
    all_payments = json.load(f)

total_payments = len(all_payments)
failed_payments = [p for p in all_payments if p["status"] == "failed"]
total_failed = len(failed_payments)
total_failed_amount = sum(p["amount"] for p in failed_payments)

recovered_entries = [e for e in log if e["outcome"] == "recovered"]
total_recovered = len(recovered_entries)
total_recovered_amount = sum(e["recovered_amount"] for e in log)
success_rate = (total_recovered / total_failed * 100) if total_failed else 0

# Action breakdown for chart
action_counts = {}
for entry in log:
    action = entry["recovery_action"]
    action_counts.setdefault(action, {"recovered": 0, "pending": 0, "escalated_to_human": 0})
    outcome = entry["outcome"]
    if outcome in action_counts[action]:
        action_counts[action][outcome] += 1

action_labels = list(action_counts.keys())
recovered_data = [action_counts[a]["recovered"] for a in action_labels]
pending_data = [action_counts[a]["pending"] for a in action_labels]
escalated_data = [action_counts[a]["escalated_to_human"] for a in action_labels]

# Build audit trail table rows
def outcome_badge(outcome):
    colors = {
        "recovered": "#16a34a",
        "pending": "#d97706",
        "escalated_to_human": "#dc2626",
    }
    labels = {
        "recovered": "Recovered",
        "pending": "Pending",
        "escalated_to_human": "Escalated",
    }
    color = colors.get(outcome, "#6b7280")
    label = labels.get(outcome, outcome)
    return f'<span style="background:{color}1a;color:{color};padding:4px 10px;border-radius:999px;font-size:12px;font-weight:600;">{label}</span>'

table_rows = ""
for entry in log:
    table_rows += f"""
    <tr>
      <td style="font-family:monospace;font-size:13px;color:#475569;">{entry['payment_id']}</td>
      <td>₹{entry['amount']/100:,.2f}</td>
      <td style="max-width:280px;color:#334155;font-size:13px;">{entry['diagnosis']}</td>
      <td style="text-transform:capitalize;">{entry['recovery_action'].replace('_',' ')}</td>
      <td>{outcome_badge(entry['outcome'])}</td>
      <td>₹{entry['recovered_amount']/100:,.2f}</td>
    </tr>"""

generated_at = datetime.now().strftime("%B %d, %Y at %I:%M %p")

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>PayBack — Autonomous Revenue Recovery Report</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #f8fafc;
    color: #0f172a;
    padding: 40px 24px;
  }}
  .container {{ max-width: 1000px; margin: 0 auto; }}
  header {{ margin-bottom: 32px; }}
  header h1 {{ font-size: 28px; font-weight: 700; margin-bottom: 4px; }}
  header p {{ color: #64748b; font-size: 14px; }}
  .cards {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 32px;
  }}
  .card {{
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 20px;
  }}
  .card .label {{ font-size: 12px; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.03em; margin-bottom: 8px; }}
  .card .value {{ font-size: 26px; font-weight: 700; }}
  .card.green .value {{ color: #16a34a; }}
  .card.blue .value {{ color: #2563eb; }}
  .panel {{
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 24px;
  }}
  .panel h2 {{ font-size: 16px; font-weight: 700; margin-bottom: 16px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{
    text-align: left;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    color: #64748b;
    padding: 10px 12px;
    border-bottom: 2px solid #e2e8f0;
  }}
  td {{
    padding: 12px;
    border-bottom: 1px solid #f1f5f9;
    font-size: 14px;
  }}
  tr:hover td {{ background: #f8fafc; }}
  canvas {{ max-height: 280px; }}
  footer {{ text-align: center; color: #94a3b8; font-size: 12px; margin-top: 32px; }}
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>PayBack — Autonomous Revenue Recovery Agent</h1>
    <p>Generated on {generated_at} · {total_payments} payments analyzed</p>
  </header>

  <div class="cards">
    <div class="card">
      <div class="label">Failed Payments</div>
      <div class="value">{total_failed}</div>
    </div>
    <div class="card green">
      <div class="label">Recovered</div>
      <div class="value">{total_recovered}</div>
    </div>
    <div class="card blue">
      <div class="label">Success Rate</div>
      <div class="value">{success_rate:.1f}%</div>
    </div>
    <div class="card green">
      <div class="label">Amount Recovered</div>
      <div class="value">₹{total_recovered_amount/100:,.0f}</div>
    </div>
  </div>

  <div class="panel">
    <h2>Recovery Outcomes by Action Type</h2>
    <canvas id="outcomeChart"></canvas>
  </div>

  <div class="panel">
    <h2>Audit Trail</h2>
    <table>
      <thead>
        <tr>
          <th>Payment ID</th>
          <th>Amount</th>
          <th>AI Diagnosis</th>
          <th>Action Taken</th>
          <th>Outcome</th>
          <th>Recovered</th>
        </tr>
      </thead>
      <tbody>
        {table_rows}
      </tbody>
    </table>
  </div>

  <footer>Built with Groq (GPT-OSS 120B) powered diagnosis · Razorpay test-mode data · PayBack Agent v1</footer>
</div>

<script>
  const ctx = document.getElementById('outcomeChart');
  new Chart(ctx, {{
    type: 'bar',
    data: {{
      labels: {json.dumps(action_labels)},
      datasets: [
        {{ label: 'Recovered', data: {json.dumps(recovered_data)}, backgroundColor: '#16a34a' }},
        {{ label: 'Pending', data: {json.dumps(pending_data)}, backgroundColor: '#d97706' }},
        {{ label: 'Escalated', data: {json.dumps(escalated_data)}, backgroundColor: '#dc2626' }}
      ]
    }},
    options: {{
      responsive: true,
      scales: {{
        x: {{ stacked: true }},
        y: {{ stacked: true, beginAtZero: true, ticks: {{ stepSize: 1 }} }}
      }},
      plugins: {{ legend: {{ position: 'bottom' }} }}
    }}
  }});
</script>
</body>
</html>"""

with open("report.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Dashboard generated: report.html")
print("Open it in your browser to view the demo report.")