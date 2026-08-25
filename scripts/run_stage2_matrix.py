"""
Stage 2: Corrected Full Experiment Matrix for RVC-FANET
All outputs go to .\results\raw\

Runs AODV, PPR, RVC across:
  - Density sweep: 10, 20, 30, 40, 50 nodes
  - Speed sweep: 5, 10, 15, 20, 25 m/s
  - Alpha sweep: 0.01, 0.05, 0.10, 0.20
  - Horizon sweep: 1, 2, 3, 5 s
  - 5 matched seeds per configuration
"""
import subprocess, os, sys, time
from pathlib import Path

EXE = Path(r"./ns3 run rvc-fanet-sim")
PROJECT = Path(r".")
# ns-3 std::ofstream cannot handle spaces in paths, so we use a staging path
CSV_STAGING = Path(r"./results/staging/stage2_experiment_matrix.csv")
CSV_FINAL = PROJECT / "results" / "raw" / "stage2_experiment_matrix.csv"

env = os.environ.copy()
env["PATH"] = env.get("PATH", "")

# Remove old staging CSV to start fresh
if CSV_STAGING.exists():
    CSV_STAGING.unlink()

def run_sim(protocol, num_nodes, sim_time, speed, tx_range, h_req, alpha, seed):
    cmd = [str(EXE),
           f"--protocol={protocol}",
           f"--numNodes={num_nodes}",
           f"--simTime={sim_time}",
           f"--nodeSpeed={speed}",
           f"--txRange={tx_range}",
           f"--hReq={h_req}",
           f"--alphaRoute={alpha}",
           f"--seed={seed}",
           f"--csvFileName={CSV_STAGING}",
           f"--calibFile=./results/raw/nominal_residuals.txt"]
    try:
        r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=180)
        return r.returncode == 0
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def main():
    protocols = ["AODV", "PPR", "RVC"]
    seeds = [42, 101, 202, 303, 404]
    sim_time = 60.0
    tx_range = 250.0

    # Default parameters
    default_nodes = 30
    default_speed = 15.0
    default_h = 3.0
    default_alpha = 0.10

    # Sweep configs
    density_nodes = [10, 20, 30, 40, 50]
    speeds = [5.0, 10.0, 15.0, 20.0, 25.0]
    alphas = [0.01, 0.05, 0.10, 0.20]
    horizons = [1.0, 2.0, 3.0, 5.0]

    total = (len(protocols) * len(density_nodes) * len(seeds) +
             len(protocols) * len(speeds) * len(seeds) +
             len(protocols) * len(alphas) * len(seeds) +
             len(protocols) * len(horizons) * len(seeds))

    print(f"{'='*60}")
    print(f" Stage 2: Corrected Experiment Matrix")
    print(f" Total Runs: {total}")
    print(f" Output: {CSV_FINAL}")
    print(f"{'='*60}")

    count = 0
    start = time.time()

    # Sweep 1: Density
    print("\n--- Density Sweep ---")
    for n in density_nodes:
        for proto in protocols:
            for s in seeds:
                count += 1
                print(f"[{count}/{total}] {proto} | N={n} | seed={s}...", end=" ", flush=True)
                ok = run_sim(proto, n, sim_time, default_speed, tx_range, default_h, default_alpha, s)
                print("OK" if ok else "FAIL")

    # Sweep 2: Speed
    print("\n--- Speed Sweep ---")
    for sp in speeds:
        for proto in protocols:
            for s in seeds:
                count += 1
                print(f"[{count}/{total}] {proto} | v={sp}m/s | seed={s}...", end=" ", flush=True)
                ok = run_sim(proto, default_nodes, sim_time, sp, tx_range, default_h, default_alpha, s)
                print("OK" if ok else "FAIL")

    # Sweep 3: Alpha
    print("\n--- Alpha Sweep ---")
    for a in alphas:
        for proto in protocols:
            for s in seeds:
                count += 1
                print(f"[{count}/{total}] {proto} | a={a} | seed={s}...", end=" ", flush=True)
                ok = run_sim(proto, default_nodes, sim_time, default_speed, tx_range, default_h, a, s)
                print("OK" if ok else "FAIL")

    # Sweep 4: Horizon
    print("\n--- Horizon Sweep ---")
    for h in horizons:
        for proto in protocols:
            for s in seeds:
                count += 1
                print(f"[{count}/{total}] {proto} | H={h}s | seed={s}...", end=" ", flush=True)
                ok = run_sim(proto, default_nodes, sim_time, default_speed, tx_range, h, default_alpha, s)
                print("OK" if ok else "FAIL")

    elapsed = time.time() - start

    # Copy results from staging to D: drive
    import shutil
    shutil.copy2(str(CSV_STAGING), str(CSV_FINAL))
    print(f"\n{'='*60}")
    print(f" COMPLETE: {count}/{total} runs in {elapsed:.0f}s")
    print(f" Staging: {CSV_STAGING}")
    print(f" Final:   {CSV_FINAL}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
