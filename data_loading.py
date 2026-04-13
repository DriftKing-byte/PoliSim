# 1) load results
df = pd.read_parquet(RESULTS_PATH)

# 2) build (alert_id, variant_id) -> variant_text table
rows = []
for a in ALERTS:
    vmap = variants_from_alert(a["text"])
    for vid, vtxt in vmap.items():
        rows.append({"alert_id": a["alert_id"], "variant_id": vid, "variant_text": vtxt})

variant_text_df = pd.DataFrame(rows)

# 3) merge + save
df2 = df.merge(variant_text_df, on=["alert_id", "variant_id"], how="left")

print("Missing variant_text:", df2["variant_text"].isna().mean())
#df2.to_parquet(RESULTS_PATH, index=False)


JSON_COL_CANDIDATES = ["parsed_json", "raw_json", "json"]
json_col = next((c for c in JSON_COL_CANDIDATES if c in df.columns), None)
print("Using JSON column:", json_col)

def safe_load_json(x):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return None
    if isinstance(x, dict):
        return x
    if isinstance(x, str):
        x = x.strip()
        if not x:
            return None
        try:
            return json.loads(x)
        except Exception:
            return None
    return None

df["parsed"] = df[json_col].apply(safe_load_json) if json_col else None
df["parse_success"] = df["parsed"].notna()

# Extract fields from parsed json (if present)
def jget(d, k, default=None):
    return d.get(k, default) if isinstance(d, dict) else default

df["actions_list"] = df["parsed"].apply(lambda d: jget(d, "actions", []))
df["confusion_reason"] = df["parsed"].apply(lambda d: jget(d, "confusion_reason", ""))
df["needs_info"] = df["parsed"].apply(lambda d: jget(d, "needs_info", []))
df["would_share"] = df["parsed"].apply(lambda d: jget(d, "would_share", None))

# If your score columns exist already, keep them; otherwise compute basic defaults
for col in ["action_recall", "confused", "compliance_intent", "action_clarity"]:
    if col not in df.columns:
        df[col] = np.nan

# Ensure numeric
for col in ["action_recall", "compliance_intent", "action_clarity"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Ensure confused is boolean-like
if df["confused"].dtype != bool:
    # if it's None/NaN, keep NaN; else cast
    df["confused"] = df["confused"].map(lambda x: x if isinstance(x, bool) else (np.nan if pd.isna(x) else bool(x)))


