# Operate

## How to Run the Solution

### Prerequisites
- Python 3.11 or higher
- No credentials, paid APIs, or external services required

### Setup

```bash
# Clone the repository
git clone https://github.com/ireccode/fraud-triage-workbench.git
cd fraud-triage-workbench

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\Activate.ps1    # Windows PowerShell

# Install dependencies
pip install -r requirements.txt
```

### Run the Application

```bash
python3 -m streamlit run app.py
```

Open `http://localhost:8501` in a browser. Click **"Analyse transactions"** to run the full workflow.

### Run Tests

```bash
python3 -m pytest tests/ -v
```

### Regenerate the Sample Dataset

```bash
python3 -m fraud.data
# writes data/sample_transactions.csv (50 records, seed=1337)
```

## Logs and Status

The application emits structured JSON to stdout during each analysis run. Each line is a valid JSON object:

```json
{"timestamp": "2026-11-20T08:50:33Z", "correlation_id": "47ed1401-...", "event": "run_started", "total_records": 50}
{"timestamp": "2026-11-20T08:50:33Z", "correlation_id": "47ed1401-...", "event": "validation_completed", "valid_count": 50}
{"timestamp": "2026-11-20T08:50:33Z", "correlation_id": "47ed1401-...", "event": "transaction_scored", "transaction_id": "TXN-0001", "outcome": "Not flagged", "anomaly_score": 0.082, "policy_triggered": false}
{"timestamp": "2026-11-20T08:50:33Z", "correlation_id": "47ed1401-...", "event": "run_completed", "total_analysed": 50, "review_count": 10, "review_rate": 0.2}
```

**Privacy boundary:** Log events never include raw financial amounts, historical averages, or complete transaction payloads. Only synthetic IDs, scores, outcome labels, and durations appear in logs.

The Streamlit UI also displays the full telemetry buffer in an expandable panel after each run.

## Configuration and Secrets

There is no configuration file or secret management. All parameters are hardcoded constants in source:

| Parameter | Location | Value |
|---|---|---|
| Reference data seed | `fraud/data.py` | `DEFAULT_REFERENCE_SEED = 42` |
| Demo data seed | `fraud/data.py` / `app.py` | `seed=1337` |
| IsolationForest contamination | `fraud/detection.py` | `0.05` |
| IsolationForest n_estimators | `fraud/detection.py` | `100` |
| Policy amount ratio threshold | `fraud/detection.py` | `POLICY_AMOUNT_RATIO_THRESHOLD = 5.0` |
| Model version tag | `fraud/detection.py` | `MODEL_VERSION = "isoforest-v1.0"` |
| Policy version tag | `fraud/detection.py` | `POLICY_VERSION = "policy-rule-or-model-v1.0"` |

## Known Failure Modes

| Failure Mode | Behaviour | Guarded? |
|---|---|---|
| CSV has wrong or missing columns | `ValidationError` raised; UI shows actionable error message per column | ✅ Yes |
| Duplicate or whitespace-padded transaction IDs | Caught by ID normalisation + duplicate check | ✅ Yes |
| Boolean values in numeric columns | Explicit bool type check rejects before `pd.to_numeric` coercion | ✅ Yes |
| NaN, Inf, or zero in amount fields | Rejected with descriptive error message | ✅ Yes |
| Non-integer or negative velocity | Rejected with descriptive error message | ✅ Yes |
| Non-boolean device flag | Rejected; valid representations listed | ✅ Yes |
| Empty input file | Caught; "empty input" error displayed | ✅ Yes |
| Unexpected exception during analysis | Caught by `except Exception` guard; displayed in UI without crash | ✅ Yes |
| Analysis triggered again after prior success | Previous session state cleared before new run begins | ✅ Yes |

## Rollback and Degrade

- The model is fitted from scratch on the fixed reference dataset each time the app starts (cached by `@st.cache_resource`). There is no model artefact to roll back.
- If the bundled CSV is missing, the app falls back to generating demo data deterministically (`fraud/data.py`) without error.
- The app degrades gracefully: a failed validation shows an error panel but the application remains interactive.

## Local-to-Cloud Considerations

| Concern | Local (current) | Cloud (production) |
|---|---|---|
| Model serving | In-process, cached by Streamlit | Separate model server (FastAPI + container) |
| Data ingestion | Static CSV | Streaming via feature store (Feast / Redis) |
| Logs | stdout JSON | OpenTelemetry → Datadog / Grafana |
| Secrets | None | Vault / AWS Secrets Manager |
| CI/CD | GitHub Actions test-only | Add Docker build, image scan, canary deploy |
| Auth | None | SSO + RBAC |
