import subprocess, os, time
from pathlib import Path

EXE = Path(r"C:\Users\deepa\.gemini\antigravity-ide\scratch\ns-allinone-3.41\ns-3.41\build\scratch\ns3.41-rvc-fanet-sim.exe")
PROJECT = Path(r"D:\VIT Vellore Research one\FANET")
CSV_FINAL = PROJECT / "results" / "empirical_calibration_stage2" / "raw" / "stage2_abrupt.csv"
CSV_STAGING = Path(r"C:\Users\deepa\.gemini\antigravity-ide\scratch\stage2_abrupt.csv")

env = os.environ.copy()
env["PATH"] = r"C:\msys64\mingw64\bin;" + r"C:\Users\deepa\.gemini\antigravity-ide\scratch\ns-allinone-3.41\ns-3.41\build\lib;" + env.get("PATH", "")

if CSV_STAGING.exists():
    CSV_STAGING.unlink()

def run_sim(protocol, hReq, seed):
    cmd = [
        str(EXE),
        f"--protocol={protocol}",
        f"--numNodes=30",
        f"--simTime=60",
        f"--nodeSpeed=15.0",
        f"--txRange=250",
        f"--hReq={hReq}",
        f"--alphaRoute=0.10",
        f"--seed={seed}",
        f"--csvFileName={CSV_STAGING}",
        f"--calibFile=results/raw/nominal_residuals_15.txt",
        f"--abruptShift=true"
    ]
    try:
        r = subprocess.run(cmd, env=env, capture_output=True, text=True, cwd=str(PROJECT), timeout=120)
        return r.returncode == 0
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def main():
    protocols = ["PPR", "RVC"]
    horizons = [1.0, 3.0, 5.0]
    seeds = list(range(1, 31))
    
    total = len(protocols) * len(horizons) * len(seeds)
    print(f"============================================================")
    print(f" Stage 2 Abrupt Mobility Stress Test")
    print(f" Total Runs: {total}")
    print(f" Output: {CSV_FINAL}")
    print(f"============================================================")
    
    count = 0
    start = time.time()
    for h in horizons:
        for proto in protocols:
            for s in seeds:
                count += 1
                print(f"[{count}/{total}] {proto} | H={h} | seed={s}...", end=" ", flush=True)
                ok = run_sim(proto, h, s)
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
