import torch, os, platform, json, re, hashlib, sqlite3, time
from google.colab import drive
drive.mount("/content/drive")

BASE_DIR = "/content/drive/MyDrive/polisim_alerts_ab/results"
os.makedirs(BASE_DIR, exist_ok=True)
print("BASE_DIR:", BASE_DIR)

import json, re, math, numpy as np, pandas as pd
import matplotlib.pyplot as plt

RESULTS_PATH = "/content/drive/MyDrive/polisim_alerts_ab/results/results_v2.parquet"
df = pd.read_parquet(RESULTS_PATH).copy()
print("Loaded:", df.shape)
display(df.head())

import numpy as np, pandas as pd, matplotlib.pyplot as plt

# alert-variant level table (one row per alert_id, variant_id)
av = feat_out.copy()  # from your earlier merge
CONTROL_ID = "A_control"

# split control vs others and compute deltas within alert
ctrl = av[av["variant_id"] == CONTROL_ID].set_index("alert_id")
others = av[av["variant_id"] != CONTROL_ID].set_index(["alert_id","variant_id"])

# join control features/outcomes onto others
j = others.join(ctrl, on="alert_id", rsuffix="_ctrl")

# deltas (features + outcomes)
for col in ["mean_recall","mean_confused","mean_compliance"]:
    j[f"d_{col}"] = j[col] - j[f"{col}_ctrl"]

for col in ["char_len","word_len","avg_words_per_sentence","bullet_count","fk_grade"]:
    j[f"d_{col}"] = j[col] - j[f"{col}_ctrl"]

# Fix: Ensure 'variant_id' is not a column before resetting the index
# It should be an index level, but the error suggests it's also a column.
if 'variant_id' in j.columns:
    j = j.drop(columns=['variant_id'])

deltas = j.reset_index()
display(deltas.head())

# Scatter: Δbullet_count vs Δrecall, colored by variant
for vid in deltas["variant_id"].unique():
    sub = deltas[deltas["variant_id"] == vid]
    plt.figure()
    plt.scatter(sub["d_bullet_count"], sub["d_mean_recall"])
    plt.axhline(0); plt.axvline(0)
    plt.xlabel("Δ bullet_count vs control")
    plt.ylabel("Δ mean_recall vs control")
    plt.title(f"{vid}: Δ bullets vs Δ recall (within-alert)")
    plt.tight_layout()
    plt.show()

# Quick correlation table on deltas (overall)
delta_corr = deltas[[f"d_{c}" for c in ["char_len","avg_words_per_sentence","bullet_count","fk_grade",
                                       "mean_recall","mean_confused","mean_compliance"]]].corr()
display(delta_corr.loc[[f"d_{c}" for c in ["char_len","avg_words_per_sentence","bullet_count","fk_grade"]],
                       [f"d_{c}" for c in ["mean_recall","mean_confused","mean_compliance"]]])

import statsmodels.formula.api as smf

# Use alert-variant table (feat_out)
dat = feat_out.dropna(subset=["mean_recall","char_len","bullet_count","fk_grade"]).copy()

# OLS with alert fixed effects
m1 = smf.ols("mean_recall ~ bullet_count + fk_grade + char_len + C(alert_id)", data=dat).fit()
print(m1.summary())

# If you want variant category controlled too:
m2 = smf.ols("mean_recall ~ bullet_count + fk_grade + char_len + C(alert_id) + C(variant_id)", data=dat).fit()
print(m2.summary())


import re, numpy as np

ACTION_VERBS = r"(evacuate|leave|avoid|stay|shelter|boil|seek|call|move|close|turn off|do not|don't)"
def early_action_score(text, window=160):
    t = str(text).lower()
    head = t[:window]
    return 1 if re.search(ACTION_VERBS, head) else 0

def slot_features(text):
    t = str(text).lower()
    has_time = bool(re.search(r"\b(today|tonight|tomorrow|until|am|pm|\d{1,2}:\d{2})\b", t))
    has_location = bool(re.search(r"\b(in|at|near|between|area|county|city|neighborhood)\b", t))
    has_source = bool(re.search(r"\b(police|sheriff|fire department|emergency management|national weather service|nws|official)\b", t))
    has_guidance = bool(re.search(ACTION_VERBS, t))
    return has_time, has_location, has_source, has_guidance

