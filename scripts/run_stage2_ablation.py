import subprocess, os, time
from pathlib import Path

EXE = Path(r"C:\Users\deepa\.gemini\antigravity-ide\scratch\ns-allinone-3.41\ns-3.41\build\scratch\ns3.41-rvc-fanet-sim.exe")
PROJECT = Path(r"D:\VIT Vellore Research one\FANET")
# We now dynamically select the calibration file based on speed
# to ensure valid empirical conformal bounds.
CSV_FINAL = PROJECT / "results" / "empirical_calibration_stage2" / "raw" / "stage2_ablation.csv"
CSV_STAGING = Path(r"C:\Users\deepa\.gemini\antigravity-ide\scratch\stage2_ablation.csv")

env = os.environ.copy()
env["PATH"] = r"C:\msys64\mingw64\bin;" + r"C:\Users\deepa\.gemini\antigravity-ide\scratch\ns-allinone-3.41\ns-3.41\build\lib;" + env.get("PATH", "")

if CSV_STAGING.exists():
    CSV_STAGING.unlink()

def run_sim(ablation, seed):
    # A0 is PPR, A1-A3 are RVC with different ablation modes
    protocol = "PPR" if ablation == "A0" else "RVC"
    ablMode = ablation if ablation != "A0" else "A3" # default A3 for PPR (ignored)
    speed = 5
    cmd = [
        str(EXE),
        f"--protocol={protocol}",
        f"--numNodes=30",
        f"--simTime=15",
        f"--nodeSpeed={speed}",
        f"--txRange=250",
        f"--hReq=3",
        f"--alphaRoute=0.10",
        f"--seed={seed}",
        f"--csvFileName={CSV_STAGING}",
        f"--calibFile=results/raw/nominal_residuals_{int(speed)}.txt",
        f"--ablationMode={ablMode}"
    ]
    try:
        r = subprocess.run(cmd, env=env, capture_output=True, text=True, cwd=str(PROJECT), timeout=120)
        return r.returncode == 0
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def main():
    ablations = ["A0", "A1", "A2", "A3"]
    seeds = range(1, 31)

    total_runs = len(ablations) * len(seeds)
    print("=" * 60)
    print(" Stage 2: Component Ablation (Empirical Calib)")
    print(f" Total Runs: {total_runs}")
    print(f" Output: {CSV_FINAL}")
    print("=" * 60)

    run_idx = 0
    for abl in ablations:
        for seed in seeds:
            run_idx += 1
            print(f"[{run_idx}/{total_runs}] {abl} | seed={seed}... ", end="", flush=True)
            ok = run_sim(abl, seed)
            print("OK" if ok else "FAIL")
                
    # Copy staging to final
    import shutil
    if CSV_STAGING.exists():
        shutil.copy2(CSV_STAGING, CSV_FINAL)
        print(f"Results copied to {CSV_FINAL}")
    else:
        print("Results file was not created!")

    elapsed = time.time() - start
    print(f"Total Time: {elapsed:.1f}s")

if __name__ == "__main__":
    main()
