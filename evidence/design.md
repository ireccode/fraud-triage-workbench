# Design

## Architecture Overview

A single-process Streamlit application. All logic runs in one Python process on the analyst's machine. There are no network calls at runtime.

```
app.py (Streamlit UI)
   │
   ├── fraud/validation.py    Fail-fast schema & boundary checks
   ├── fraud/detection.py     IsolationForest model + policy rules + evidence
   ├── fraud/telemetry.py     Structured JSON stdout emitter
   └── fraud/data.py          Deterministic synthetic data generators
```

## Data Flow

```
data/sample_transactions.csv
        │
        ▼
validate_transactions()       Schema, uniqueness, type, range checks
        │
        ▼
build_feature_matrix()        Derives amount_ratio = amount / historical_average_amount
        │
        ▼
IsolationForest.predict()     Fitted once on 1,000-row reference set (seed=42, cached)
        │
        ▼
Policy Rule                   Flag if model == -1 OR amount_ratio >= 5.0
        │
        ▼
Factual Evidence              Deterministic strings from input values (no model internals)
        │
        ▼
Streamlit session_state       Ranked queue + detail panel + telemetry viewer
```

## Component Boundaries

| Component | Responsibility | Coupling |
|---|---|---|
| `fraud/data.py` | Generate reference and demo datasets | None — pure data |
| `fraud/validation.py` | Reject invalid input before scoring | Raises `ValidationError` |
| `fraud/detection.py` | Score, apply policy, build evidence | Calls validation internally |
| `fraud/telemetry.py` | Emit and buffer structured events | Called by detection |
| `app.py` | UI, session state, error display | Orchestrates all modules |

## Key Trade-offs

**IsolationForest vs supervised model**: IsolationForest is unsupervised and requires no labelled fraud data, which is realistic for a demonstration. Supervised models (e.g. LightGBM) would need historical fraud labels.

**Deterministic rules alongside model**: The `amount_ratio >= 5.0` threshold is a simple, explainable business rule that can be audited without understanding the model internals. This reflects a layered approach common in regulated environments.

**Factual evidence over model explainability**: SHAP or LIME would add explainability infrastructure and dependency weight. For a triage demonstration, deterministic input-derived statements are more trustworthy (no hallucination risk) and faster to compute.

**Single process, no API layer**: Keeps the demo self-contained. A production system would separate a scoring API (FastAPI + model server) from the UI.

## Security and Privacy Considerations

- Telemetry events never log raw financial values, amounts, or customer identifiers. Only synthetic transaction IDs, scores, and outcome labels appear in logs.
- No authentication layer is included (out of scope for a local demo).
- No data leaves the local machine at runtime.

## Technology Choices

| Technology | Reason |
|---|---|
| Streamlit | Rapid analyst-facing UI with minimal frontend boilerplate |
| scikit-learn IsolationForest | Standard, auditable unsupervised anomaly detector; no licensing cost |
| pandas | Columnar data wrangling; widely understood in data engineering teams |
| pytest + AppTest | Unit and integration tests including Streamlit session state |

## Likely Production / Cloud Shape

In a production environment this slice would evolve to:

1. **Feature Store** (e.g. Feast + Redis): Replace pre-aggregated CSV features with real-time sliding-window aggregations.
2. **Model Registry** (e.g. MLflow): Version and promote the IsolationForest artefact; support A/B testing against supervised models.
3. **Scoring API** (e.g. FastAPI on Cloud Run / EKS): Separate the model from the UI; expose a REST endpoint consumed by the Streamlit frontend or a downstream case management system.
4. **Observability** (e.g. OpenTelemetry → Datadog / Grafana): Replace stdout JSON with OTLP traces and metrics.
5. **CI/CD** (GitHub Actions → staging → production): The existing `ci.yml` test workflow forms the first gate; add Docker build, container scan, and canary deployment stages.
