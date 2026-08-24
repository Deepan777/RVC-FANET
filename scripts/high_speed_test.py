import subprocess, os

EXE = r"C:\Users\deepa\.gemini\antigravity-ide\scratch\ns-allinone-3.41\ns-3.41\build\scratch\ns3.41-rvc-fanet-sim.exe"
env = os.environ.copy()
env["PATH"] = r"C:\msys64\mingw64\bin;" + r"C:\Users\deepa\.gemini\antigravity-ide\scratch\ns-allinone-3.41\ns-3.41\build\lib;" + env.get("PATH", "")

for proto in ["AODV", "PPR", "RVC"]:
    print(f"\nTesting {proto} at 30 m/s")
    cmd = [EXE, f"--protocol={proto}", "--numNodes=20", "--simTime=40", "--nodeSpeed=30", "--hReq=3", "--alphaRoute=0.1"]
    r = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if r.returncode != 0:
        print("FAILED", r.stderr)
    else:
        print(r.stdout[-1500:])
