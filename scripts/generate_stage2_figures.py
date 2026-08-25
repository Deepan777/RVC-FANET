import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import os

PROJECT = Path(r".")
CSV_PATH = PROJECT / "results" / "raw" / "stage2_experiment_matrix.csv"
FIG_PNG = PROJECT / "figures" / "png"
FIG_PDF = PROJECT / "figures" / "pdf"
FIG_SVG = PROJECT / "figures" / "svg"

for d in [FIG_PNG, FIG_PDF, FIG_SVG]:
    os.makedirs(d, exist_ok=True)

def save_fig(fig, name):
    fig.savefig(FIG_PNG / f"{name}.png", dpi=300, bbox_inches='tight')
    fig.savefig(FIG_PDF / f"{name}.pdf", bbox_inches='tight')
    fig.savefig(FIG_SVG / f"{name}.svg", bbox_inches='tight')
    plt.close(fig)

def main():
    if not CSV_PATH.exists():
        print("Data not ready yet.")
        return
        
    df = pd.read_csv(CSV_PATH)
    
    sns.set_theme(style="whitegrid", context="paper", font_scale=1.2)
    palette = {"AODV": "#e74c3c", "PPR": "#f39c12", "RVC": "#2ecc71"}

    # FIGURE 2 & 3: PDR vs Density
    # Filter to default speed (15), default H (3), default alpha (0.1)
    df_dens = df[(df['nodeSpeed'] == 15.0) & (df['hReq'] == 3.0) & (df['alphaRoute'] == 0.1)]
    
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.lineplot(data=df_dens, x='numNodes', y='pdr', hue='protocol', marker='o', palette=palette, ax=ax)
    ax.set_title("Absolute PDR vs Network Density")
    ax.set_ylabel("Packet Delivery Ratio")
    ax.set_xlabel("Number of UAVs")
    save_fig(fig, "fig2_pdr_vs_density")
    
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.lineplot(data=df_dens, x='numNodes', y='conditionalPdr', hue='protocol', marker='s', palette=palette, ax=ax)
    ax.set_title("Conditional PDR vs Network Density")
    ax.set_ylabel("Conditional PDR (when path exists)")
    ax.set_xlabel("Number of UAVs")
    save_fig(fig, "fig3_conditional_pdr_vs_density")
    
    # FIGURE 4 & 5: PDR vs Speed
    df_speed = df[(df['numNodes'] == 30) & (df['hReq'] == 3.0) & (df['alphaRoute'] == 0.1)]
    
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.lineplot(data=df_speed, x='nodeSpeed', y='pdr', hue='protocol', marker='o', palette=palette, ax=ax)
    ax.set_title("Absolute PDR vs Mobility Speed")
    ax.set_ylabel("Packet Delivery Ratio")
    ax.set_xlabel("Mean UAV Speed (m/s)")
    save_fig(fig, "fig4_pdr_vs_speed")
    
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.lineplot(data=df_speed, x='nodeSpeed', y='conditionalPdr', hue='protocol', marker='s', palette=palette, ax=ax)
    ax.set_title("Conditional PDR vs Mobility Speed")
    ax.set_ylabel("Conditional PDR (when path exists)")
    ax.set_xlabel("Mean UAV Speed (m/s)")
    save_fig(fig, "fig5_conditional_pdr_vs_speed")

    # FIGURE 9: Alpha vs Admissions/Pruning
    df_alpha = df[(df['numNodes'] == 30) & (df['nodeSpeed'] == 15.0) & (df['hReq'] == 3.0) & (df['protocol'] == 'RVC')]
    if not df_alpha.empty:
        fig, ax1 = plt.subplots(figsize=(7, 5))
        ax2 = ax1.twinx()
        sns.lineplot(data=df_alpha, x='alphaRoute', y='contractsCreated', color='g', marker='o', ax=ax1, label='Contracts Admitted')
        sns.lineplot(data=df_alpha, x='alphaRoute', y='rreqsPruned', color='r', marker='x', ax=ax2, label='Routes Pruned')
        ax1.set_xlabel("Requested Risk Budget (\u03B1)")
        ax1.set_ylabel("Contracts Admitted", color='g')
        ax2.set_ylabel("Risky Routes Pruned", color='r')
        ax1.set_title("RVC Route Admission vs Risk Budget")
        # Combine legends
        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax2.legend(lines + lines2, labels + labels2, loc='upper left')
        save_fig(fig, "fig9_alpha_admissions_pruning")

    # FIGURE 19: Delay vs Delivery Operating Point (Delay vs CondPDR)
    fig, ax = plt.subplots(figsize=(7, 5))
    df_dens_mean = df_dens.groupby('protocol').mean(numeric_only=True).reset_index()
    sns.scatterplot(data=df_dens_mean, x='avgDelayMs', y='conditionalPdr', hue='protocol', s=200, palette=palette, ax=ax)
    ax.set_title("Delivery vs Delay Operating Point (N=30)")
    ax.set_xlabel("Average End-to-End Delay (ms)")
    ax.set_ylabel("Conditional PDR")
    save_fig(fig, "fig19_delay_vs_delivery")

    print("Figures 2, 3, 4, 5, 9, 19 generated.")

if __name__ == "__main__":
    main()
