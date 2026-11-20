# Intent

## Problem Statement

Fraud analysts at a financial institution need a tool to triage payment transactions quickly and consistently. Manual review of every transaction is not scalable. Automated blocking based on a single model is too opaque and risky for a regulated context. The gap is a lightweight, auditable triage layer that ranks candidate transactions for human review with factual, traceable evidence.

## Intended Users

A fraud analyst or risk operations team member who wants to load a batch of payment transactions, see which are most anomalous, and inspect the specific input values and scoring signals that drove each triage decision — before escalating to a confirmed fraud investigation.

## Assumptions

- Input data arrives as a flat CSV with pre-aggregated synthetic features (amount, historical average, velocity, device flag). No real-time streaming aggregation is performed.
- The reference model is fitted once on a fixed synthetic baseline; it is not retrained per run.
- Outputs are triage signals for human review, not autonomous decisions.
- The environment is a local developer machine running Python 3.11 with no cloud dependencies.

## Constraints

- Python 3.11+, Streamlit, pandas, scikit-learn only. No external APIs, databases, or infrastructure.
- No LLM integration, authentication, Docker, or paid services.
- Entirely offline and credential-free.
- Synthetic identifiers only; no real customer data.

## Out of Scope

- Real-time streaming ingestion or feature store aggregation.
- Supervised learning or model retraining from analyst feedback.
- Production deployment, authentication, or multi-tenancy.
- Calibrated fraud probabilities (scores are uncalibrated anomaly signals).

## Success Criteria

1. An analyst can load bundled synthetic transactions, run analysis, and see a ranked review queue in one click.
2. Each flagged transaction shows factual input-derived evidence (not speculative model explanations).
3. Telemetry captures correlation IDs, event names, outcomes, and durations without logging sensitive payload data.
4. All automated tests pass from a clean checkout with a single command.
5. No credentials, paid services, or restricted data are required at any point.
