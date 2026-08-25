# RVC-FANET

Route-Validity-Contract Routing for Flying Ad Hoc Networks

## Overview

RVC-FANET is a risk-budgeted routing protocol for Flying Ad Hoc Networks (FANETs). It utilizes:
- Constant-Velocity prediction for dynamic link state tracking.
- A finite-horizon safety margin to bound prediction errors.
- A frozen empirical calibration to map safety margins to link-risk probability.
- Additive route-risk composition to bound the end-to-end failure probability of a candidate route.
- A risk-budget ($\alpha_{\mathrm{route}}$) to limit the maximum acceptable route failure probability.
- A Route-Validity Contract ensuring the chosen route remains valid for the specified horizon without the need for periodic hello-message probing.

## Requirements

- ns-3.41
- Python 3.x
- NumPy, Pandas, SciPy, Matplotlib (for running the Python scripts)

## Repository Structure

- `src/`: Core ns-3 C++ implementation of RVC-FANET and PPR.
- `scripts/`: Python scripts for executing experiments, analysis, figure generation, and validation.
- `scripts/validation/`: Additional stress-tests and validation experiments.

## Build

Place the `rvc-fanet-sim.cc` file into your `ns-3.41/scratch` directory and configure the build using ns-3's standard CMake or waf build system.
```bash
./ns3 configure
./ns3 build
```

## Running PPR

To run the Point-Predictive Routing (PPR) baseline for a single simulation:
```bash
./ns3 run "scratch/rvc-fanet-sim --protocol=PPR"
```

## Running RVC-FANET

To run the full RVC-FANET protocol:
```bash
./ns3 run "scratch/rvc-fanet-sim --protocol=RVC"
```

## Experiments

The `scripts/` directory contains several runners corresponding to the evaluations:
- `run_stage2_ablation.py`: Executes the A0-A3 ablation study.
- `run_stage2_abrupt.py`: Executes the abrupt-mobility stress test.
- `run_stage2_matrix.py`: Executes the network-density sensitivity sweep.
- `run_stage2_gate1.py`, `run_stage2_rest.py`: Execute the PPR vs RVC comparison.
- `run_all_experiments.py`: Unified orchestrator for 30-seed matched executions.

## Analysis

- `analyze_all.py`: Processes the raw CSV outputs to generate statistical results, PDR, Conditional PDR, delay, and finite-horizon route failure rates.

## Figures

- `generate_final_figures.py`: Re-generates publication figures from processed results.
- `generate_stage2_figures.py`, `plot_density.py`: Generates specific analysis plots (ablation, density sweeps).

## Tests

- `conformal_audit.py`, `rho_audit.py`: Validates empirical calibration and nominal coverage.
- `predictor_unit_test.py`, `high_speed_test.py`, `smoke_test.py`: Verifies prediction correctness, numerical behavior, and general ns-3 integration.

## Citation

A. Helen Sharmila and P. Deepanramkumar,
“RVC-FANET: Route-Validity-Contract Routing for Flying Ad Hoc Networks.”
