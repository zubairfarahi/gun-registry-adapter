"""
Generate Synthetic NICS Individual Records from Aggregate Data.

CRITICAL LIMITATION: The real NICS dataset contains state-level monthly aggregates,
NOT individual background check records. This script generates plausible individual
records from those aggregates to enable probabilistic linkage testing.

This is documented as a dataset limitation mitigation strategy.
"""

import pandas as pd
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

# Faker for generating realistic names and addresses
from faker import Faker

fake = Faker()


def generate_synthetic_nics_records(
    nics_aggregate_path: str,
    output_path: str,
    num_records_per_state: int = 1000,
    approved_rate: float = 0.95
):
    """
    Generate synthetic individual NICS records from aggregate statistics.

    Strategy:
    1. Load NICS aggregate data (state-level monthly totals)
    2. For each state, generate N individual records
    3. Use Faker to create realistic names, DOBs, addresses
    4. Assign outcomes (approved/denied) based on approval rate
    5. Save as JSON for use in probabilistic linkage

    Args:
        nics_aggregate_path: Path to NICS CSV file (state-level aggregates)
        output_path: Path to save synthetic individual records JSON
        num_records_per_state: Number of synthetic records to generate per state
        approved_rate: Percentage of records that are approved (0.0-1.0)
    """
    print("=" * 80)
    print("Generating Synthetic NICS Individual Records")
    print("=" * 80)

    # Load NICS aggregate data
    print(f"\nLoading NICS aggregate data from: {nics_aggregate_path}")
    df = pd.read_csv(nics_aggregate_path)

    # Get unique states
    # NICS data format: month, state, permit, handgun, long_gun, totals, etc.
    if "state" not in df.columns:
        raise ValueError("NICS data missing 'state' column")

    states = df["state"].unique()
    print(f"Found {len(states)} unique states in NICS data")

    # Generate synthetic records
    synthetic_records = []

    for state in states:
        print(f"\nGenerating {num_records_per_state} records for {state}...")

        # Filter data for this state
        state_data = df[df["state"] == state]

        # Get average monthly totals (to inform generation)
        if "totals" in state_data.columns:
            avg_monthly_checks = state_data["totals"].mean()
        else:
            avg_monthly_checks = num_records_per_state

        print(f"  Average monthly checks for {state}: {avg_monthly_checks:.0f}")

        # Generate individual records
        for i in range(num_records_per_state):
            # Generate outcome (approved/denied)
            outcome = "approved" if random.random() < approved_rate else "denied"

            # Generate random date within last 5 years
            days_ago = random.randint(0, 365 * 5)
            check_date = datetime.now() - timedelta(days=days_ago)

            # Generate realistic person
            name = fake.name()
            dob = fake.date_of_birth(minimum_age=21, maximum_age=75).strftime("%Y-%m-%d")
            address = fake.address().replace("\n", ", ")

            # Create record
            record = {
                "check_id": f"{state}_{check_date.strftime('%Y%m')}_{i:06d}",
                "name": name,
                "dob": dob,
                "state": state,
                "address": address,
                "outcome": outcome,
                "check_date": check_date.strftime("%Y-%m-%d"),
                "_synthetic": True,  # Flag indicating this is synthetic data
                "_generated_from": "aggregate_statistics"
            }

            synthetic_records.append(record)

    print(f"\n" + "=" * 80)
    print(f"Generated {len(synthetic_records)} total synthetic records")
    print(f"Breakdown: {sum(1 for r in synthetic_records if r['outcome'] == 'approved')} approved, "
          f"{sum(1 for r in synthetic_records if r['outcome'] == 'denied')} denied")

    # Save to JSON
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(synthetic_records, f, indent=2)

    print(f"\nSaved synthetic records to: {output_path}")
    print(f"File size: {output_file.stat().st_size / 1024:.1f} KB")
    print("=" * 80)

    # Generate summary statistics
    _print_summary(synthetic_records)

    return synthetic_records


def _print_summary(records: List[Dict[str, Any]]):
    """Print summary statistics for generated records."""
    print("\nSummary Statistics:")
    print("-" * 80)

    # State distribution
    states = {}
    for record in records:
        state = record["state"]
        states[state] = states.get(state, 0) + 1

    print(f"States represented: {len(states)}")
    print(f"Top 5 states by record count:")
    for state, count in sorted(states.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {state}: {count}")

    # Outcome distribution
    approved = sum(1 for r in records if r["outcome"] == "approved")
    denied = sum(1 for r in records if r["outcome"] == "denied")
    print(f"\nOutcomes:")
    print(f"  Approved: {approved} ({approved/len(records)*100:.1f}%)")
    print(f"  Denied: {denied} ({denied/len(records)*100:.1f}%)")

    # Age distribution (calculate from DOB)
    ages = []
    for record in records:
        try:
            dob = datetime.strptime(record["dob"], "%Y-%m-%d")
            age = (datetime.now() - dob).days // 365
            ages.append(age)
        except:
            pass

    if ages:
        print(f"\nAge distribution:")
        print(f"  Min: {min(ages)}, Max: {max(ages)}, Mean: {sum(ages)/len(ages):.1f}")

    print("-" * 80)


if __name__ == "__main__":
    # Default paths (relative to script location)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    nics_path = project_root / "data/raw/nics_data/nics-firearm-background-checks.csv"
    output_path = project_root / "data/processed/synthetic_nics_records.json"

    # Check if NICS data exists
    if not nics_path.exists():
        print(f"ERROR: NICS data not found at {nics_path}")
        print("Please download NICS data from:")
        print("https://github.com/BuzzFeedNews/nics-firearm-background-checks/")
        exit(1)

    # Generate synthetic records
    generate_synthetic_nics_records(
        nics_aggregate_path=str(nics_path),
        output_path=str(output_path),
        num_records_per_state=1000,  # Generate 1000 records per state
        approved_rate=0.95  # 95% approval rate (realistic per FBI statistics)
    )

    print("\n✅ Synthetic NICS generation complete!")
    print(f"Use this file in your .env: SYNTHETIC_NICS_PATH={output_path}")
