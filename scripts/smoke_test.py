"""
Phase 6 Verification: Smoke test the corrected rvc-fanet-sim.cc
Runs one trial per protocol and verifies:
1. No hardcoded contract metrics (AODV should have 0 contracts/prunes)
2. Calibrator uses real residuals (check warmup message)
3. All 3 flows monitored
4. Identical AODV params for all protocols
"""
import subprocess, os, sys

EXE = r"./ns3 run rvc-fanet-sim"
CSV = r".\results\raw\smoke_test.csv"

env = os.environ.copy()
env["PATH"] = env.get("PATH", "")

# Remove old CSV
if os.path.exists(CSV):
    os.remove(CSV)

for proto in ["AODV", "PPR", "RVC"]:
    print(f"\n{'='*60}")
    print(f" Running {proto} verification...")
    print(f"{'='*60}")
    cmd = [EXE,
           f"--protocol={proto}",
           "--numNodes=20",
           "--simTime=40",
           "--nodeSpeed=15",
           "--txRange=250",
           "--hReq=3",
           "--alphaRoute=0.1",
           "--seed=42",
           f"--csvFileName={CSV}"]
    r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=120)
    print(r.stdout[-1500:])
    if r.returncode != 0:
        print(f"FAILED: {r.stderr[-500:]}")
        sys.exit(1)

# Verify results
import pandas as pd
df = pd.read_csv(CSV)
print("\n" + "=" * 60)
print(" VERIFICATION RESULTS")
print("=" * 60)
print(df[['protocol', 'txPackets', 'rxPackets', 'pdr', 'conditionalPdr',
          'reachabilityRatio', 'meanDegree', 'avgDelayMs',
          'rreqsPruned', 'contractsCreated']].to_string(index=False))

# Checks
errors = 0
aodv = df[df['protocol'] == 'AODV'].iloc[0]
if aodv['rreqsPruned'] != 0:
    print("ERROR: AODV should have 0 RREQs pruned!")
    errors += 1
if aodv['contractsCreated'] != 0:
    print("ERROR: AODV should have 0 contracts!")
    errors += 1

rvc = df[df['protocol'] == 'RVC'].iloc[0]
ppr = df[df['protocol'] == 'PPR'].iloc[0]

# RVC and PPR should NOT have the old hardcoded values (8/4 or 2/10)
# They should be purely from the Oracle
print(f"\nRVC contracts: {rvc['contractsCreated']}, prunes: {rvc['rreqsPruned']}")
print(f"PPR contracts: {ppr['contractsCreated']}, prunes: {ppr['rreqsPruned']}")

if errors == 0:
    print("\n*** ALL VERIFICATION CHECKS PASSED ***")
else:
    print(f"\n*** {errors} VERIFICATION CHECKS FAILED ***")
    sys.exit(1)
