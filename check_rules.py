"""Check how a simple threshold rule behaves on the SYNTHETIC data.

The rule learns what "normal" looks like from the first 600 cycles, then
raises a warning when a signal stays far from normal for several cycles
in a row. The injected faults in sample_data.csv are the ground truth.

Usage:
  python check_rules.py                  # warn after 3 cycles in a row
  python check_rules.py --consecutive 1  # react to a single sample
"""
import argparse
import csv
import statistics
from datetime import datetime

# signal -> direction that means "worse" (+1 higher is worse, -1 lower is worse)
SIGNALS = {
    "cycle_time_s": +1,
    "melt_temp_c": +1,
    "mold_temp_c": +1,
    "injection_pressure_bar": -1,
    "cushion_mm": +1,
}
LEARN_CYCLES = 600   # healthy rows used to learn "normal"
WARN_Z = 3.0         # distance from normal, in standard deviations


def load(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            for k in SIGNALS:
                r[k] = float(r[k])
            r["part_ok"] = r["part_ok"] == "True"
            r["t"] = datetime.strptime(r["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
            rows.append(r)
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", default="sample_data.csv")
    ap.add_argument("--consecutive", type=int, default=3,
                    help="cycles in a row beyond the limit before warning")
    args = ap.parse_args()

    rows = load(args.file)
    learn = rows[:LEARN_CYCLES]
    stats = {s: (statistics.mean(r[s] for r in learn),
                 statistics.stdev(r[s] for r in learn)) for s in SIGNALS}

    streak = {s: 0 for s in SIGNALS}
    warn_rows = []                      # row indexes where a new warning starts
    for i, r in enumerate(rows):
        fired = False
        for s, d in SIGNALS.items():
            m, sd = stats[s]
            z = d * (r[s] - m) / sd
            streak[s] = streak[s] + 1 if z > WARN_Z else 0
            if streak[s] == args.consecutive:
                fired = True
        if fired:
            warn_rows.append(i)

    print(f"Rule: warn when a signal is more than {WARN_Z:g} standard deviations "
          f"from normal for {args.consecutive} cycle(s) in a row.")
    print(f"Normal is learned from the first {LEARN_CYCLES} cycles.\n")
    print(f"{'fault':<18}{'starts':<10}{'first warning':<24}{'first bad part':<18}early warning")
    labels = [x for x in dict.fromkeys(r["fault_label"] for r in rows) if x != "none"]
    for lab in labels:
        idx = [i for i, r in enumerate(rows) if r["fault_label"] == lab]
        a, b = idx[0], idx[-1]
        w = next((i for i in warn_rows if a <= i <= b), None)
        bad = next((i for i in idx if not rows[i]["part_ok"]), None)
        start = rows[a]["t"].strftime("%H:%M")
        if w is None:
            warn_txt = "not detected"
        else:
            mins = (rows[w]["t"] - rows[a]["t"]).total_seconds() / 60
            warn_txt = f"{w - a} cycles / {mins:.1f} min"
        bad_txt = "-" if bad is None else f"{bad - a} cycles"
        if w is not None and bad is not None:
            early = f"{bad - w} cycles / {(rows[bad]['t'] - rows[w]['t']).total_seconds() / 60:.1f} min"
        else:
            early = "-"
        print(f"{lab:<18}{start:<10}{warn_txt:<24}{bad_txt:<18}{early}")

    healthy = [i for i, r in enumerate(rows) if r["fault_label"] == "none"]
    hs = set(healthy)
    false_w = sum(1 for i in warn_rows if i in hs)
    print(f"\nWarnings raised while the machine was healthy: {false_w} "
          f"(in {len(healthy)} healthy cycles)")


if __name__ == "__main__":
    main()
