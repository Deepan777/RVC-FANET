# RVC-FANET

Route-Validity-Contract Routing for Flying Ad Hoc Networks

## Overview

RVC-FANET is a risk-budgeted routing protocol for Flying Ad Hoc Networks (FANETs). It utilizes:
- Constant-Velocity prediction for dynamic link state tracking
- finite-horizon spatial safety margin
- empirical calibration for link-risk estimation
- additive route-risk composition
- route-risk budget ($\alpha_{\mathrm{route}}$)
- Route-Validity Contract

## Requirements

- ns-3.41
- Python 3.x
- NumPy, Pandas, SciPy, Matplotlib

## Repository Structure

- `src/`: Main ns-3 implementation.
- `scripts/`: Experiment execution, calibration, statistical analysis, validation, and figure-generation scripts.
- `scripts/validation/`: Additional stress-tests and validation experiments.

## Running the Implementation

To run the Point-Predictive Routing (PPR) baseline:
```bash
./ns3 run "scratch/rvc-fanet-sim --protocol=PPR"
```

To run the RVC-FANET protocol:
```bash
./ns3 run "scratch/rvc-fanet-sim --protocol=RVC"
```

## Experiments

The `scripts/` directory contains several runners corresponding to the evaluations:
- `run_stage2_gate1.py`, `run_stage2_rest.py`: speed comparison
- `run_all_experiments.py`: unified matched-seed orchestration
- `run_stage2_matrix.py`: density sensitivity
- `run_stage2_ablation.py`: component ablation
- `run_stage2_abrupt.py`: abrupt-mobility stress test
- `conformal_audit.py`, `rho_audit.py`: calibration evaluation

## Analysis and Figures

- `analyze_all.py`: generates statistical results, tables, PDR, Conditional PDR, delay, and route failure rates.
- `generate_final_figures.py`: generates final manuscript figures.
- `generate_stage2_figures.py`, `plot_density.py`: generates specific analysis plots.

## Tests

- `predictor_unit_test.py`, `high_speed_test.py`, `smoke_test.py`: Verifies prediction correctness, numerical behavior, and general ns-3 integration.

## Citation

A. Helen Sharmila and P. Deepanramkumar,
“RVC-FANET: Route-Validity-Contract Routing for Flying Ad Hoc Networks.”
