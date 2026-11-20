# Agentic Workflow

## AI Tool Used

**Antigravity** (Google Gemini-powered coding agent), running in an IDE-integrated agentic mode with file read/write, shell execution, and web search tools.

## How the Work Was Decomposed

The build was broken into discrete, ordered vertical slices — each committed independently before moving to the next:

| Step | Deliverable | Commit |
|---|---|---|
| 1 | Project scaffold, `requirements.txt`, `.gitignore` | `e3a32fa` |
| 2 | Synthetic data module (`fraud/data.py`) + tests | `f0f08f5` |
| 3 | Validation module (`fraud/validation.py`) + 24 tests | `1816207` |
| 4 | Telemetry module (`fraud/telemetry.py`) + 3 tests | `e502bda` |
| 5 | Detection + policy engine (`fraud/detection.py`) + 6 tests | `8f47757` |
| 6 | Streamlit UI (`app.py`) + 2 AppTest smoke tests | `75d04c4` |
| 7 | GitHub Actions CI workflow | `fd13c4f` |
| 8 | Documentation (README, AI_USAGE.md, runbook) | `cdcd4f9` |
| 9–13 | Bug fixes from independent code review (findings 1–5) | `4a06e59`–`2f2f6f1` |
| 14 | Ruff lint and format pass | `0e38d6b` |

## Representative Steering Instructions

The agent was given structured natural-language briefs for each slice, for example:

> *"Implement `fraud/validation.py`. Validate required columns, unique non-empty transaction IDs, numeric types, and boolean values. Reject missing or non-finite numeric values. Require amount and historical_average_amount > 0. Require transactions_last_10m to be a non-negative integer. Raise a ValidationError with actionable messages. Write pytest tests for every rule."*

> *"Implement `fraud/detection.py`. Derive amount_ratio = amount / historical_average_amount. Use IsolationForest fitted once on the fixed reference dataset with contamination=0.05, n_estimators=100, random_state=42. Apply policy: flag if model == -1 OR amount_ratio >= 5.0. Never include scenario labels as model features. Attach MODEL_VERSION and POLICY_VERSION constants to every result row."*

> *"Run an independent submission-readiness review of this repository acting as a senior engineer reviewing a technical interview submission for a banking / AI engineering role. Find issues an employer could reasonably discover when cloning, running, testing, and inspecting the repository."*

## Where I Intervened

1. **Review gate between modules**: After each module the agent ran the test suite and I confirmed pass/fail before the next slice began.
2. **Code review prompt**: After the initial build I explicitly asked the agent to act as an independent senior reviewer and find defects — not just confirm passing tests. This surfaced five real bugs (whitespace duplicate IDs, boolean coercion, stale session state, README inaccuracies).
3. **Ruff linting pass**: I added a ruff check/fix/format step after the review fixes to enforce consistent Python style.
4. **History management**: I instructed the agent to remove an accidental planning-document commit that had leaked into the tracked history before pushing to GitHub.

## How I Reviewed Generated Output

- Ran `python3 -m pytest tests/ -v` after each module commit and verified pass counts before proceeding.
- Read all generated source files to check business logic matched the requirements (policy threshold, score direction, evidence string formatting).
- Confirmed telemetry events omit raw financial values by reading `test_telemetry.py` assertions.
- Ran `python3 -m ruff check .` and `python3 -m ruff format --check .` as a final quality gate.
- Verified the Streamlit app loaded and produced a ranked queue by reviewing AppTest output and session state assertions.
