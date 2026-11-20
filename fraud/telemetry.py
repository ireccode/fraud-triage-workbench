"""Lightweight application telemetry and structured JSON event logging.

Emits structured JSON events to standard output and records them in an
in-memory run buffer for display within the Streamlit UI.
Does not log raw input payloads and relies on a monotonic clock.
"""

import json
import sys
import time
import uuid
from datetime import UTC, datetime
from typing import Any


class TelemetryCollector:
    """Collects and outputs structured events for a single analysis execution."""

    def __init__(self, correlation_id: str | None = None):
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self._start_perf = time.perf_counter()
        self._events: list[dict[str, Any]] = []

    @property
    def elapsed_ms(self) -> float:
        """Calculate elapsed monotonic time in milliseconds since run start."""
        elapsed = (time.perf_counter() - self._start_perf) * 1000.0
        return max(0.0, round(elapsed, 2))

    def emit_event(self, event: str, **kwargs: Any) -> dict[str, Any]:
        """Format, log to stdout, and buffer a structured event."""
        event_dict: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "correlation_id": self.correlation_id,
            "event": event,
            "duration_ms": self.elapsed_ms,
        }
        event_dict.update(kwargs)

        # Output to stdout as single-line JSON
        serialized = json.dumps(event_dict, ensure_ascii=False)
        sys.stdout.write(serialized + "\n")
        sys.stdout.flush()

        self._events.append(event_dict)
        return event_dict

    def log_run_started(self, total_records: int) -> dict[str, Any]:
        return self.emit_event("run_started", total_records=total_records)

    def log_validation_completed(self, valid_count: int) -> dict[str, Any]:
        return self.emit_event("validation_completed", valid_count=valid_count)

    def log_validation_failed(self, error_summary: str) -> dict[str, Any]:
        return self.emit_event("validation_failed", error=error_summary)

    def log_transaction_scored(
        self,
        transaction_id: str,
        model_version: str,
        policy_version: str,
        outcome: str,
        anomaly_score: float,
        policy_triggered: bool,
    ) -> dict[str, Any]:
        """Log score event for an individual transaction.

        Crucial: Never logs full input records or raw feature payloads.
        """
        return self.emit_event(
            "transaction_scored",
            transaction_id=transaction_id,
            model_version=model_version,
            policy_version=policy_version,
            outcome=outcome,
            anomaly_score=round(anomaly_score, 4),
            policy_triggered=policy_triggered,
        )

    def log_run_completed(
        self,
        total_analysed: int,
        review_count: int,
        review_rate: float,
    ) -> dict[str, Any]:
        return self.emit_event(
            "run_completed",
            total_analysed=total_analysed,
            review_count=review_count,
            review_rate=round(review_rate, 4),
        )

    def log_run_failed(self, error_message: str) -> dict[str, Any]:
        return self.emit_event("run_failed", error=error_message)

    def get_events(self) -> list[dict[str, Any]]:
        """Return shallow copies of all buffered events."""
        return list(self._events)

    def to_json(self, indent: int = 2) -> str:
        """Return formatted JSON string of all events in this run."""
        return json.dumps(self._events, indent=indent, ensure_ascii=False)
