import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv('./results/raw/stage2_experiment_matrix.csv')

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
palette = {'AODV': 'grey', 'PPR': 'blue', 'RVC': 'green'}

# Panel A: Absolute PDR
sns.lineplot(data=df, x='numNodes', y='pdr', hue='protocol', palette=palette, marker='o', ax=axes[0], errorbar=('ci', 95))
axes[0].set_title('A: Absolute PDR vs Network Density')
axes[0].set_xlabel('Number of UAVs')
axes[0].set_ylabel('Absolute Packet Delivery Ratio')
axes[0].set_xticks([10, 20, 30, 40, 50])
axes[0].grid(True, linestyle=':', alpha=0.7)

# Panel B: Conditional PDR
sns.lineplot(data=df, x='numNodes', y='conditionalPdr', hue='protocol', palette=palette, marker='o', ax=axes[1], errorbar=('ci', 95))
axes[1].set_title('B: Conditional PDR vs Network Density')
axes[1].set_xlabel('Number of UAVs')
axes[1].set_ylabel('Conditional Packet Delivery Ratio')
axes[1].set_xticks([10, 20, 30, 40, 50])
axes[1].grid(True, linestyle=':', alpha=0.7)

plt.tight_layout()
plt.savefig('./figures/FINAL_NETWORK_DENSITY.pdf', dpi=300)
print("Saved FINAL_NETWORK_DENSITY.pdf")
