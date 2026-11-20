# Fraud Triage Workbench Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Implement a small, self-contained, observable fraud-triage Streamlit workbench with deterministic synthetic data, strict validation, IsolationForest anomaly detection, explicit review policy rules, explainable factual evidence, and structured telemetry.

**Architecture:** Pure Python modular architecture with clear separation of concerns: `fraud.data` (deterministic reference & demo generation), `fraud.validation` (fail-fast input checks), `fraud.detection` (IsolationForest training on reference data + policy evaluation + factual evidence generation), `fraud.telemetry` (lightweight JSON application telemetry with correlation IDs and monotonic timing), and `app.py` (reactive single-process Streamlit UI with cached reference model and session state persistence).

**Tech Stack:** Python 3.11+, Streamlit 1.50.0, pandas 2.2.3, scikit-learn 1.6.1, pytest 9.1.1.

---

### Task 59: Project Scaffold, Dependencies & Deterministic Synthetic Data
**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `fraud/__init__.py`
- Create: `fraud/data.py`
- Create: `data/sample_transactions.csv`

**Description:**
Define direct pinned dependencies. Implement deterministic reference data generation and demo transaction generation using fixed random seed (42). Generate `data/sample_transactions.csv` containing ordinary transactions and distinct unusual transactions.

---

### Task 60: Validation Module and Unit Tests
**Files:**
- Create: `fraud/validation.py`
- Create: `tests/test_validation.py`

**Description:**
Implement validation logic rejecting missing columns, non-unique IDs, NaN/inf values, non-positive amounts, negative transaction counts, and non-boolean device flags. Write thorough pytest tests covering all valid and invalid edge cases.

---

### Task 61: Telemetry Module and Unit Tests
**Files:**
- Create: `fraud/telemetry.py`
- Create: `tests/test_telemetry.py`

**Description:**
Implement lightweight structured JSON logging to stdout with in-memory run buffer for the UI. Ensure correlation IDs, monotonic timing (`perf_counter`), explicit event names (`run_started`, `validation_completed`, `validation_failed`, `transaction_scored`, `run_completed`, `run_failed`), and no logging of full input payloads. Test event schemas, durations, and UI rerender safety.

---

### Task 62: Detection, Policy & Factual Evidence Engine and Unit Tests
**Files:**
- Create: `fraud/detection.py`
- Create: `tests/test_detection.py`

**Description:**
Fit IsolationForest once on the reference dataset (`n_estimators=100`, `contamination=0.05`, `random_state=42`). Derive `amount_ratio`. Evaluate policy: model finding is outlier OR `amount_ratio >= 5.0`. Generate deterministic factual evidence strings. Rank queue by anomaly score ascending (`decision_function`). Test determinism, policy triggers, ordering, and evidence correctness.

---

### Task 63: Streamlit Application & E2E Smoke Tests
**Files:**
- Create: `app.py`
- Create: `tests/test_app.py`

**Description:**
Build single-page Streamlit UI: banner & synthetic disclaimer, sample preview, "Analyse transactions" button, run summary metrics, ranked review table, transaction detail panel with input values/findings/evidence/versions, and expandable telemetry log view. Persist analysis results in `st.session_state` so selecting transactions does not trigger reruns. Add `AppTest` smoke test verifying load, analysis, and selection stability.

---

### Task 64: GitHub Actions CI Workflow, README & AI Usage Records
**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `README.md`
- Create: `AI_USAGE.md`

**Description:**
Configure GitHub Actions CI on Python 3.11. Write comprehensive README with text architecture diagram, setup commands, design decisions, and limitations. Document honest AI usage in `AI_USAGE.md`.

---

### Task 65: End-to-End Verification and Session Handoff
**Files:**
- Modify: `docs/plans/task.md`
- Modify: `mem-vault-kao-legal/LOG-DECISIONS.md`
- Modify: `mem-vault-kao-legal/SESSION-HANDOFF-LAST.md`

**Description:**
Run full test suite via pytest, verify Streamlit headless execution, check all files, and update tracking records.