# add to feats dataframe you built from variant_text_df
feats["early_action"] = feats["variant_text"].apply(early_action_score)
tmp = feats["variant_text"].apply(lambda x: slot_features(x)).apply(pd.Series)
tmp.columns = ["has_time","has_location","has_source","has_guidance"]
feats = pd.concat([feats, tmp], axis=1)
feats["slot_count"] = feats[["has_time","has_location","has_source","has_guidance"]].sum(axis=1)

# merge again (or merge these columns into feat_out)
feat_out2 = outcomes.merge(feats, on=["alert_id","variant_id"], how="left")

# now run fixed effects regression with these
import statsmodels.formula.api as smf
dat = feat_out2.dropna(subset=["mean_recall","early_action","slot_count"]).copy()
m = smf.ols("mean_recall ~ early_action + slot_count + bullet_count + C(alert_id)", data=dat).fit()
print(m.summary())


import numpy as np, matplotlib.pyplot as plt

def jitter(x, scale=0.06, seed=0):
    rng = np.random.default_rng(seed)
    return x + rng.normal(0, scale, size=len(x))

sub = deltas[deltas["variant_id"] == "B_action_first"].copy()
x = sub["d_bullet_count"].fillna(0).astype(float).values
y = sub["d_mean_recall"].astype(float).values

plt.figure()
plt.scatter(jitter(x), y)
plt.axhline(0); plt.axvline(0)
plt.xlabel("Δ bullet_count vs control (jittered)")
plt.ylabel("Δ mean_recall vs control")
plt.title("B_action_first: Δ bullets vs Δ recall (within-alert)")
plt.tight_layout()
plt.show()


import re, numpy as np

ACTION_VERBS = r"\b(evacuate|leave|avoid|stay|shelter|boil|seek|call|move|close|turn off|do not|don't)\b"

def first_action_pos(text):
    t = str(text).lower()
    m = re.search(ACTION_VERBS, t)
    return m.start() if m else np.nan

def early_action_ratio(text):
    pos = first_action_pos(text)
    if np.isnan(pos):
        return np.nan
    return pos / max(len(str(text)), 1)

feats["first_action_pos"] = feats["variant_text"].apply(first_action_pos)
feats["early_action_ratio"] = feats["variant_text"].apply(early_action_ratio)

feat_out3 = outcomes.merge(feats, on=["alert_id","variant_id"], how="left")


import numpy as np, matplotlib.pyplot as plt

# deltas: DataFrame with columns ['alert_id','variant_id','d_mean_recall'] from your within-alert join
def plot_waterfall(deltas, variant_id, metric="d_mean_recall"):
    sub = deltas[deltas["variant_id"] == variant_id].copy()
    sub = sub.dropna(subset=[metric])

    sub = sub.sort_values(metric).reset_index(drop=True)
    x = sub[metric].values
    y = np.arange(len(sub))

    plt.figure()
    plt.scatter(x, y)
    plt.axvline(0)
    plt.yticks(y, sub["alert_id"].astype(str))
    plt.xlabel("Δ mean recall vs control")
    plt.ylabel("Alert (sorted)")
    plt.title(f"{variant_id}: per-alert Δ recall (waterfall)")
    plt.tight_layout()
    plt.show()

    # quick summary text (optional)
    print("n alerts:", len(sub),
          "| improved:", int((x > 0).sum()),
          "| harmed:", int((x < 0).sum()),
          "| unchanged:", int((x == 0).sum()),
          "| median Δ:", float(np.median(x)))

plot_waterfall(deltas, "B_action_first")
plot_waterfall(deltas, "C_plain")
plot_waterfall(deltas, "D_constraint")


import numpy as np, matplotlib.pyplot as plt

def bootstrap_ci(arr, n_boot=4000, alpha=0.05, seed=0):
    rng = np.random.default_rng(seed)
    v = np.asarray(arr, dtype=float)
    v = v[~np.isnan(v)]
    if len(v) == 0:
        return np.nan, np.nan, np.nan
    boots = np.array([rng.choice(v, size=len(v), replace=True).mean() for _ in range(n_boot)])
    return v.mean(), np.quantile(boots, alpha/2), np.quantile(boots, 1-alpha/2)

