import pandas as pd
import json, os, datetime
from anthropic import Anthropic
from jinja2 import Template

client = Anthropic()  # reads ANTHROPIC_API_KEY from env
MODEL = "claude-sonnet-4-5"

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

def classify_ticket(row):
    prompt = CLASSIFY_PROMPT.format(subject=row["subject"], body=row["body"], tier=row["customer_tier"])
    resp = client.messages.create(
        model=MODEL,
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}]
    )
    text = resp.content[0].text.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"severity": "Unknown", "category": "Other", "root_cause_guess": "parse_error",
                "suggested_response": "", "confidence": 0.0, "needs_human_review": True}

def run_pipeline(input_csv="tickets_raw.csv", output_csv="tickets_processed.csv", limit=50):
    df = pd.read_csv(input_csv).head(limit)  # limit keeps API cost low for demo
    results = []
    for _, row in df.iterrows():
        result = classify_ticket(row)
        results.append({**row.to_dict(), **result})
        print(f"Processed {row['ticket_id']} -> {result['severity']} / {result['category']}")

    out_df = pd.DataFrame(results)
    out_df.to_csv(output_csv, index=False)
    generate_digest(out_df)
    return out_df

def generate_digest(df):
    summary = df.groupby("category").size().to_dict()
    critical = df[df["severity"] == "Critical"].to_dict("records")
    review_needed = df[df["needs_human_review"] == True].to_dict("records")

    template = Template("""
    <html><head><style>
        body { font-family: 'Segoe UI', sans-serif; background:#f4f6f8; padding:30px; color:#1a1a2e; }
        .card { background:white; border-radius:10px; padding:24px; margin-bottom:20px; box-shadow:0 2px 8px rgba(0,0,0,0.06); }
        h1 { color:#4f46e5; }
        .stat { display:inline-block; background:#eef2ff; padding:10px 16px; border-radius:8px; margin-right:10px; }
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
    print("Digest saved -> digest.html")

if __name__ == "__main__":
    run_pipeline()