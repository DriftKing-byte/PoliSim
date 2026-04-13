# =========================
# 2) Overall performance tables
# =========================
perf = df.groupby("variant_id").agg(
    n=("agent_id", "count"),
    mean_recall=("action_recall", "mean"),
    mean_confused=("confused", "mean"),
    mean_compliance=("compliance_intent", "mean"),
    mean_clarity=("action_clarity", "mean"),
    parse_success_rate=("parse_success", "mean"),
).reset_index().sort_values("mean_recall", ascending=False)

print("\nOverall performance by variant:")
display(perf)

# Subgroup performance
if subgroup_cols:
    perf_sub = df.groupby(subgroup_cols + ["variant_id"]).agg(
        n=("agent_id", "count"),
        mean_recall=("action_recall", "mean"),
        mean_confused=("confused", "mean"),
        mean_compliance=("compliance_intent", "mean"),
        parse_success_rate=("parse_success", "mean"),
    ).reset_index()
    print("\nSubgroup performance (first rows):")
    display(perf_sub.head(30))

# =========================
# 4) Win rate across alerts (robustness)
# =========================
alert_level = df.groupby(["alert_id", "variant_id"]).agg(
    mean_recall=("action_recall", "mean"),
    mean_confused=("confused", "mean"),
    mean_compliance=("compliance_intent", "mean"),
    parse_success_rate=("parse_success", "mean"),
).reset_index()

# Best recall per alert
best_recall = alert_level.sort_values(["alert_id", "mean_recall"], ascending=[True, False]).groupby("alert_id").head(1)
win_rate = best_recall["variant_id"].value_counts().rename_axis("variant_id").reset_index(name="alerts_won")
win_rate["win_rate"] = win_rate["alerts_won"] / best_recall["alert_id"].nunique()

print("\nWin rate (best mean recall per alert):")
display(win_rate)

# Optional: best (lowest) confusion per alert
best_conf = alert_level.sort_values(["alert_id", "mean_confused"], ascending=[True, True]).groupby("alert_id").head(1)
win_conf = best_conf["variant_id"].value_counts().rename_axis("variant_id").reset_index(name="alerts_won_lowest_confused")
win_conf["win_rate"] = win_conf["alerts_won_lowest_confused"] / best_conf["alert_id"].nunique()
print("\nWin rate (lowest confusion per alert):")
display(win_conf)

if variant_text_df is not None:
    feats = variant_text_df.copy()
    feat_cols = feats["variant_text"].apply(message_features).apply(pd.Series)
    feats = pd.concat([feats, feat_cols], axis=1)

    # Merge with alert-level outcomes
    outcomes = df.groupby(["alert_id", "variant_id"]).agg(
        mean_recall=("action_recall", "mean"),
        mean_confused=("confused", "mean"),
        mean_compliance=("compliance_intent", "mean"),
        parse_success_rate=("parse_success", "mean"),
        n=("agent_id", "count"),
    ).reset_index()

    feat_out = outcomes.merge(feats, on=["alert_id", "variant_id"], how="left")
    print("\nFeature + outcome merged:")
    display(feat_out.head())

    # Correlations (numeric features only)
    num_feats = ["char_len","word_len","avg_words_per_sentence","bullet_count","fk_grade"]
    corr_tbl = feat_out[num_feats + ["mean_recall","mean_confused","mean_compliance"]].corr(numeric_only=True)
    print("\nCorrelation table (features vs outcomes):")
    display(corr_tbl.loc[num_feats, ["mean_recall","mean_confused","mean_compliance"]])

    # ---- Scatter: char_len vs confusion
    plt.figure()
    plt.scatter(feat_out["char_len"], feat_out["mean_confused"])
    plt.xlabel("Message length (chars)")
    plt.ylabel("Mean confused rate")
    plt.title("Message length vs confusion (alert-variant level)")
    plt.tight_layout()
    plt.show()

    # ---- Scatter: fk_grade vs recall
    plt.figure()
    plt.scatter(feat_out["fk_grade"], feat_out["mean_recall"])
    plt.xlabel("Flesch-Kincaid grade (approx.)")
    plt.ylabel("Mean action recall")
    plt.title("Readability vs action recall (alert-variant level)")
    plt.tight_layout()
    plt.show()

    # Save tables
    diag.to_csv("diag_by_variant.csv", index=False)
    perf.to_csv("perf_by_variant.csv", index=False)
    delta_tbl.to_csv("paired_deltas_vs_control.csv", index=False)
    win_rate.to_csv("win_rate_by_alert.csv", index=False)
    failure_tbl.to_csv("failure_modes_by_variant.csv", index=False)
    feat_out.to_csv("message_features_with_outcomes.csv", index=False)
    print("\nSaved CSVs to current working dir (Colab).")

plt.figure()
for vid in feat_out["variant_id"].unique():
    sub = feat_out[feat_out["variant_id"] == vid]
    plt.scatter(sub["fk_grade"], sub["mean_recall"], label=vid)
plt.xlabel("FK grade"); plt.ylabel("Mean recall")
plt.title("Readability vs recall (colored by variant)")
plt.legend()
plt.tight_layout()
plt.show()


plt.figure()
plt.scatter(feat_out3["first_action_pos"], feat_out3["mean_recall"])
plt.xlabel("Position of first action verb (chars from start)")
plt.ylabel("Mean action recall")
plt.title("Earlier actions vs recall (alert-variant level)")
plt.tight_layout()
plt.show()


# Assuming you created j with d_first_action_pos and d_mean_recall (from my earlier snippet)
plt.figure()
plt.scatter(j["d_first_action_pos"], j["d_mean_recall"])
plt.axhline(0); plt.axvline(0)
plt.xlabel("Δ first action position (chars) vs control (negative = earlier)")
plt.ylabel("Δ mean recall vs control")
plt.title("Within-alert: moving actions earlier vs recall change")
plt.tight_layout()
plt.show()


