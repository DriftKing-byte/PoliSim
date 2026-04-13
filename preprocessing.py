# Build paired pivot: one row per (alert_id, agent_id)
pair_idx = ["alert_id", "agent_id"]
needed_cols = pair_idx + ["variant_id", "action_recall", "confused", "compliance_intent"]
pair_df = df[needed_cols].dropna(subset=["variant_id"]).copy()

# Pivot outcomes
pivot_recall = pair_df.pivot_table(index=pair_idx, columns="variant_id", values="action_recall", aggfunc="mean")
pivot_conf = pair_df.pivot_table(index=pair_idx, columns="variant_id", values="confused", aggfunc="mean")
pivot_comp = pair_df.pivot_table(index=pair_idx, columns="variant_id", values="compliance_intent", aggfunc="mean")

variants = [c for c in pivot_recall.columns if c != CONTROL_ID and c is not None]
delta_rows = []
for v in variants:
    if CONTROL_ID not in pivot_recall.columns:
        continue
    d_recall = pivot_recall[v] - pivot_recall[CONTROL_ID]
    d_conf = pivot_conf[v] - pivot_conf[CONTROL_ID] if (v in pivot_conf.columns and CONTROL_ID in pivot_conf.columns) else None
    d_comp = pivot_comp[v] - pivot_comp[CONTROL_ID] if (v in pivot_comp.columns and CONTROL_ID in pivot_comp.columns) else None

    m, lo, hi = bootstrap_ci(d_recall.dropna().values, seed=1)
    m2, lo2, hi2 = bootstrap_ci(d_conf.dropna().values, seed=2) if d_conf is not None else (np.nan, np.nan, np.nan)
    m3, lo3, hi3 = bootstrap_ci(d_comp.dropna().values, seed=3) if d_comp is not None else (np.nan, np.nan, np.nan)

    delta_rows.append({
        "variant_id": v,
        "delta_recall_mean": m, "delta_recall_ci_lo": lo, "delta_recall_ci_hi": hi,
        "delta_confused_mean": m2, "delta_confused_ci_lo": lo2, "delta_confused_ci_hi": hi2,
        "delta_compliance_mean": m3, "delta_compliance_ci_lo": lo3, "delta_compliance_ci_hi": hi3,
        "n_pairs": int(d_recall.dropna().shape[0]),
    })

# =========================
# 6) Failure-mode taxonomy from confusion_reason / needs_info
# =========================
def categorize_failure(reason, needs):
    txt = norm(reason) + " " + " ".join([norm(x) for x in (needs if isinstance(needs, list) else [])])
    if not txt.strip():
        return "none_reported"

    rules = [
        ("missing_location", ["where", "location", "area", "address", "which part"]),
        ("missing_timing", ["until when", "when", "time", "duration", "how long", "deadline"]),
        ("unclear_action_steps", ["what do i do", "steps", "how to", "instructions", "unclear", "not sure what"]),
        ("conflicting_info", ["conflict", "contradict", "both", "but also"]),
        ("jargon_or_terms", ["shelter in place", "advisory", "alert level", "acronym", "jargon"]),
        ("resource_constraints", ["no car", "cannot", "don't have", "no access", "childcare", "disabled"]),
        ("update_channel_unclear", ["where to check", "updates", "website", "link", "official"]),
    ]
    for label, kws in rules:
        if any(k in txt for k in kws):
            return label
    return "other"

df["failure_mode"] = df.apply(lambda r: categorize_failure(r["confusion_reason"], r["needs_info"]), axis=1)

failure_tbl = df.groupby(["variant_id", "failure_mode"]).size().reset_index(name="count")
failure_tbl["share"] = failure_tbl.groupby("variant_id")["count"].transform(lambda x: x / x.sum())

print("\nFailure mode distribution (top rows):")
display(failure_tbl.sort_values(["variant_id", "count"], ascending=[True, False]).head(30))

# =========================
# 7) Message feature analysis
# =========================
# Build message text for each (alert_id, variant_id)
# Requires ALERTS + variants_from_alert. If you don't have them here, you can still do features
# only if your df already includes a column like 'variant_text'.
variant_text_col = next((c for c in ["variant_text", "message_text", "alert_variant_text"] if c in df.columns), None)

variant_text_df = None
if variant_text_col:
    variant_text_df = df[["alert_id", "variant_id", variant_text_col]].drop_duplicates().rename(columns={variant_text_col:"variant_text"})
else:
    try:
        rows = []
        for a in ALERTS:
            vmap = variants_from_alert(a["text"])
            for vid, vtxt in vmap.items():
                rows.append({"alert_id": a["alert_id"], "variant_id": vid, "variant_text": vtxt})
        variant_text_df = pd.DataFrame(rows)
    except Exception:
        print("NOTE: No variant text available. Add 'variant_text' to results or provide ALERTS+variants_from_alert.")


sub = deltas[deltas["variant_id"] == "B_action_first"].copy()
sub["d_bullet_count"] = sub["d_bullet_count"].fillna(0).astype(int)

groups = [g["d_mean_recall"].dropna().values for _, g in sub.groupby("d_bullet_count")]

plt.figure()
plt.boxplot(groups, labels=[str(k) for k in sorted(sub["d_bullet_count"].unique())])
plt.axhline(0)
plt.xlabel("Δ bullet_count (categorical)")
plt.ylabel("Δ mean_recall vs control")
plt.title("B_action_first: Δ recall by Δ bullet count")
plt.tight_layout()
plt.show()


def ecdf(vals):
    v = np.sort(np.asarray(vals))
    y = np.arange(1, len(v)+1) / len(v)
    return v, y

plt.figure()
for vid in sorted(deltas["variant_id"].unique()):
    sub = deltas[deltas["variant_id"] == vid]["d_mean_recall"].dropna().values
    if len(sub) == 0:
        continue
    x, y = ecdf(sub)
    plt.plot(x, y, marker='o', linestyle='none')  # points only
plt.axvline(0)
plt.xlabel("Δ mean recall vs control")
plt.ylabel("ECDF (share of alerts ≤ x)")
plt.title("Per-alert Δ recall distribution (ECDF)")
plt.tight_layout()
plt.show()


