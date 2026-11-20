"""Synthetic dataset generator for Fraud Triage Workbench.

Provides deterministic generation of:
1. Reference dataset: Used exclusively to fit the anomaly detection baseline model.
2. Demonstration dataset: A sample batch representing transactions to be evaluated.
"""

from pathlib import Path

import numpy as np
import pandas as pd

DEFAULT_REFERENCE_SEED = 42
DEFAULT_DEMO_SEED = 1337

REQUIRED_COLUMNS = [
    "transaction_id",
    "amount",
    "historical_average_amount",
    "transactions_last_10m",
    "is_new_device",
]


def generate_reference_data(
    n_samples: int = 1000, seed: int = DEFAULT_REFERENCE_SEED
) -> pd.DataFrame:
    """Generate deterministic reference transactions for baseline model training.

    This dataset simulates standard customer transaction behaviour without labels.
    Never mixed with runtime evaluation transactions.
    """
    rng = np.random.default_rng(seed)

    historical_averages = np.round(rng.uniform(20.0, 200.0, size=n_samples), 2)
    # Ratios closely distributed around 1.0 (mean ~ 1.0, std ~ 0.25, bounded)
    ratios = np.clip(rng.normal(1.0, 0.25, size=n_samples), 0.2, 2.5)
    amounts = np.round(historical_averages * ratios, 2)
    # Ensure minimum amount is strictly positive
    amounts = np.maximum(amounts, 1.00)

    # Low velocity in standard baseline (mostly 0 or 1, occasionally 2)
    velocities = rng.poisson(lam=0.4, size=n_samples)
    velocities = np.clip(velocities, 0, 5)

    # Low proportion of new devices (~7%)
    new_devices = rng.random(size=n_samples) < 0.07

    transaction_ids = [f"REF-{i + 1:05d}" for i in range(n_samples)]

    df = pd.DataFrame(
        {
            "transaction_id": transaction_ids,
            "amount": amounts,
            "historical_average_amount": historical_averages,
            "transactions_last_10m": velocities.astype(int),
            "is_new_device": new_devices.astype(bool),
        }
    )
    return df[REQUIRED_COLUMNS]


def generate_demo_data(
    n_samples: int = 50, seed: int = DEFAULT_DEMO_SEED
) -> pd.DataFrame:
    """Generate deterministic demonstration transactions for triage evaluation.

    Contains mostly ordinary payment transactions alongside a small number of
    deliberately unusual transactions (e.g. extreme amount spikes, high velocity bursts,
    new device with high multiplier).
    """
    rng = np.random.default_rng(seed)

    # 1. Generate ordinary transactions
    n_ordinary = max(1, n_samples - 6)
    hist_avg = np.round(rng.uniform(25.0, 180.0, size=n_ordinary), 2)
    ratios = np.clip(rng.normal(1.0, 0.22, size=n_ordinary), 0.3, 2.0)
    amounts = np.round(hist_avg * ratios, 2)
    amounts = np.maximum(amounts, 2.00)
    velocities = np.clip(rng.poisson(lam=0.35, size=n_ordinary), 0, 3)
    new_devices = rng.random(size=n_ordinary) < 0.06

    ordinary_df = pd.DataFrame(
        {
            "transaction_id": [f"TXN-{i + 1:04d}" for i in range(n_ordinary)],
            "amount": amounts,
            "historical_average_amount": hist_avg,
            "transactions_last_10m": velocities.astype(int),
            "is_new_device": new_devices.astype(bool),
        }
    )

    # 2. Inject specific deliberate scenarios (never labeled in the dataset)
    unusual_records = [
        # Scenario A: Extreme amount multiplier (amount_ratio >= 5.0 policy rule trigger)
        {
            "transaction_id": f"TXN-{n_ordinary + 1:04d}",
            "amount": 1250.00,
            "historical_average_amount": 150.00,
            "transactions_last_10m": 0,
            "is_new_device": False,
        },
        # Scenario B: High transaction burst velocity
        {
            "transaction_id": f"TXN-{n_ordinary + 2:04d}",
            "amount": 45.00,
            "historical_average_amount": 40.00,
            "transactions_last_10m": 7,
            "is_new_device": False,
        },
        # Scenario C: New device with high velocity and elevated amount
        {
            "transaction_id": f"TXN-{n_ordinary + 3:04d}",
            "amount": 540.00,
            "historical_average_amount": 90.00,
            "transactions_last_10m": 5,
            "is_new_device": True,
        },
        # Scenario D: Clear amount spike triggering 5x policy
        {
            "transaction_id": f"TXN-{n_ordinary + 4:04d}",
            "amount": 620.00,
            "historical_average_amount": 100.00,
            "transactions_last_10m": 1,
            "is_new_device": False,
        },
        # Scenario E: New device combined with moderate multiplier and velocity
        {
            "transaction_id": f"TXN-{n_ordinary + 5:04d}",
            "amount": 320.00,
            "historical_average_amount": 85.00,
            "transactions_last_10m": 4,
            "is_new_device": True,
        },
        # Scenario F: Subtle elevated velocity on known device
        {
            "transaction_id": f"TXN-{n_ordinary + 6:04d}",
            "amount": 185.00,
            "historical_average_amount": 60.00,
            "transactions_last_10m": 6,
            "is_new_device": False,
        },
    ]

    unusual_df = pd.DataFrame(unusual_records[: max(0, n_samples - n_ordinary)])
    combined_df = pd.concat([ordinary_df, unusual_df], ignore_index=True)

    # Re-index IDs consecutively to avoid sorting bias
    combined_df["transaction_id"] = [
        f"TXN-{i + 1:04d}" for i in range(len(combined_df))
    ]
    return combined_df[REQUIRED_COLUMNS]


def save_sample_csv(output_path: str | Path = "data/sample_transactions.csv") -> Path:
    """Export the deterministic demo dataset to CSV."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df = generate_demo_data(n_samples=50, seed=DEFAULT_DEMO_SEED)
    df.to_csv(path, index=False)
    return path


if __name__ == "__main__":
    saved = save_sample_csv()
    print(f"Generated sample dataset at: {saved.resolve()}")
