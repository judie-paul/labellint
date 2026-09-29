# Reproducible synthetic results

These measurements use templated synthetic data and simulated annotators, not human workers.
Each run has 200 source items, 50 annotators and three raters per item (600 records).
The validation seed was not used to select thresholds. Defaults are unchanged between runs.

Reproduce with `make results`, or run the CLI commands:

```sh
labellint run --config configs/default.yaml
labellint evaluate reports/sim.jsonl reports/scan.json --out reports/eval.json
labellint run --config configs/validation.yaml
labellint evaluate reports/validation/sim.jsonl reports/validation/scan.json --out reports/validation/eval.json
```

## Seed 42

| Detector | Precision | Recall | F1 |
|---|---:|---:|---:|
| duplicate | 0.4351 | 1.0000 | 0.6064 |
| contradiction | 0.5714 | 1.0000 | 0.7273 |
| speed | 0.8000 | 1.0000 | 0.8889 |
| agreement | 0.2708 | 0.6341 | 0.3796 |
| Combined | 0.7489 | 0.9598 | 0.8413 |

Clean-data false-positive rate: **13.1455%**.
Confusion counts: TP=167, FP=56, FN=7, TN=370.

## Seed 2026

| Detector | Precision | Recall | F1 |
|---|---:|---:|---:|
| duplicate | 0.4016 | 1.0000 | 0.5730 |
| contradiction | 0.3714 | 1.0000 | 0.5417 |
| speed | 0.7869 | 0.9796 | 0.8727 |
| agreement | 0.3718 | 0.6905 | 0.4833 |
| Combined | 0.7250 | 0.9355 | 0.8169 |

Clean-data false-positive rate: **12.3596%**.
Confusion counts: TP=145, FP=55, FN=10, TN=390.

## Interpretation

Agreement is the weakest standalone baseline: corrupted peers and
rating noise make consensus unreliable. Duplicate precision is limited by source-template
reuse and short rusher rationales. Cross-detector overlap means per-detector scores
should not be interpreted as overall audit performance. False positives remain material.

`eval.json` also contains per-corruption metrics against clean controls and a risk-threshold
sweep. Most baseline severity scores are binary, so changing the aggregate threshold
can leave predictions unchanged. Zero metric denominators return zero. No real-world
accuracy claim or paid-model evaluation is made.
