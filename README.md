# RVC-FANET

Route-Validity-Contract Routing for Flying Ad Hoc Networks

## Overview

RVC-FANET performs finite-horizon route admission using:
- Constant-Velocity prediction;
- finite-horizon safety margin;
- empirical calibration;
- link-risk estimation;
- route-level risk composition;
- risk-budgeted route admission;
- route-validity contract.

## Requirements

- ns-3.41
- Python 3.x
- NumPy
- Pandas
- SciPy
- Matplotlib

## Repository Structure

- `src/`: RVC-FANET ns-3 implementation source code
- `scripts/`: Scripts required to run experiments and generate figures
- `configs/`: Configuration files

## Build

Place the `rvc-fanet-sim.cc` file into your `ns-3.41/scratch` directory and configure the build using ns-3's standard waf or CMake build system.
```bash
./ns3 configure
./ns3 build
```

## Run

To run the Point-Predictive Routing (PPR) baseline:
```bash
./ns3 run "scratch/rvc-fanet-sim --protocol=PPR"
```

To run the RVC-FANET protocol:
```bash
./ns3 run "scratch/rvc-fanet-sim --protocol=RVC"
```

## Reproducing Results

Run the full suite of experiments:
```bash
python scripts/run_all_experiments.py
```
Process and generate figures:
```bash
python scripts/generate_final_figures.py
```

## Citation

A. Helen Sharmila and P. Deepanramkumar,
“RVC-FANET: Route-Validity-Contract Routing for Flying Ad Hoc Networks.”
