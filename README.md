# Fraud Triage Workbench

A lightweight, self-contained Python demonstration workbench for payment fraud triage. It combines an unsupervised **IsolationForest** anomaly baseline with deterministic business policy thresholds, factual input-derived evidence, and structured JSON telemetry.

---

## 1. Purpose & Demo Walkthrough

The workbench equips fraud analysts to inspect and triage payment transactions without external dependencies or cloud infrastructure:
1. **Load Bundled Data**: Preview pre-packaged synthetic payment transactions (`data/sample_transactions.csv`) generated deterministically.
2. **Execute Analysis**: Click **"Analyse transactions"** to run input validation, score deviations against a pinned reference model, and apply review policy rules.
3. **Ranked Review Queue**: Prioritise suspicious transactions in a ranked review table ordered by anomaly score ascending (most anomalous first).
4. **Factual Evidence & Detail Inspector**: Select any transaction to inspect exact input values, model findings, triggered policy rules, and factual supporting statements.
5. **Lightweight Telemetry**: Expand the live telemetry panel to inspect structured JSON execution logs tagged with a correlation ID, event names, and monotonic durations.

---

## 2. Text Architecture Diagram

```
+-----------------------------------------------------------------------+
|                             Streamlit UI                              |
|   (app.py - Banner, Preview, Queue Table, Detail Panel, Telemetry)    |
+-----------------------------------------------------------------------+
           |                                             |
           v                                             v
+-----------------------+                    +--------------------------+
|  Validation Engine    |                    |   Telemetry Collector    |
| (fraud/validation.py) |                    |   (fraud/telemetry.py)   |
| Fail-fast schema &    |                    | Correlation ID, monotonic|
| boundary checks       |                    | ms timer, stdout JSON    |
+-----------------------+                    +--------------------------+
           |
           v
+-----------------------------------------------------------------------+
|                      Detection & Policy Engine                        |
|                        (fraud/detection.py)                           |
|                                                                       |
|  1. Feature Derivation: amount_ratio = amount / historical_avg        |
|  2. Baseline Model: IsolationForest fitted on reference data          |
|     (decision_function score: lower = more anomalous)                 |
|  3. Policy Rule: Flag if Model Outlier OR amount_ratio >= 5.0x        |
|  4. Factual Evidence: Deterministic statements from input values      |
|  5. Version Tags: MODEL_VERSION & POLICY_VERSION                      |
+-----------------------------------------------------------------------+
           ^                                             ^
           |                                             |
+-----------------------+                    +--------------------------+
| Reference Baseline    |                    | Demo Batch Transactions  |
|  (fraud/data.py)      |                    | (data/sample_transactions.csv)|
| 1,000 synthetic items |                    | 50 synthetic test items  |
| seed=42 (Cached once) |                    | seed=1337                |
+-----------------------+                    +--------------------------+
```

---

## 3. Local Setup, Run, and Test Commands

### Prerequisites
- Python 3.11 or higher.

### Environment Setup

