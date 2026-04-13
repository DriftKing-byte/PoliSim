delta_tbl = pd.DataFrame(delta_rows).sort_values("delta_recall_mean", ascending=False)
print("\nPaired deltas vs control:")
display(delta_tbl)

# ---- Figure: delta recall with CI
if len(delta_tbl) > 0:
    x = np.arange(len(delta_tbl))
    y = delta_tbl["delta_recall_mean"].values
    yerr = np.vstack([
        y - delta_tbl["delta_recall_ci_lo"].values,
        delta_tbl["delta_recall_ci_hi"].values - y
    ])
    plt.figure()
    plt.bar(x, y)
    plt.errorbar(x, y, yerr=yerr, fmt="none", capsize=3)
    plt.xticks(x, delta_tbl["variant_id"].values, rotation=30, ha="right")
    plt.ylabel("Δ Action recall vs control")
    plt.title("Paired Δ Action Recall (bootstrap CI)")
    plt.tight_layout()
    plt.show()


