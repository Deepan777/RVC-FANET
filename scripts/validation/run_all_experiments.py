"""
RVC-FANET Strengthening Validation — Unified Experiment Runner
Executes all 6 tasks sequentially using the instrumented ns-3 simulation.
All outputs go to .\
"""
import subprocess, os, sys, time, json
from pathlib import Path
import shutil

EXE = Path(r"./ns3 run rvc-fanet-sim")
PROJECT = Path(r".")
# Staging area (no spaces in path for ns-3 ofstream)
STAGING = Path(r"./results/validation")

env = os.environ.copy()
env["PATH"] = env.get("PATH", "")

SEEDS = list(range(1, 31))  # 30 matched seeds

def ensure_dirs():
    for d in ["task1", "task2", "task3", "task4", "task5", "task6"]:
        (STAGING / d).mkdir(parents=True, exist_ok=True)
    (PROJECT / "results" / "strengthening_stage").mkdir(parents=True, exist_ok=True)

def run_sim(protocol, num_nodes, sim_time, speed, tx_range, h_req, alpha, seed,
            csv_path, contracts_csv="", mobility_shift=False):
    cmd = [str(EXE),
           f"--protocol={protocol}",
           f"--numNodes={num_nodes}",
           f"--simTime={sim_time}",
           f"--nodeSpeed={speed}",
           f"--txRange={tx_range}",
           f"--hReq={h_req}",
           f"--alphaRoute={alpha}",
           f"--seed={seed}",
           f"--csvFileName={csv_path}"]
    if contracts_csv:
        cmd.append(f"--contractsCsv={contracts_csv}")
    if mobility_shift:
        cmd.append("--mobilityShift=true")
    try:
        r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=300)
        return r.returncode == 0, r.stdout
    except Exception as e:
        return False, str(e)

def copy_to_project(src, dst_relative):
    dst = PROJECT / dst_relative
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(src), str(dst))

# ================================================================
# TASK 1: Alpha vs CVR
# ================================================================
def run_task1():
    print("\n" + "="*70)
    print(" TASK 1: Requested Alpha vs Observed CVR")
    print("="*70)
    
    alphas = [0.01, 0.05, 0.10, 0.20, 0.50]
    csv = STAGING / "task1" / "alpha_vs_cvr.csv"
    contracts_csv = STAGING / "task1" / "alpha_vs_cvr_contracts.csv"
    
    for f in [csv, contracts_csv]:
        if f.exists(): f.unlink()
    
    total = len(alphas) * len(SEEDS) * 3  # AODV + PPR + RVC
    count = 0
    
    for alpha in alphas:
        for proto in ["AODV", "PPR", "RVC"]:
            for seed in SEEDS:
                count += 1
                print(f"[{count}/{total}] {proto} a={alpha} seed={seed}...", end=" ", flush=True)
                ok, _ = run_sim(proto, 30, 60, 15, 250, 3, alpha, seed, str(csv), str(contracts_csv))
                print("OK" if ok else "FAIL")
    
    copy_to_project(csv, "results/strengthening_stage/task1_alpha_vs_cvr.csv")
    copy_to_project(contracts_csv, "results/strengthening_stage/task1_contracts.csv")
    print(f"Task 1 complete: {count} runs")

# ================================================================
# TASK 2: PPR vs RVC Matched Comparison
# ================================================================
def run_task2():
    print("\n" + "="*70)
    print(" TASK 2: PPR vs RVC Matched Comparison")
    print("="*70)
    
    speeds = [5, 15, 25]
    csv = STAGING / "task2" / "ppr_vs_rvc.csv"
    contracts_csv = STAGING / "task2" / "ppr_vs_rvc_contracts.csv"
    
    for f in [csv, contracts_csv]:
        if f.exists(): f.unlink()
    
    total = len(speeds) * len(SEEDS) * 3  # AODV + PPR + RVC
    count = 0
    
    for speed in speeds:
        for proto in ["AODV", "PPR", "RVC"]:
            for seed in SEEDS:
                count += 1
                print(f"[{count}/{total}] {proto} v={speed} seed={seed}...", end=" ", flush=True)
                ok, _ = run_sim(proto, 30, 60, speed, 250, 3, 0.10, seed, str(csv), str(contracts_csv))
                print("OK" if ok else "FAIL")
    
    copy_to_project(csv, "results/strengthening_stage/task2_ppr_vs_rvc.csv")
    copy_to_project(contracts_csv, "results/strengthening_stage/task2_contracts.csv")
    print(f"Task 2 complete: {count} runs")