#### On macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### On Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Run the Application
```bash
python3 -m streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### Run the Automated Tests
```bash
python3 -m pytest tests/ -v
```

> **Note:** If `streamlit` or `pytest` are not on your shell `PATH`, always prefix with `python3 -m`.

### Reproduce Synthetic Demonstration Dataset
```bash
python3 -m fraud.data
```

---

## 4. Feature Definitions, Score Direction, and Policy

| Feature | Type | Definition & Role |
|---|---|---|
| `transaction_id` | `str` | Synthetic identifier (e.g. `TXN-0001`). Never used as a model feature. |
| `amount` | `float` | Transaction monetary value in standard currency units (> 0.00). |
| `historical_average_amount` | `float` | Customer's historical mean payment amount (> 0.00). |
| `amount_ratio` | `float` | Derived feature: `amount / historical_average_amount`. |
| `transactions_last_10m` | `int` | Transaction velocity count in preceding 10 minutes (>= 0). |
| `is_new_device` | `bool` | Flag indicating whether the transaction device is newly observed. |

### Score Direction
- **IsolationForest `decision_function`**: Outputs a continuous score where **lower means more unusual / anomalous**. Negative values reflect deviations beyond the contamination threshold of the baseline.
- **Review Queue Sorting**: Ascending by `anomaly_score` so analysts triage the most anomalous transactions first.

### Review Policy
- A transaction is flagged for **"Review"** if:
  1. The unsupervised IsolationForest predicts an outlier (`predict == -1`), **OR**
  2. `amount_ratio >= 5.0` (an explicit, illustrative business policy threshold).
- Transactions not meeting either condition receive the outcome **"Not flagged"**.
- System outcomes strictly use `"Review"` and `"Not flagged"`; terms like `"Fraud confirmed"` or `"Safe"` are deliberately avoided.

### Engine Versioning
- `MODEL_VERSION`: `isoforest-v1.0`
- `POLICY_VERSION`: `policy-rule-or-model-v1.0`

---

## 5. Architectural Decisions: ML + Deterministic Rules vs LLM

1. **Deterministic Reproducibility & Auditability**:
   - Financial fraud triage requires strict repeatability. An IsolationForest trained on a fixed reference set with explicit random seeds and deterministic rules guarantees that identical inputs always yield identical decisions and factual evidence.
2. **Sub-millisecond Latency & Zero External Cost**:
   - Processing transactions using scikit-learn and vectorized pandas executes in single-digit milliseconds per batch with zero network latency, no external API costs, and zero rate-limit risks.
3. **No Hallucination Risk in Factual Evidence**:
   - Explanations shown to analysts are directly formatted from factual input properties (e.g., `"Amount is 8.2 times the historical average"`). LLMs can invent speculative behavioral narratives; deterministic templates guarantee that evidence statements are 100% faithful to the input record.
4. **Offline Air-Gapped Operation**:
   - Meets the strict constraint of zero runtime network calls, zero credentials, and fully local execution.

---

## 6. Observability Design & Logging Boundaries

- **Lightweight Application Telemetry**: Designed for process-level transparency, not distributed tracing.
- **Correlation ID**: A UUID4 string is generated at the start of each analysis execution, tying all related log lines together.
- **Monotonic Clocks**: Elapsed durations are calculated using `time.perf_counter()`, ensuring non-negative millisecond measurements unaffected by system clock adjustments.
- **Standardized Events**:
  - `run_started`: Run initiation and total batch record count.
  - `validation_completed` / `validation_failed`: Schema and boundary check results.
  - `transaction_scored`: Emitted per transaction with `transaction_id`, `model_version`, `policy_version`, `outcome`, `anomaly_score`, and `policy_triggered`.
  - `run_completed`: Batch totals, review counts, review rate, and total duration.
  - `run_failed`: Exception summary if an unexpected failure occurs.
- **Strict Privacy / Data Boundary**:
  - Log payloads **never** emit raw financial inputs, customer profiles, or full transaction payloads. Only synthetic IDs, scores, and categorical outcomes are logged.
- **Streamlit Re-render Safety**:
  - Analysis results and telemetry buffers are stored in `st.session_state`. Selecting or inspecting a transaction updates UI state without rerunning the scoring pipeline or emitting duplicate log events.

---

## 7. Tests and Verification Performed

35 automated tests are implemented and passing across four suites:
- `tests/test_validation.py` (24 tests):
  - Valid datasets and type coercion.
  - Rejection of empty datasets and missing columns.
  - Duplicate or whitespace-only transaction IDs.
  - Invalid, negative, zero, NaN, and infinite amounts or historical averages.
  - Non-integer or negative velocity counts.
  - Non-boolean device flags.
- `tests/test_telemetry.py` (3 tests):
  - Structured JSON schema validation and stdout emission.
  - Monotonic non-negative durations.
  - Absence of full payload data in log events.
  - Failure event formats and in-memory buffer accuracy.
- `tests/test_detection.py` (6 tests):
  - Deterministic repeatable scoring.
  - Extreme amount multiplier policy rule trigger (`amount_ratio >= 5.0`).
  - Adherence to specified outcome labels (`Review`, `Not flagged`).
  - Queue ordering by anomaly score ascending.
  - Factual evidence string fidelity.
  - Model and policy version tagging.
- `tests/test_app.py` (2 tests via Streamlit `AppTest`):
  - Initial UI load without exceptions.
  - End-to-end analysis triggering, queue display, and session state persistence ensuring transaction selection does not rerun analysis or duplicate logs.

---

## 8. Limitations & Boundary Scope

- **Synthetic Data**: Uses synthetic random distributions; does not model complex real-world fraud schemes, seasonal trends, or merchant category codes.
- **Uncalibrated Anomaly Scores**: `decision_function` scores measure average path depth across isolation trees, **not** calibrated probabilities of fraud.
- **Supplied Synthetic Features**: Features like historical average and 10-minute velocity are ingested as pre-aggregated synthetic inputs; no distributed stream-processing or feature-store aggregation is included.
- **Human Triage Required**: Flagging an item as `"Review"` is a triage signal for human review, not an autonomous blocking or confirmation action.

---

## 9. Production Next Steps (Outside Current Scope)

1. **Feature Store Integration**: Implement real-time streaming feature aggregations (e.g. Redis / Feast) for sliding-window velocity and rolling customer expenditure averages.
2. **Supervised Feedback Loop**: Incorporate confirmed analyst labels to train supervised or semi-supervised gradient-boosted trees (e.g. LightGBM) alongside unsupervised detectors.
3. **Calibrated Probability Calibration**: Calibrate model outputs using Platt scaling or isotonic regression to output actual risk probabilities.
4. **Production Observability**: Export OpenTelemetry metrics and traces to an enterprise collector (e.g. Prometheus / Jaeger / Datadog).
5. **Role-Based Access Control (RBAC)**: Secure analyst access with SSO, audit trails, and multi-tenant isolation.

