"""Replay the synthetic data as if it were arriving live.

This is a replay of recorded (synthetic) rows. It is NOT live data.
Usage:
  python replay.py                         # 60x faster than real time
  python replay.py --speed 600 --limit 20  # quick look at 20 rows
"""
import argparse
import csv
import json
import time
from datetime import datetime

FLOATS = ("cycle_time_s", "melt_temp_c", "mold_temp_c",
          "injection_pressure_bar", "hold_pressure_bar", "cushion_mm")


def parse_ts(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", default="sample_data.csv")
    ap.add_argument("--speed", type=float, default=60.0,
                    help="1 = real time, 60 = 60 times faster")
    ap.add_argument("--limit", type=int, default=0,
                    help="stop after N rows (0 = all rows)")
    args = ap.parse_args()

    prev = None
    with open(args.file, newline="", encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f)):
            if args.limit and i >= args.limit:
                break
            ts = parse_ts(row["timestamp"])
            if prev is not None:
                time.sleep(max(0.0, (ts - prev).total_seconds() / args.speed))
            prev = ts
            out = {"replay": True, "timestamp": row["timestamp"],
                   "machine_id": row["machine_id"], "cycle": int(row["cycle"])}
            for k in FLOATS:
                out[k] = float(row[k])
            out["part_ok"] = row["part_ok"] == "True"
            out["fault_label"] = row["fault_label"]
            print(json.dumps(out), flush=True)


if __name__ == "__main__":
    main()
