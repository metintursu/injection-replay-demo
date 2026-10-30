# Injection Replay Demo

Synthetic injection-molding machine data, plus a small script that replays it as if it were arriving live.

> **All data in this repository is synthetic.** No value comes from a real machine, plant or company. The numbers are invented and do not describe any real process.

## What is in here

| File | Purpose |
|---|---|
| `generate_data.py` | Generates the synthetic data (fixed random seed, so the output is always the same) |
| `sample_data.csv` / `sample_data.json` | The generated data: 2,697 rows, about 24 hours of cycles |
| `replay.py` | Prints the rows one by one with realistic timing, faster than real time |
| `check_rules.py` | Tests a simple threshold rule against the injected faults and prints how early it warns |

## Quick start

Requires Python 3 (tested with 3.11). No extra packages.

    python generate_data.py                  # optional, recreates sample_data.csv and .json
    python replay.py                         # replay at 60x speed
    python replay.py --speed 600 --limit 20  # quick look at 20 rows

Every replayed row contains `"replay": true`, so downstream tools can tell it apart from live data.

## Data

| Column | Meaning |
|---|---|
| `timestamp`, `machine_id`, `cycle` | Time (fictional, 1 January 2026), machine name, cycle number |
| `cycle_time_s` | Cycle duration in seconds |
| `melt_temp_c`, `mold_temp_c` | Melt and mold temperature in degrees C |
| `injection_pressure_bar`, `hold_pressure_bar` | Pressures in bar |
| `cushion_mm` | Cushion in millimeters |
| `part_ok` | `false` when a fixed threshold is crossed (melt above 244 C, mold above 55 C or injection pressure below 830 bar) |
| `fault_label` | The fault that was injected on purpose, `none` otherwise |

Three invented faults are built in:

- `heater_drift`: melt temperature creeps up over 120 cycles
- `cooling_blockage`: the mold gets warmer and cycles get longer over 80 cycles
- `pressure_loss`: injection pressure drops and the cushion grows over 30 cycles

## Example: does a simple rule notice the faults?

`check_rules.py` learns what normal looks like from the first 600 cycles and warns when a signal stays more than 3 standard deviations away for 3 cycles in a row. Result on the synthetic data:

    fault             starts    first warning           first bad part    early warning
    heater_drift      06:13     40 cycles / 21.3 min    88 cycles         48 cycles / 25.6 min
    cooling_blockage  13:20     17 cycles / 9.2 min     56 cycles         39 cycles / 21.7 min
    pressure_loss     20:28     7 cycles / 3.8 min      23 cycles         16 cycles / 8.5 min

    Warnings raised while the machine was healthy: 0 (in 2467 healthy cycles)

With `--consecutive 1` (react to a single sample) the warnings come earlier, but 13 false warnings appear in the healthy cycles. This trade-off is the point of the example.

These numbers are optimistic. The noise is a clean bell curve and the faults are smooth, so they are easy cases. Real machines have jumps, shift changes and mold changes. The result shows that the method works on this data, not that it will work on a real machine.

## Limitations

- Synthetic data only. Do not draw conclusions about real machines from it.
- This is a replay, not a live feed.
- `fault_label` is the ground truth we injected. It is useful for testing whether a rule or model would notice a fault, but real faults are messier.
- There is no prediction model here. `check_rules.py` is a plain threshold rule, not machine learning.

## Related

[Unified Automation Hub](https://github.com/metintursu/unified-automation-hub): a Docker stack for industrial automation (Node-RED, n8n, EMQX, InfluxDB, Grafana).

## License

MIT

## Open-data check

Exploratory test on a public labeled dataset (ProBayes, CC BY 4.0): see [open-data-check/RESULTS.md](open-data-check/RESULTS.md). First hint only, not evidence for any factory.

