# Open-data check: can process signals separate OK from NOK parts?

Status: exploratory. 47 experiments from one lab. This is a first hint, not evidence that anything works in a factory.

All data here is public. No real factory data is used anywhere in this repository.

## Data

ProBayes injection molding dataset (file dataset_V2.parquet), published by SKZ (German Plastics Center) and Fraunhofer IPA, license CC BY 4.0. The dataset is not included in this repository (89 MB). Download it from its original publisher and read its data description first.

- Machine: KraussMaffei 160-750PX, part: "warpage shell", materials: PP and ABS (70% recyclate).
- 564 parts in 47 experiments (date + experiment name), about 12 parts each.
- Label LBL_NOK = at least one of the defects "underfilled" or "sink marks" was found by manual inspection.

## Important facts about the data

- Every experiment is either all OK or all NOK (34 OK experiments, 13 NOK experiments, none mixed). The label is decided by the machine setting, so the real sample size is 47, not 564.
- The machine settings were chosen on purpose to produce bad parts. Real production varies far less.
- NOK share is 27.5%, so plain accuracy is misleading. Always compare against "say OK every time" (0 of 13 NOK found).

## Method

- Only machine-side process signals are used as features (QUA, DXP, TCE, TCN, DOS, DRY, ENV, CALC). Time series are summarised per cycle (mean, std, min, max).
- Excluded to avoid leaking the answer: LBL (labels), CV (part measurements), SCA (weight), SIM (simulation), IR (thermal camera), MET (except for grouping and material).
- Validation: leave-one-experiment-out. Each experiment is held out completely. Thresholds and models are learned only from the other experiments.
- Script output labels are in Turkish.

## Results

Models on all kept features (leave-one-experiment-out):

| Input | Model | NOK parts found | False alarms (OK parts) | NOK experiments found | False alarm experiments |
|---|---|---|---|---|---|
| Settings only | Logistic | 77% | 21% | 10/13 | 7/34 |
| Settings only | Random forest | 62% | 18% | 8/13 | 6/34 |
| Process signals only | Logistic | 85% | 4% | 11/13 | 1/34 |
| Process signals only | Random forest | 66% | 6% | 8/13 | 2/34 |
| Settings + signals | Logistic | 84% | 4% | 11/13 | 1/34 |
| Settings + signals | Random forest | 63% | 6% | 8/13 | 2/34 |

Simple threshold rules, one threshold set for both materials (simple_rule.py):

| Rule | NOK experiments found | False alarm experiments | Balanced accuracy |
|---|---|---|---|
| A) best single signal, chosen automatically | 6/13 | 5/34 | 66% |
| B) cushion volume high OR cavity pressure low | 12/13 | 10/34 | 81% |
| B') cushion high AND cavity pressure low | 5/13 | 0/34 | 69% |
| C) holding pressure setting only | 7/13 | 2/34 | 74% |

Same rules, thresholds learned per material (simple_rule_material.py):

| Rule | NOK experiments found | False alarm experiments | Balanced accuracy |
|---|---|---|---|
| A) best single signal | 9/13 | 5/34 | 77% |
| B) cushion high OR cavity pressure low | 13/13 | 8/34 | 88% |
| B') cushion high AND cavity pressure low | 7/13 | 1/34 | 75% |
| C) holding pressure setting only | 10/13 | 7/34 | 78% |

Signals that separated bad from good experiments best (top_signals.py): cushion volume (higher in NOK), cavity pressure (lower in NOK), holding pressure (lower in NOK). Cooling water temperature, air temperature and the drying system told almost nothing. This matches injection molding physics: too little holding pressure packs too little melt into the mold.

## What this does and does not show

- Process signals carry real information about these defects, and simple rules beat "always OK".
- The advantage of signals over just reading the settings is small (about 3 experiments) and could be chance with 47 experiments.
- The best rule still raised false alarms in about a quarter of the good experiments, which would be too noisy in production.
- The signals are consequences of the defect cause (too little packing), so this is detection while producing, not proven early warning.
- Features were screened on the same 47 experiments, so results are somewhat optimistic.
- One machine, one mold, one lab, deliberately bad settings. Nothing here shows the result transfers to another factory.
- What is missing for real use is labeled scrap data from the actual machine.

## Reproduce

Put dataset_V2.parquet in a folder with these scripts, then run:

    pip install pandas pyarrow scikit-learn
    python build_features.py
    python evaluate.py
    python top_signals.py
    python simple_rule.py
    python simple_rule_material.py

build_features.py writes features.parquet (ignored by git).

## Credit

Data: SKZ and Fraunhofer IPA, project "ProBayes", CC BY 4.0. Analysis scripts in this folder: MIT, see the repository license.
