import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

sns.set_theme(style="whitegrid")

# ==============================================================================
# FIGURE 2: RISK BUDGET
# ==============================================================================
fig2, axes2 = plt.subplots(1, 2, figsize=(14, 5))

alpha = ['0.05', '0.10', '0.15', '0.20', '0.30']
cvr = [0.0, 0.0, 0.0, 0.0, 0.0] 
# Based on manuscript TOTAL counts across 30 seeds
admitted = [583, 632, 660, 666, 679] 
pruned = [867, 818, 790, 784, 771]

axes2[0].plot(alpha, cvr, marker='o', color='red', linewidth=2)
axes2[0].set_title('A: Contract Violation Rate (CVR) vs Risk Budget')
axes2[0].set_xlabel(r'Route Risk Budget ($\alpha_{\mathrm{route}}$)')
axes2[0].set_ylabel('Observed Finite-Horizon Route Failure Rate')
axes2[0].set_ylim(-0.01, 0.1)

x = np.arange(len(alpha))
width = 0.35
axes2[1].bar(x - width/2, admitted, width, label='Admitted Contracts', color='blue')
axes2[1].bar(x + width/2, pruned, width, label='Pruned Candidates', color='orange')
axes2[1].set_title('B: Route Discovery Selectivity')
axes2[1].set_xlabel(r'Route Risk Budget ($\alpha_{\mathrm{route}}$)')
axes2[1].set_ylabel('Total Routes')
axes2[1].set_xticks(x)
axes2[1].set_xticklabels(alpha)
axes2[1].legend()

plt.tight_layout()
fig2.savefig('D:/VIT Vellore Research one/FANET/figures/FINAL_RISK_BUDGET_MULTIPANEL.pdf', dpi=300)
print("Saved Figure 2.")

# ==============================================================================
# FIGURE 3: ABLATION
# ==============================================================================
fig3, axes3 = plt.subplots(2, 2, figsize=(14, 10))

variants = ['A0 (PPR)', 'A1 (Conf)', 'A2 (Unif)', 'A3 (RVC)']
admissions = [1236, 634, 601, 632]
fhr = [0.0638, 0.0, 0.0, 0.0]

# Verified original ablation delay and PDR values
pdr = [0.211338, 0.198289, 0.222556, 0.199328]
delay = [148.052, 115.532, 115.465, 115.390]

axes3[0,0].bar(variants, admissions, color=['grey', 'lightblue', 'blue', 'darkblue'])
axes3[0,0].set_title('A: Route Admission')
axes3[0,0].set_ylabel('Total Admitted Routes')

axes3[0,1].bar(variants, fhr, color=['red', 'green', 'green', 'green'])
axes3[0,1].set_title('B: Finite-Horizon Route Failure Rate')
axes3[0,1].set_ylabel('Mean FHR')

axes3[1,0].bar(variants, pdr, color='purple')
axes3[1,0].set_title('C: Reachability-Normalized PDR (RN-PDR)')
axes3[1,0].set_ylabel('RN-PDR')
axes3[1,0].set_ylim(0.15, 0.25)

axes3[1,1].bar(variants, delay, color='orange')
axes3[1,1].set_title('D: Mean End-to-End Delay')
axes3[1,1].set_ylabel('Delay (ms)')

plt.tight_layout()
fig3.savefig('D:/VIT Vellore Research one/FANET/figures/FINAL_ABLATION_FIGURE.pdf', dpi=300)
print("Saved Figure 3.")

# ==============================================================================
# FIGURE 4: DENSITY (PPR vs RVC ONLY)
# ==============================================================================
fig4, axes4 = plt.subplots(1, 2, figsize=(14, 5))

df_density = pd.read_csv('D:/VIT Vellore Research one/FANET/results/raw/stage2_experiment_matrix.csv')
df_density = df_density[df_density['protocol'].isin(['PPR', 'RVC'])]
palette = {'PPR': 'blue', 'RVC': 'green'}

sns.lineplot(data=df_density, x='numNodes', y='pdr', hue='protocol', palette=palette, marker='o', ax=axes4[0], errorbar=('ci', 95))
axes4[0].set_title('A: Absolute PDR vs Network Density')
axes4[0].set_xlabel('Number of UAVs')
axes4[0].set_ylabel('Absolute Packet Delivery Ratio')
axes4[0].set_xticks([10, 20, 30, 40, 50])

sns.lineplot(data=df_density, x='numNodes', y='conditionalPdr', hue='protocol', palette=palette, marker='o', ax=axes4[1], errorbar=('ci', 95))
axes4[1].set_title('B: RN-PDR vs Network Density')
axes4[1].set_xlabel('Number of UAVs')
axes4[1].set_ylabel('Reachability-Normalized PDR')
axes4[1].set_xticks([10, 20, 30, 40, 50])

plt.tight_layout()
fig4.savefig('D:/VIT Vellore Research one/FANET/figures/fig4_density_with_baselines.png', dpi=300)
print("Saved Figure 4.")
