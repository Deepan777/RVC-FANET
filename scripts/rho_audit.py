import numpy as np

# Simulate the logic of LinkRiskEstimator from C++
scores = np.random.uniform(0.1, 0.4, 30) # 1-step residuals
scores.sort()
n = len(scores)

txRange = 250.0

def compute_rho(max_dist):
    margin = txRange - max_dist
    if margin < 0:
        return 1.0
        
    kMax = -1
    for i in range(n):
        if scores[i] <= margin:
            kMax = i
        else:
            break
            
    if kMax < 0:
        return 1.0
        
    rho = 1.0 - (kMax + 1) / (n + 1)
    return max(0.0, rho)

for max_dist in [100.0, 200.0, 240.0, 249.0, 249.7, 251.0]:
    print(f"Max Dist: {max_dist}m -> Margin: {txRange - max_dist:.2f}m -> Rho: {compute_rho(max_dist):.4f}")
