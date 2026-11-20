# Decision Records

## DR-01: IsolationForest over supervised model

**Decision:** Use `sklearn.ensemble.IsolationForest` as the anomaly baseline, fitted on a fixed synthetic reference dataset.

**Rationale:** A supervised fraud classifier requires labelled historical fraud events, which are unavailable in a demonstration context. IsolationForest is unsupervised, standard, and well understood in financial risk contexts. It is deterministic given a fixed seed, making results reproducible and auditable.

**Trade-off:** IsolationForest does not output calibrated probabilities. Scores are path-depth measures, not fraud likelihoods. A production system would layer calibrated supervised models on top (e.g. LightGBM with Platt scaling).

---

## DR-02: Deterministic policy rule alongside the model

**Decision:** Flag a transaction for review if `model.predict() == -1` **OR** `amount_ratio >= 5.0`, not model alone.

**Rationale:** In regulated environments, explainability and auditability are non-negotiable. A single numeric model threshold is opaque to non-technical stakeholders. A named, explicit business rule (`amount_ratio >= 5.0`) can be reviewed, challenged, and adjusted by a risk officer without ML expertise. The OR combination means either signal alone is sufficient to trigger review.

**Trade-off:** A fixed threshold (`5.0`) is a simplification. In production this would be parameterised, versioned, and subject to a governance approval process.

---

## DR-03: Factual evidence statements over model explainability (SHAP/LIME)

**Decision:** Evidence shown to analysts is derived deterministically from raw input values (e.g. `"Amount is 8.2 times the historical average ($820.00 vs $100.00)"`), not from SHAP values or LIME approximations.

**Rationale:** SHAP and LIME add significant dependency weight and execution time. More importantly, they can produce inconsistent or misleading attributions on tree-based anomaly models. Deterministic input-derived statements are 100% faithful to the data, never hallucinate, and are easier to explain to a fraud analyst or regulator.

**Trade-off:** Factual statements describe inputs, not which features drove the model's internal decision. For a demonstration, this is acceptable and arguably safer.

---

## DR-04: Single-process Streamlit app, no API layer

**Decision:** All logic runs inside a single Streamlit process. No separate REST API or microservice.

**Rationale:** The exercise scope is a local vertical slice. Introducing FastAPI, Docker, and service-to-service communication would add significant setup complexity for no additional demonstration value. The module boundaries (`fraud/validation.py`, `fraud/detection.py`, etc.) are already drawn in a way that makes extraction into a separate API straightforward.

**Trade-off:** Not representative of a production deployment pattern. The design section documents exactly how the slice would be promoted to a scored API + UI architecture in a cloud environment.

---

## DR-05: Synthetic data only; no historical aggregation engine

**Decision:** Pre-aggregated synthetic features (historical average, 10-minute velocity) are supplied as inputs in the CSV. No sliding-window or streaming aggregation is built.

**Rationale:** Building a streaming feature engine (Kafka, Flink, Redis) would take far more than the 3-hour timebox and would be infrastructure, not engineering quality. Supplying synthetic pre-aggregated features allows the full triage workflow (validate → score → rank → evidence → telemetry) to be demonstrated end-to-end without that complexity.

**Trade-off:** In production, real-time velocity and historical average features would come from a feature store. DR-01 in the design notes documents this explicitly as a production next step.
