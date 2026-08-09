requirements: 
pandas>=2.3.3
anthropic>=0.40
faker>=30.0
jinja2>=3.1
python-dotenv>=1.0



## How to run it

### 1. Install Python 3.14
Download from [python.org](https://www.python.org). Use the standard installer (not the free-threaded/"3.14t" build). Confirm install:
```bash
python --version
```

### 2. Clone the repo
```bash
git clone https://github.com/your-username/ticket-triage.git
cd ticket-triage
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Get an Anthropic API key
Sign up at [console.anthropic.com](https://console.anthropic.com), create an API key, and add a small amount of credit under **Plans & Billing** (a few dollars easily covers running this project many times over).

### 5. Set up your API key
Create a file named `.env` in the project root:

This file is already excluded from version control via `.gitignore` — never commit your real key.

### 6. Run the full pipeline
```bash
python run_demo.py
```
This generates synthetic tickets, runs them through Claude for triage, and builds `digest.html`.

### 7. View the results
```bash
start .\digest.html
```
(Mac/Linux: `open digest.html`)

### 8. Automate it (optional)
```powershell
schtasks /create /tn "TicketTriage" /tr "powershell -File C:\path\to\run_pipeline.ps1" /sc daily /st 08:00
```

## Configuration

Adjust these variables at the top of `run_demo.py`:
```python
NUM_TICKETS = 300       # total synthetic tickets generated
NUM_TO_PROCESS = 25      # how many get sent to the AI
MODEL = "claude-sonnet-4-5"
```

## Sample output

The digest includes:
- Ticket volume by category
- Critical tickets flagged for immediate attention
- A review queue for anything the model wasn't confident about

## Notes

- Ticket data is synthetically generated with Faker for demo purposes — swap in real data by replacing `tickets_raw.csv`.
- `NUM_TO_PROCESS` is capped at 25 by default to keep API costs low during testing.

