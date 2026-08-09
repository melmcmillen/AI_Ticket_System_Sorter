import pandas as pd
from faker import Faker
import random

fake = Faker()
categories = ["Login Issue", "Billing Error", "Feature Request", "Performance Bug", "Data Sync Failure", "UI Glitch"]
severities_hint = ["minor annoyance", "blocking work", "system down", "cosmetic issue"]

def generate_tickets(n=300):
    rows = []
    for i in range(n):
        cat = random.choice(categories)
        rows.append({
            "ticket_id": f"TCK-{1000+i}",
            "subject": f"{cat}: {fake.sentence(nb_words=6)}",
            "body": fake.paragraph(nb_sentences=4) + f" This started after {fake.word()} update.",
            "customer_tier": random.choice(["Free", "Pro", "Enterprise"]),
            "created_at": fake.date_time_between(start_date="-14d", end_date="now")
        })
    return pd.DataFrame(rows)

if __name__ == "__main__":
    df = generate_tickets(300)
    df.to_csv("tickets_raw.csv", index=False)
    print(f"Generated {len(df)} synthetic tickets -> tickets_raw.csv")