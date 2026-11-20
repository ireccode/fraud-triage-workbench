# AI Usage Record

This record documents the AI tools, prompts, generated artifacts, verifications, and decisions involved in the development of the **Fraud Triage Workbench**.

---

## 1. Tool & Assistant Identification
- **AI Tool**: Antigravity Agent (Google Gemini 3.8 Flash)
- **Role**: Pragmatic Senior Python Engineer
- **Environment**: macOS, Python 3.11.9, Streamlit 1.50.0, scikit-learn 1.6.1, pandas 2.2.3, pytest 9.1.1

---

## 2. Work Generated and Assisted
1. **Implementation Plan & Checklist**:
   - Structured plan in `docs/plans/2026-11-20-fraud-triage-workbench.md` and live task tracker in `docs/plans/task.md`.
2. **Synthetic Data Module (`fraud/data.py`)**:
   - Deterministic generators for reference data (seed=42) and demo data (seed=1337).
   - Bundled CSV generation (`data/sample_transactions.csv`).
3. **Validation Module (`fraud/validation.py`)**:
   - Strict validation checks for schema, uniqueness, non-empty IDs, positive numbers, non-negative integer velocity, and boolean normalization.
4. **Telemetry Module (`fraud/telemetry.py`)**:
   - Lightweight structured JSON stdout emitter with correlation IDs, monotonic timing (`time.perf_counter()`), and in-memory run buffer.
5. **Detection & Policy Engine (`fraud/detection.py`)**:
   - Cached IsolationForest model fitting on reference data, feature matrix construction, illustrative policy threshold (`amount_ratio >= 5.0`), deterministic factual evidence generator, and version constants.
6. **Streamlit Application (`app.py`)**:
   - Single-page UI with synthetic disclaimer, sample preview, run summary metrics, ranked review queue, detail inspector, and expandable telemetry viewer.
   - Streamlit session state caching to prevent rerender duplicate analysis.
7. **Automated Test Suite (`tests/`)**:
   - 35 tests covering validation, telemetry, detection, and Streamlit AppTest smoke tests.
8. **CI Workflow & Documentation**:
   - `.github/workflows/ci.yml`, `requirements.txt`, `.gitignore`, `README.md`, and `AI_USAGE.md`.

---

## 3. Human Decisions Still Requiring Review
- [ ] Review of illustrative policy threshold: Confirm whether `amount_ratio >= 5.0` aligns with interview panel expectations or whether a different heuristic should be discussed.
- [ ] IsolationForest parameters: Confirm whether `contamination=0.05` and `n_estimators=100` are optimal for candidate presentation.
- [ ] Presentation styling: Confirm whether default Streamlit components meet the reviewer's visual expectations.

---

## 4. Actual Corrections and Verification Performed
- **CLI Pytest Invocation**: Initially attempted running bare `pytest`, which was not in default PATH (`zsh: command not found: pytest`). Corrected to `python3 -m pytest`, which cleanly located the installed environment.
- **Streamlit AppTest Verification**: Ensured `streamlit.testing.v1.AppTest` was imported and executed against `app.py`. Verified that button click, run completion, and transaction selection work without raising unhandled exceptions or triggering second analysis runs.
- **Privacy Boundary Check**: Verified in `test_telemetry.py` that input payloads (amounts, averages) are omitted from `transaction_scored` telemetry events.
- **Non-git Environment Disclosure**: Checked `git status` and identified that the workspace root is not a Git repository (Obsidian vault root). Preserved unrelated project directories (`kao-*`, `mem-*`) without altering repository state.

---

## 5. Commands Executed & Results
| Command | Result |
|---|---|
| `python3 --version` | Python 3.11.9 |
| `python3 -m pip list` | Verified `streamlit 1.50.0`, `pandas 2.2.3`, `scikit-learn 1.6.1`, `pytest 9.1.1` |
| `python3 -m fraud.data` | Generated `data/sample_transactions.csv` (51 lines, 50 records) |
| `python3 -m pytest tests/test_validation.py -v` | 24 passed |
| `python3 -m pytest tests/test_telemetry.py -v` | 3 passed |
| `python3 -m pytest tests/test_detection.py -v` | 6 passed |
| `python3 -m pytest tests/test_app.py -v` | 2 passed |
| `python3 -m pytest tests/ -v` | 35 passed in 1.95s |

---

## 6. Time Spent Tracking
- **Elapsed Engineering & Implementation Time**: `[Candidate to complete / verify: ~45 minutes of agent generation, testing, and refinement]`

