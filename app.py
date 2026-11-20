"""Fraud Triage Workbench - Streamlit Application.

Demonstrates an unsupervised anomaly detection baseline (IsolationForest)
combined with deterministic policy rules, factual evidence statements,
and lightweight structured application telemetry.
"""

from pathlib import Path
import time
import pandas as pd
import streamlit as st

from fraud.data import generate_demo_data
from fraud.detection import (
    MODEL_VERSION,
    POLICY_AMOUNT_RATIO_THRESHOLD,
    POLICY_VERSION,
    evaluate_batch,
    train_reference_model,
)
from fraud.telemetry import TelemetryCollector
from fraud.validation import ValidationError

SAMPLE_CSV_PATH = Path("data/sample_transactions.csv")


@st.cache_resource(show_spinner="Fitting reference model baseline...")
def get_cached_model():
    """Fit IsolationForest on reference data once and cache the instance."""
    start = time.perf_counter()
    model = train_reference_model()
    training_duration_ms = round((time.perf_counter() - start) * 1000.0, 2)
    return model, training_duration_ms


def load_bundled_data() -> pd.DataFrame:
    """Load sample transactions from bundled CSV or generate deterministically."""
    if SAMPLE_CSV_PATH.exists():
        return pd.read_csv(SAMPLE_CSV_PATH)
    return generate_demo_data(n_samples=50, seed=1337)


