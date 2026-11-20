# Verification

## Command to Run All Checks

```bash
python3 -m pytest tests/ -v
```

## Results (as of final commit `0e38d6b`)

```
platform darwin -- Python 3.11.9, pytest-9.1.1
collected 39 items

tests/test_app.py::test_app_initial_load                                        PASSED
tests/test_app.py::test_app_analysis_and_selection_persistence                  PASSED
tests/test_app.py::test_failed_run_clears_stale_session_state                   PASSED
tests/test_detection.py::test_deterministic_scoring                             PASSED
tests/test_detection.py::test_policy_threshold_trigger                          PASSED
tests/test_detection.py::test_outcome_labels_adhere_to_specification            PASSED
tests/test_detection.py::test_review_queue_ordering_by_anomaly_score            PASSED
tests/test_detection.py::test_factual_evidence_matches_inputs                   PASSED
tests/test_detection.py::test_version_constants_attached                        PASSED
tests/test_telemetry.py::test_telemetry_event_emission_and_fields               PASSED
tests/test_telemetry.py::test_telemetry_failure_events                          PASSED
tests/test_telemetry.py::test_telemetry_in_memory_buffer                        PASSED
tests/test_validation.py::test_valid_demo_dataset                               PASSED
tests/test_validation.py::test_empty_dataframe_rejected                         PASSED
tests/test_validation.py::test_missing_required_columns                         PASSED
tests/test_validation.py::test_duplicate_transaction_ids_rejected               PASSED
tests/test_validation.py::test_whitespace_padded_duplicate_transaction_ids_rejected PASSED
tests/test_validation.py::test_empty_or_whitespace_transaction_ids              PASSED
tests/test_validation.py::test_invalid_amounts_rejected[0.0]                    PASSED
tests/test_validation.py::test_invalid_amounts_rejected[-15.5]                  PASSED
tests/test_validation.py::test_invalid_amounts_rejected[nan]                    PASSED
tests/test_validation.py::test_invalid_amounts_rejected[inf]                    PASSED
tests/test_validation.py::test_invalid_amounts_rejected[-inf]                   PASSED
tests/test_validation.py::test_boolean_in_numeric_columns_rejected[True]        PASSED
tests/test_validation.py::test_boolean_in_numeric_columns_rejected[False]       PASSED
tests/test_validation.py::test_invalid_historical_average_rejected[0.0]         PASSED
tests/test_validation.py::test_invalid_historical_average_rejected[-10.0]       PASSED
tests/test_validation.py::test_invalid_historical_average_rejected[nan]         PASSED
tests/test_validation.py::test_invalid_historical_average_rejected[inf]         PASSED
tests/test_validation.py::test_invalid_historical_average_rejected[-inf]        PASSED
tests/test_validation.py::test_invalid_transaction_velocity_rejected[-1]        PASSED
tests/test_validation.py::test_invalid_transaction_velocity_rejected[2.5]       PASSED
tests/test_validation.py::test_invalid_transaction_velocity_rejected[nan]       PASSED
tests/test_validation.py::test_invalid_transaction_velocity_rejected[inf]       PASSED
tests/test_validation.py::test_invalid_boolean_device_rejected[maybe]           PASSED
tests/test_validation.py::test_invalid_boolean_device_rejected[42]              PASSED
tests/test_validation.py::test_invalid_boolean_device_rejected[unknown]         PASSED
tests/test_validation.py::test_invalid_boolean_device_rejected[nan]             PASSED
tests/test_validation.py::test_boolean_type_coercion                            PASSED

39 passed in 2.52s
```

## What Each Suite Verifies

| Suite | Tests | Covers |
|---|---|---|
| `test_validation.py` | 27 | Schema, uniqueness, whitespace IDs, type rejection (bool-as-numeric), NaN/inf, zero/negative amounts, non-integer velocity, non-boolean device flag |
| `test_detection.py` | 6 | Deterministic scoring, policy threshold trigger, outcome label spec, queue sort order, factual evidence fidelity, version constant attachment |
| `test_telemetry.py` | 3 | JSON schema, monotonic durations, payload privacy (no raw financial values in logs), failure events, in-memory buffer |
| `test_app.py` | 3 | Initial UI load, end-to-end analysis run + session state persistence (no duplicate scoring on selection), stale state cleared on failed run |

## Linting and Formatting

```bash
python3 -m ruff check .        # All checks passed
python3 -m ruff format --check . # 13 files already formatted
```

## Known Gaps

- No load or performance test. Batch size is bounded at 50 synthetic records.
- No mutation testing to verify test assertion strength.
- Streamlit AppTest cannot test browser rendering or visual layout.
- GitHub Actions CI is configured but requires public repo runner minutes; not verified against a live run on this repository.

## Local vs CI/CD Split

| Check | Local | PR Gate (CI) |
|---|---|---|
| `python3 -m pytest tests/ -v` | ✅ | ✅ (`.github/workflows/ci.yml`) |
| `ruff check` + `ruff format --check` | ✅ | Could be added as a CI step |
| Streamlit manual smoke test | ✅ | Not automated in CI |
| Docker build / container scan | ❌ Not applicable | Would be added for production pipeline |
