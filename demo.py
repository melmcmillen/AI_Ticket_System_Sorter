"""
AI-Powered Ticket Triage Pipeline — Full Demo (single file)
Run with: python run_demo.py
Requires: pip install "pandas>=2.3.3" "anthropic>=0.40" "faker>=30.0" "jinja2>=3.1"
Requires env var: ANTHROPIC_API_KEY
"""

import pandas as pd
from faker import Faker
import random, json, datetime
from anthropic import Anthropic
from jinja2 import Template

# ---------- CONFIG ----------
NUM_TICKETS = 300        # total synthetic tickets generated
NUM_TO_PROCESS = 25       # how many get sent to the AI (keep low for demo cost/speed)
MODEL = "claude-sonnet-4-5"

client = Anthropic()  # reads ANTHROPIC_API_KEY from environment
fake = Faker()

CATEGORIES = ["Login Issue", "Billing Error", "Feature Request",
              "Performance Bug", "Data Sync Failure", "UI Glitch"]

CLASSIFY_PROMPT = """You are a support triage assistant. Classify this ticket.

Subject: {subject}
Body: {body}
Customer tier: {tier}

Return ONLY valid JSON with this exact structure, no other text:
{{
  "severity": "Low" | "Medium" | "High" | "Critical",
  "category": "Login Issue" | "Billing Error" | "Feature Request" | "Performance Bug" | "Data Sync Failure" | "UI Glitch" | "Other",
  "root_cause_guess": "<one short sentence>",
  "suggested_response": "<2-3 sentence draft reply to the customer>",
  "confidence": <float 0.0-1.0>,
  "needs_human_review": <true/false, true if confidence < 0.75 or severity is Critical>
}}"""


# ---------- STEP 1: GENERATE SYNTHETIC DATA ----------
def generate_tickets(n=NUM_TICKETS):
    print(f"[1/3] Generating {n} synthetic support tickets...")
    rows = []
    for i in range(n):
        cat = random.choice(CATEGORIES)
        rows.append({
            "ticket_id": f"TCK-{1000+i}",
            "subject": f"{cat}: {fake.sentence(nb_words=6)}",
            "body": fake.paragraph(nb_sentences=4) + f" This started after {fake.word()} update.",
            "customer_tier": random.choice(["Free", "Pro", "Enterprise"]),
            "created_at": fake.date_time_between(start_date="-14d", end_date="now")
        })
    df = pd.DataFrame(rows)
    df.to_csv("tickets_raw.csv", index=False)
    print(f"      Saved -> tickets_raw.csv")
    return df


# ---------- STEP 2: AI TRIAGE ----------
def classify_ticket(row):
    prompt = CLASSIFY_PROMPT.format(subject=row["subject"], body=row["body"], tier=row["customer_tier"])
    resp = client.messages.create(
        model=MODEL,
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}]
    )
    text = resp.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"severity": "Unknown", "category": "Other", "root_cause_guess": "parse_error",
                "suggested_response": "", "confidence": 0.0, "needs_human_review": True}

def run_triage(df):
    print(f"[2/3] Running AI triage on {NUM_TO_PROCESS} tickets via {MODEL}...")
    subset = df.head(NUM_TO_PROCESS)
    results = []
    for _, row in subset.iterrows():
        result = classify_ticket(row)
        results.append({**row.to_dict(), **result})
        print(f"      {row['ticket_id']} -> {result['severity']} / {result['category']}")
    out_df = pd.DataFrame(results)
    out_df.to_csv("tickets_processed.csv", index=False)
    print("      Saved -> tickets_processed.csv")
    return out_df


# ---------- STEP 3: BUILD DIGEST ----------
def generate_digest(df):
    print("[3/3] Building HTML digest...")
    summary = df.groupby("category").size().to_dict()
    critical = df[df["severity"] == "Critical"].to_dict("records")
    review_needed = df[df["needs_human_review"] == True].to_dict("records")

    template = Template("""
    <html><head><style>
        body { font-family: 'Segoe UI', sans-serif; background:#f4f6f8; padding:30px; color:#1a1a2e; }
        .card { background:white; border-radius:10px; padding:24px; margin-bottom:20px; box-shadow:0 2px 8px rgba(0,0,0,0.06); }
        h1 { color:#4f46e5; }
        .stat { display:inline-block; background:#eef2ff; padding:10px 16px; border-radius:8px; margin-right:10px; margin-bottom:8px; }
        .critical { border-left:4px solid #ef4444; padding-left:12px; margin-bottom:10px; }
        table { width:100%; border-collapse:collapse; }
        th, td { text-align:left; padding:8px; border-bottom:1px solid #eee; }
    </style></head><body>
        <h1>Daily Ticket Triage Digest</h1>
        <p>{{ date }} — {{ total }} tickets processed</p>
        <div class="card">
            <h3>Volume by Category</h3>
            {% for cat, count in summary.items() %}
                <span class="stat">{{ cat }}: {{ count }}</span>
            {% endfor %}
        </div>
        <div class="card">
            <h3>⚠️ Critical Tickets ({{ critical|length }})</h3>
            {% for t in critical %}
                <div class="critical"><b>{{ t.ticket_id }}</b>: {{ t.subject }}<br>
                <i>{{ t.root_cause_guess }}</i></div>
            {% else %}
                <p>None flagged as critical.</p>
            {% endfor %}
        </div>
        <div class="card">
            <h3>🔍 Needs Human Review ({{ review_needed|length }})</h3>
            <table><tr><th>ID</th><th>Category</th><th>Confidence</th></tr>
            {% for t in review_needed %}
                <tr><td>{{ t.ticket_id }}</td><td>{{ t.category }}</td><td>{{ "%.0f"|format(t.confidence*100) }}%</td></tr>
            {% endfor %}
            </table>
        </div>
    </body></html>
    """)
    html = template.render(date=datetime.date.today(), total=len(df), summary=summary,
                            critical=critical, review_needed=review_needed)
    with open("digest.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("      Saved -> digest.html")


# ---------- RUN EVERYTHING ----------
if __name__ == "__main__":
    print("=" * 50)
    print("AI TICKET TRIAGE PIPELINE — FULL DEMO")
    print("=" * 50)
    raw_df = generate_tickets()
    processed_df = run_triage(raw_df)
    generate_digest(processed_df)
    print("=" * 50)
    print("DONE. Open digest.html to view the report.")
    print("=" * 50)