rows = []
for vid in sorted(deltas["variant_id"].unique()):
    x = deltas.loc[deltas["variant_id"] == vid, "d_mean_recall"].dropna().values
    m, lo, hi = bootstrap_ci(x, seed=1)
    rows.append((vid, x, m, lo, hi))

plt.figure()
for i, (vid, x, m, lo, hi) in enumerate(rows):
    # jittered raw points
    y = np.full_like(x, i, dtype=float) + np.random.normal(0, 0.06, size=len(x))
    plt.scatter(x, y)

    # CI line + mean marker
    plt.plot([lo, hi], [i, i])
    plt.scatter([m], [i])

plt.axvline(0)
plt.yticks(range(len(rows)), [r[0] for r in rows])
plt.xlabel("Δ mean recall vs control")
plt.title("Variant effects on recall (per-alert points + bootstrap CI)")
plt.tight_layout()
plt.show()


import re, numpy as np, pandas as pd
import matplotlib.pyplot as plt

# 1) Define what counts as an "action verb" (tweak as needed)
ACTION_RE = re.compile(
    r"\b(evacuate|leave|avoid|stay|shelter|boil|seek|call|move|close|turn off|do not|don't)\b",
    flags=re.IGNORECASE
)

def first_action_pos(text):
    if text is None:
        return np.nan
    t = str(text)
    m = ACTION_RE.search(t)
    return float(m.start()) if m else np.nan

# 2) Get message text per alert/variant
# You should have variant_text either in feat_out already or in feats/variant_text_df.
if "variant_text" in feat_out.columns:
    text_df = feat_out[["alert_id","variant_id","variant_text"]].drop_duplicates()
elif "variant_text" in feats.columns:
    text_df = feats[["alert_id","variant_id","variant_text"]].drop_duplicates()
else:
    raise ValueError("No 'variant_text' found in feat_out or feats. Add it first.")

text_df["first_action_pos"] = text_df["variant_text"].apply(first_action_pos)

# 3) Merge into alert-variant outcomes
# feat_out should already have mean_recall per (alert_id, variant_id)
av = feat_out.merge(
    text_df[["alert_id","variant_id","first_action_pos"]],
    on=["alert_id","variant_id"],
    how="left"
)

CONTROL_ID = "A_control"

ctrl = av[av["variant_id"] == CONTROL_ID].set_index("alert_id")
oth  = av[av["variant_id"] != CONTROL_ID].set_index(["alert_id","variant_id"])

j = oth.join(ctrl[["mean_recall","first_action_pos"]], on="alert_id", rsuffix="_ctrl").reset_index()

j["d_mean_recall"] = j["mean_recall"] - j["mean_recall_ctrl"]
j["d_first_action_pos"] = j["first_action_pos"] - j["first_action_pos_ctrl"]

print("Columns in j:", j.columns.tolist())
display(j[["alert_id","variant_id","d_first_action_pos","d_mean_recall"]].head())

# 4) Plot: all variants together (jitter by variant)
plt.figure()
for vid in sorted(j["variant_id"].unique()):
    sub = j[j["variant_id"] == vid]
    plt.scatter(sub["d_first_action_pos"], sub["d_mean_recall"], label=vid)
plt.axhline(0); plt.axvline(0)
plt.xlabel("Δ first action position (chars) vs control (negative = earlier)")
plt.ylabel("Δ mean recall vs control")
plt.title("Within-alert: moving actions earlier vs recall change")
plt.legend()
plt.tight_layout()
plt.show()

# 5) Plot: B_action_first only (often clearest)
if "B_action_first" in j["variant_id"].unique():
    sub = j[j["variant_id"] == "B_action_first"].dropna(subset=["d_first_action_pos","d_mean_recall"])
    plt.figure()
    plt.scatter(sub["d_first_action_pos"], sub["d_mean_recall"])
    plt.axhline(0); plt.axvline(0)
    plt.xlabel("Δ first action position (chars) vs control (negative = earlier)")
    plt.ylabel("Δ mean recall vs control")
    plt.title("B_action_first: earlier actions vs recall change (within-alert)")
    plt.tight_layout()
    plt.show()


