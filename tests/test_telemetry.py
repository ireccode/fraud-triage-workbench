"""Unit tests for the telemetry module."""

import json
from io import StringIO

from fraud.telemetry import TelemetryCollector


def test_telemetry_event_emission_and_fields(monkeypatch):
    """Verify structured JSON events emit to stdout with all required fields."""
    fake_stdout = StringIO()
    monkeypatch.setattr("sys.stdout", fake_stdout)

    collector = TelemetryCollector(correlation_id="test-corr-1234")
    collector.log_run_started(total_records=10)
    collector.log_validation_completed(valid_count=10)
    collector.log_transaction_scored(
        transaction_id="TXN-0001",
        model_version="isoforest-v1.0",
        policy_version="rule-or-model-v1.0",
        outcome="Review",
        anomaly_score=-0.1425,
        policy_triggered=True,
    )
    collector.log_run_completed(total_analysed=10, review_count=1, review_rate=0.1)

    output = fake_stdout.getvalue().strip().split("\n")
    assert len(output) == 4

    events = [json.loads(line) for line in output]
    for ev in events:
        assert ev["correlation_id"] == "test-corr-1234"
        assert "timestamp" in ev
        assert "event" in ev
        assert "duration_ms" in ev
        assert isinstance(ev["duration_ms"], (int, float))
        assert ev["duration_ms"] >= 0.0

    assert events[0]["event"] == "run_started"
    assert events[0]["total_records"] == 10

    assert events[1]["event"] == "validation_completed"
    assert events[1]["valid_count"] == 10

    assert events[2]["event"] == "transaction_scored"
    assert events[2]["transaction_id"] == "TXN-0001"
    assert events[2]["model_version"] == "isoforest-v1.0"
    assert events[2]["policy_version"] == "rule-or-model-v1.0"
    assert events[2]["outcome"] == "Review"
    assert events[2]["anomaly_score"] == -0.1425
    # Full input record fields must not be present
    assert "amount" not in events[2]
    assert "historical_average_amount" not in events[2]

    assert events[3]["event"] == "run_completed"
    assert events[3]["total_analysed"] == 10
    assert events[3]["review_count"] == 1
    assert events[3]["review_rate"] == 0.1


def test_telemetry_failure_events(monkeypatch):
    """Verify validation_failed and run_failed events emit properly."""
    fake_stdout = StringIO()
    monkeypatch.setattr("sys.stdout", fake_stdout)

    collector = TelemetryCollector(correlation_id="err-corr-5678")
    collector.log_validation_failed("Missing column 'amount'")
    collector.log_run_failed("Unexpected IO error")

    lines = fake_stdout.getvalue().strip().split("\n")
    assert len(lines) == 2

    ev1 = json.loads(lines[0])
    assert ev1["event"] == "validation_failed"
    assert ev1["error"] == "Missing column 'amount'"

    ev2 = json.loads(lines[1])
    assert ev2["event"] == "run_failed"
    assert ev2["error"] == "Unexpected IO error"


def test_telemetry_in_memory_buffer():
    """Verify in-memory buffer returns exact events and valid JSON."""
    collector = TelemetryCollector()
    collector.log_run_started(total_records=5)
    collector.log_run_completed(total_analysed=5, review_count=0, review_rate=0.0)

    buffered = collector.get_events()
    assert len(buffered) == 2
    assert buffered[0]["event"] == "run_started"

    json_str = collector.to_json()
    parsed = json.loads(json_str)
    assert len(parsed) == 2