# ================================================================
# TASK 3: Packet Loss Root-Cause
# ================================================================
def run_task3():
    print("\n" + "="*70)
    print(" TASK 3: Packet Loss Root-Cause Decomposition")
    print("="*70)
    
    speeds = [5, 15, 25]
    csv = STAGING / "task3" / "packet_loss.csv"
    
    if csv.exists(): csv.unlink()
    
    total = len(speeds) * 20 * 3
    count = 0
    
    for speed in speeds:
        for proto in ["AODV", "PPR", "RVC"]:
            for seed in SEEDS[:20]:
                count += 1
                print(f"[{count}/{total}] {proto} v={speed} seed={seed}...", end=" ", flush=True)
                ok, _ = run_sim(proto, 30, 60, speed, 250, 3, 0.10, seed, str(csv))
                print("OK" if ok else "FAIL")
    
    copy_to_project(csv, "results/strengthening_stage/task3_packet_loss.csv")
    print(f"Task 3 complete: {count} runs")

# ================================================================
# TASK 4: A0-A3 Core Ablation
# ================================================================
def run_task4():
    print("\n" + "="*70)
    print(" TASK 4: A0-A3 Core Ablation")
    print("="*70)
    
    protocols = ["PPR", "A1", "A2", "RVC"]  # A0=PPR, A3=RVC
    csv = STAGING / "task4" / "ablation.csv"
    contracts_csv = STAGING / "task4" / "ablation_contracts.csv"
    
    for f in [csv, contracts_csv]:
        if f.exists(): f.unlink()
    
    total = len(protocols) * len(SEEDS)
    count = 0
    
    for proto in protocols:
        for seed in SEEDS:
            count += 1
            print(f"[{count}/{total}] {proto} seed={seed}...", end=" ", flush=True)
            ok, _ = run_sim(proto, 30, 60, 15, 250, 3, 0.10, seed, str(csv), str(contracts_csv))
            print("OK" if ok else "FAIL")
    
    copy_to_project(csv, "results/strengthening_stage/task4_ablation.csv")
    copy_to_project(contracts_csv, "results/strengthening_stage/task4_contracts.csv")
    print(f"Task 4 complete: {count} runs")

# ================================================================
# TASK 5: Contract Slack Early Warning (uses Task 1/2 contract data)
# ================================================================
def run_task5():
    print("\n" + "="*70)
    print(" TASK 5: Contract Slack Early Warning")
    print("="*70)
    # Task 5 analysis is done in post-processing from Task 1/2 contract records
    # We also need a comparison: RVC vs RVC-NoRevalidation
    # For now the Oracle approach doesn't have revalidation, so we just analyze slack
    print("Task 5 uses contract records from Tasks 1/2/4 — will analyze in post-processing")

# ================================================================
# TASK 6: Abrupt Mobility Robustness
# ================================================================
def run_task6():
    print("\n" + "="*70)
    print(" TASK 6: Abrupt Mobility Robustness")
    print("="*70)
    
    csv = STAGING / "task6" / "abrupt_mobility.csv"
    contracts_csv = STAGING / "task6" / "abrupt_contracts.csv"
    
    for f in [csv, contracts_csv]:
        if f.exists(): f.unlink()
    
    total = 20 * 3 * 2  # 20 seeds x 3 protocols x 2 modes (normal + shift)
    count = 0
    
    for shift in [False, True]:
        for proto in ["AODV", "PPR", "RVC"]:
            for seed in SEEDS[:20]:
                count += 1
                label = "shift" if shift else "normal"
                print(f"[{count}/{total}] {proto} {label} seed={seed}...", end=" ", flush=True)
                ok, _ = run_sim(proto, 30, 60, 15, 250, 3, 0.10, seed,
                               str(csv), str(contracts_csv), mobility_shift=shift)
                print("OK" if ok else "FAIL")
    
    copy_to_project(csv, "results/strengthening_stage/task6_abrupt_mobility.csv")
    copy_to_project(contracts_csv, "results/strengthening_stage/task6_contracts.csv")
    print(f"Task 6 complete: {count} runs")

# ================================================================
# MAIN
# ================================================================
def main():
    ensure_dirs()
    
    start = time.time()
    
    run_task1()
    run_task2()
    run_task3()
    run_task4()
    run_task5()
    run_task6()
    
    elapsed = time.time() - start
    print(f"\n{'='*70}")
    print(f" ALL EXPERIMENTS COMPLETE in {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
