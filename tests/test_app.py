"""End-to-end smoke test for the Streamlit Fraud Triage application."""

from streamlit.testing.v1 import AppTest


def test_app_initial_load():
    """Verify that the Streamlit app loads in initial state without exceptions."""
    at = AppTest.from_file("app.py", default_timeout=15)
    at.run()

    assert not at.exception
    # Title and ready message present
    assert len(at.title) >= 1
    assert "Fraud Triage Workbench" in at.title[0].value
    assert len(at.button) >= 1
    assert at.button[0].label == "Analyse transactions"


def test_app_analysis_and_selection_persistence():
    """Verify end-to-end analysis run, queue population, and selection without re-run."""
    at = AppTest.from_file("app.py", default_timeout=15)
    at.run()

    # Click 'Analyse transactions'
    at.button[0].click().run()

    assert not at.exception
    assert "latest_run" in at.session_state

    run_state = at.session_state["latest_run"]
    first_correlation_id = run_state["correlation_id"]
    first_events_count = run_state["events_count"]

    assert run_state["total_analysed"] > 0
    assert run_state["review_count"] > 0
    assert run_state["review_rate"] > 0.0

    # Ensure transaction selector exists
    assert len(at.selectbox) >= 1
    selector = at.selectbox[0]

    # Select an alternate transaction ID from options
    options = selector.options
    assert len(options) > 1
    second_option = options[1]

    # Select another transaction and rerun UI cycle
    selector.select(second_option).run()

    assert not at.exception
    # Session state must persist: correlation_id and events_count must remain identical!
    # No second analysis run or duplicate telemetry emitted
    persisted_run = at.session_state["latest_run"]
    assert persisted_run["correlation_id"] == first_correlation_id
    assert persisted_run["events_count"] == first_events_count
    assert persisted_run["selected_txn_id"] == second_option


def test_failed_run_clears_stale_session_state(monkeypatch):
    """Verify that triggering analysis clears stale session state on failure."""
    from fraud.validation import ValidationError

    def mock_evaluate(*args, **kwargs):
        raise ValidationError(["Forced validation failure for testing"])

    monkeypatch.setattr("fraud.detection.evaluate_batch", mock_evaluate)

    at = AppTest.from_file("app.py", default_timeout=15)
    at.run()

    # Pre-populate session state as if a previous run succeeded
    at.session_state["latest_run"] = {"stale_key": "stale_value"}

    at.button[0].click().run()

    # Must clear stale session state and display the error
    assert "latest_run" not in at.session_state
    assert len(at.error) >= 1
    assert "Forced validation failure for testing" in at.error[0].value




