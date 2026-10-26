"""Generate SYNTHETIC injection-molding data.

Nothing here comes from a real machine. All values are invented.
Output: sample_data.csv and sample_data.json (same rows).
Run: python generate_data.py
"""
import csv
import json
import random
from datetime import datetime, timedelta, timezone

SEED = 42
HOURS = 24
START = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
MACHINE = "machine_01"

# invented healthy baseline: (mean, standard deviation)
BASE = {
    "cycle_time_s": (32.0, 0.40),
    "melt_temp_c": (230.0, 1.5),
    "mold_temp_c": (45.0, 0.8),
    "injection_pressure_bar": (950.0, 12.0),
    "hold_pressure_bar": (520.0, 8.0),
    "cushion_mm": (4.5, 0.15),
}

# invented faults: (label, first_cycle, length_in_cycles)
FAULTS = [
    ("heater_drift", 700, 120),       # melt temperature creeps up
    ("cooling_blockage", 1500, 80),   # mold gets warmer, cycles get longer
    ("pressure_loss", 2300, 30),      # injection pressure drops, cushion grows
]


def apply_fault(label, progress, v):
    """progress goes from 0.0 to 1.0 while the fault is active."""
    if label == "heater_drift":
        v["melt_temp_c"] += 18.0 * progress
    elif label == "cooling_blockage":
        v["mold_temp_c"] += 12.0 * progress
        v["cycle_time_s"] += 3.0 * progress
    elif label == "pressure_loss":
        v["injection_pressure_bar"] *= 1.0 - 0.15 * progress
        v["cushion_mm"] += 0.9 * progress


def main():
    rng = random.Random(SEED)
    rows = []
    t = START
    end = START + timedelta(hours=HOURS)
    cycle = 0
    while t < end:
        v = {k: rng.gauss(m, s) for k, (m, s) in BASE.items()}
        label = "none"
        for name, first, length in FAULTS:
            if first <= cycle < first + length:
                label = name
                apply_fault(name, (cycle - first + 1) / length, v)
        severe = (v["melt_temp_c"] > 244 or v["mold_temp_c"] > 55
                  or v["injection_pressure_bar"] < 830)
        row = {"timestamp": t.strftime("%Y-%m-%dT%H:%M:%SZ"),
               "machine_id": MACHINE, "cycle": cycle}
        row.update({k: round(x, 2) for k, x in v.items()})
        row["part_ok"] = not severe
        row["fault_label"] = label
        rows.append(row)
        t += timedelta(seconds=v["cycle_time_s"])
        cycle += 1

    with open("sample_data.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    with open("sample_data.json", "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=1)
    faults = sorted({r["fault_label"] for r in rows} - {"none"})
    print(f"{len(rows)} rows written. Fault labels: {', '.join(faults)}")


if __name__ == "__main__":
    main()
