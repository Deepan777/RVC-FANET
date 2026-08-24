import pandas as pd

CSV_PATH = r"D:\VIT Vellore Research one\FANET\results\raw\stage2_experiment_matrix.csv"
df = pd.read_csv(CSV_PATH)

# Function to format dataframe
def format_df(df_grouped):
    # Select relevant columns and round
    cols = ['protocol', 'pdr', 'conditionalPdr', 'reachabilityRatio', 'avgDelayMs', 'contractsCreated', 'rreqsPruned']
    return df_grouped[cols].round(2).to_markdown(index=False)

print("### 1. Full Density Sweep Results (Speed = 15 m/s, H = 3s, alpha = 0.1)")
for nodes in sorted(df['numNodes'].unique()):
    if nodes != 30: # We already showed 30 in the summary, but let's show all
        pass
    subset = df[(df['nodeSpeed'] == 15.0) & (df['hReq'] == 3.0) & (df['alphaRoute'] == 0.1) & (df['numNodes'] == nodes)]
    if not subset.empty:
        print(f"\n#### Density: {nodes} UAVs")
        print(format_df(subset.groupby('protocol').mean(numeric_only=True).reset_index()))

print("\n### 2. Full Speed Sweep Results (Nodes = 30, H = 3s, alpha = 0.1)")
for speed in sorted(df['nodeSpeed'].unique()):
    subset = df[(df['numNodes'] == 30) & (df['hReq'] == 3.0) & (df['alphaRoute'] == 0.1) & (df['nodeSpeed'] == speed)]
    if not subset.empty:
        print(f"\n#### Speed: {speed} m/s")
        print(format_df(subset.groupby('protocol').mean(numeric_only=True).reset_index()))

print("\n### 3. Full Risk Budget (Alpha) Sweep Results (Nodes = 30, Speed = 15 m/s, H = 3s)")
for alpha in sorted(df['alphaRoute'].unique()):
    subset = df[(df['numNodes'] == 30) & (df['nodeSpeed'] == 15.0) & (df['hReq'] == 3.0) & (df['alphaRoute'] == alpha)]
    if not subset.empty:
        print(f"\n#### Alpha: {alpha}")
        print(format_df(subset.groupby('protocol').mean(numeric_only=True).reset_index()))

print("\n### 4. Full Horizon (H) Sweep Results (Nodes = 30, Speed = 15 m/s, alpha = 0.1)")
for h in sorted(df['hReq'].unique()):
    subset = df[(df['numNodes'] == 30) & (df['nodeSpeed'] == 15.0) & (df['alphaRoute'] == 0.1) & (df['hReq'] == h)]
    if not subset.empty:
        print(f"\n#### Horizon: {h} seconds")
        print(format_df(subset.groupby('protocol').mean(numeric_only=True).reset_index()))