def main():
    st.set_page_config(page_title="Fraud Triage Workbench", layout="wide")

    # Header & Synthetic Data Disclaimer
    st.title("Fraud Triage Workbench")
    st.markdown(
        """
        > **Synthetic Data Disclaimer:** This workbench operates strictly on synthetic, uncalibrated
        > test transactions for interview demonstration purposes. It does **not** connect to live payment systems,
        > calculate real fraud probabilities, or confirm fraudulent conduct without human triage review.
        """
    )

    # Load baseline model and sample transactions
    model, training_duration_ms = get_cached_model()
    sample_df = load_bundled_data()

    # Section 1: Bundled Sample Preview
    st.subheader("1. Bundled Transactions Preview")
    st.caption(f"Showing sample transactions available for evaluation ({len(sample_df)} total records).")
    st.dataframe(sample_df.head(6), use_container_width=True)

    # Section 2: Trigger Analysis
    analyse_clicked = st.button("Analyse transactions", type="primary")

    if analyse_clicked:
        collector = TelemetryCollector()
        start_analysis = time.perf_counter()
        try:
            results = evaluate_batch(sample_df, model=model, collector=collector)
            analysis_duration_ms = round((time.perf_counter() - start_analysis) * 1000.0, 2)

            # Prepare sorted review queue (lowest anomaly score = most unusual first)
            review_queue = (
                results[results["outcome"] == "Review"]
                .sort_values(by="anomaly_score", ascending=True)
                .copy()
            )

            total = len(results)
            review_count = len(review_queue)
            review_rate = (review_count / total * 100.0) if total > 0 else 0.0

            # Default transaction selection to highest priority review item if available
            default_txn = (
                review_queue["transaction_id"].iloc[0]
                if not review_queue.empty
                else results["transaction_id"].iloc[0]
            )

            st.session_state["latest_run"] = {
                "correlation_id": collector.correlation_id,
                "results": results,
                "review_queue": review_queue,
                "total_analysed": total,
                "review_count": review_count,
                "review_rate": review_rate,
                "analysis_duration_ms": analysis_duration_ms,
                "training_duration_ms": training_duration_ms,
                "events_json": collector.to_json(),
                "events_count": len(collector.get_events()),
                "selected_txn_id": default_txn,
            }
        except ValidationError as val_err:
            st.error(f"Validation Error: {val_err.message}")
            if hasattr(val_err, "errors"):
                for err in val_err.errors:
                    st.write(f"- {err}")
        except Exception as exc:
            st.error(f"Analysis failed with an unexpected error: {exc}")

    # Section 3: Review Results and Details
    if "latest_run" in st.session_state:
        run = st.session_state["latest_run"]
        results = run["results"]
        review_queue = run["review_queue"]

        st.divider()
        st.subheader("2. Analysis Run Summary")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Transactions Analysed", run["total_analysed"])
        col2.metric("Flagged for Review", run["review_count"])
        col3.metric("Review Rate", f"{run['review_rate']:.1f}%")
        col4.metric(
            "Analysis Duration",
            f"{run['analysis_duration_ms']:.1f} ms",
            help=f"Baseline model fit cached once ({run['training_duration_ms']:.1f} ms)",
        )

        st.subheader("3. Ranked Review Queue")
        if review_queue.empty:
            st.info("No transactions were flagged for review in this batch.")
        else:
            display_cols = [
                "transaction_id",
                "anomaly_score",
                "amount",
                "historical_average_amount",
                "amount_ratio",
                "transactions_last_10m",
                "is_new_device",
                "outcome",
                "policy_triggers",
            ]
            st.caption(
                "Ranked by anomaly score ascending (lower score = higher deviation from reference baseline)."
            )
            st.dataframe(
                review_queue[display_cols],
                use_container_width=True,
                hide_index=True,
            )

        st.subheader("4. Transaction Evidence & Detail Inspector")
        all_ids = results["transaction_id"].tolist()
        current_selection = run.get("selected_txn_id", all_ids[0])
        try:
            current_index = all_ids.index(current_selection)
        except ValueError:
            current_index = 0

        selected_id = st.selectbox(
            "Select transaction to inspect:",
            options=all_ids,
            index=current_index,
            key="txn_selector",
        )
        # Update selected transaction in session state without triggering re-analysis
        run["selected_txn_id"] = selected_id

        # Retrieve selected record
        record = results[results["transaction_id"] == selected_id].iloc[0]

        detail_left, detail_right = st.columns(2)

        with detail_left:
            st.markdown("#### Input Values")
            st.write(f"**Transaction ID:** `{record['transaction_id']}`")
            st.write(f"**Amount:** `${record['amount']:.2f}`")
            st.write(f"**Historical Average Amount:** `${record['historical_average_amount']:.2f}`")
            st.write(f"**Amount Ratio:** `{record['amount_ratio']:.2f}x`")
            st.write(f"**Transactions (Last 10m):** `{record['transactions_last_10m']}`")
            st.write(f"**Is New Device:** `{record['is_new_device']}`")

        with detail_right:
            st.markdown("#### Triage Findings & Decision")
            st.write(
                f"**Anomaly Score:** `{record['anomaly_score']:.4f}` *(lower = more anomalous)*"
            )
            st.write(f"**Model Finding:** `{record['model_finding']}` *(IsolationForest unsupervised baseline)*")
            st.write(f"**Outcome:** `{record['outcome']}`")

            triggers_str = (
                ", ".join(record["policy_triggers"])
                if isinstance(record["policy_triggers"], list)
                else str(record["policy_triggers"])
            )
            st.write(f"**Policy Triggers:** {triggers_str}")
            st.caption(
                f"Policy Rule: Flag if model finding == Outlier OR amount_ratio >= {POLICY_AMOUNT_RATIO_THRESHOLD:.1f}x (illustrative threshold)"
            )
            st.write(f"**Engine Versions:** `{record['model_version']}` | `{record['policy_version']}`")

        st.markdown("#### Supporting Factual Evidence")
        st.caption("Factual statements derived strictly from input values (not an explanation of internal model weights).")
        for item in record["evidence"]:
            st.markdown(f"- {item}")

        st.divider()
        st.subheader("5. Application Telemetry")
        with st.expander(
            f"View Execution Telemetry ({run['events_count']} events, Run ID: {run['correlation_id']})",
            expanded=False,
        ):
            st.write(f"**Correlation ID:** `{run['correlation_id']}`")
            st.code(run["events_json"], language="json")

    else:
        st.divider()
        st.info("Ready. Click 'Analyse transactions' above to evaluate the bundled batch.")


if __name__ == "__main__":
    main()

