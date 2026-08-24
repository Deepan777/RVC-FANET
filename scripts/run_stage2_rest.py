import subprocess, os, time
from pathlib import Path

EXE = Path(r"C:\Users\deepa\.gemini\antigravity-ide\scratch\ns-allinone-3.41\ns-3.41\build\scratch\ns3.41-rvc-fanet-sim.exe")
PROJECT = Path(r"D:\VIT Vellore Research one\FANET")
# We now dynamically select the calibration file based on speed
# to ensure valid empirical conformal bounds.
CSV_FINAL = PROJECT / "results" / "empirical_calibration_stage2" / "raw" / "stage2_rest.csv"
CSV_STAGING = Path(r"C:\Users\deepa\.gemini\antigravity-ide\scratch\stage2_rest.csv")

env = os.environ.copy()
env["PATH"] = r"C:\msys64\mingw64\bin;" + r"C:\Users\deepa\.gemini\antigravity-ide\scratch\ns-allinone-3.41\ns-3.41\build\lib;" + env.get("PATH", "")

if CSV_STAGING.exists():
    CSV_STAGING.unlink()

def run_sim(protocol, speed, seed, alpha, nodes):
    cmd = [
        str(EXE),
        f"--protocol={protocol}",
        f"--numNodes={nodes}",
        f"--simTime=15",
        f"--nodeSpeed={speed}",
        f"--txRange=250",
        f"--hReq=3",
        f"--alphaRoute={alpha}",
        f"--seed={seed}",
        f"--csvFileName={CSV_STAGING}",
        f"--calibFile=results/raw/nominal_residuals_{int(speed)}.txt"
    ]
    try:
        r = subprocess.run(cmd, env=env, capture_output=True, text=True, cwd=str(PROJECT), timeout=120)
        return r.returncode == 0
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def main():
    speeds = [5.0]
    seeds = list(range(1, 31))
    
    # 1. Alpha Sweep
    alphas = [0.05, 0.10, 0.15, 0.20, 0.30]
    
    # 2. Density Sweep
    densities = [10, 20, 30, 40, 50]
    
    total = (len(alphas) * len(seeds)) + (2 * len(densities) * len(seeds))
    print(f"============================================================")
    print(f" Stage 2 Rest: Alpha and Density Sweeps")
    print(f" Total Runs: {total}")
    print(f" Output: {CSV_FINAL}")
    print(f"============================================================")
    
    count = 0
    start = time.time()
    
    # Alpha sweep
    print("--- Running Alpha Sweep ---")
    for a in alphas:
        for s in seeds:
            count += 1
            print(f"[{count}/{total}] RVC | alpha={a} | seed={s}...", end=" ", flush=True)
            ok = run_sim("RVC", 5.0, s, a, 30)
            print("OK" if ok else "FAIL")
            
    # Density sweep
    print("--- Running Density Sweep ---")
    for d in densities:
        for proto in ["PPR", "RVC"]:
            for s in seeds:
                count += 1
                print(f"[{count}/{total}] {proto} | nodes={d} | seed={s}...", end=" ", flush=True)
                ok = run_sim(proto, 5.0, s, 0.10, d)
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
