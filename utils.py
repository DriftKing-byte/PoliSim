df = df2.copy()

# =========================
# 1) Parse/validity diagnostics tables
# =========================
diag = df.groupby("variant_id").agg(
    n=("agent_id", "count"),
    parse_success_rate=("parse_success", "mean"),
    mean_retry=("retry_count", "mean") if "retry_count" in df.columns else ("parse_success", "mean"),
    empty_actions_rate=("actions_list", lambda s: np.mean([isinstance(a, list) and len(a)==0 for a in s])),
).reset_index().sort_values("parse_success_rate")

print("\nParse diagnostics by variant:")
display(diag)

# Optional: diagnostics by subgroup too (english/mobility/trust)
subgroup_cols = [c for c in ["english", "mobility", "trust"] if c in df.columns]
if subgroup_cols:
    diag_sub = df.groupby(subgroup_cols + ["variant_id"]).agg(
        n=("agent_id", "count"),
        parse_success_rate=("parse_success", "mean"),
        empty_actions_rate=("actions_list", lambda s: np.mean([isinstance(a, list) and len(a)==0 for a in s])),
    ).reset_index()
    print("\nParse diagnostics by subgroup:")
    display(diag_sub.head(20))

# =========================
# 3) Paired deltas vs control + bootstrap CIs
# =========================
CONTROL_ID = "A_control"  # change if your control name differs

def bootstrap_ci(values, n_boot=2000, alpha=0.05, seed=0):
    """Return (mean, lo, hi) bootstrap CI for 1D array-like, ignoring NaNs."""
    rng = np.random.default_rng(seed)
    v = np.array([x for x in values if x is not None and not (isinstance(x, float) and np.isnan(x))], dtype=float)
    if len(v) == 0:
        return (np.nan, np.nan, np.nan)
    means = []
    for _ in range(n_boot):
        samp = rng.choice(v, size=len(v), replace=True)
        means.append(np.mean(samp))
    means = np.array(means)
    lo = np.quantile(means, alpha/2)
    hi = np.quantile(means, 1-alpha/2)
    return (float(np.mean(v)), float(lo), float(hi))

# =========================
# 5) Hallucinated / unsafe action checks
# =========================
# Requires ALERTS with required_actions and (optionally) alert text.
# Build map: alert_id -> required_actions
required_map = None
try:
    required_map = {a["alert_id"]: a.get("required_actions", []) for a in ALERTS}
except Exception:
    print("NOTE: ALERTS not found. Unsafe/hallucinated action checks will be skipped.")

# Simple normalization
def norm(s):
    return re.sub(r"\s+", " ", str(s).strip().lower())

# A small blacklist of clearly unsafe behaviors (edit to match your hazard domain)
UNSAFE_PHRASES = [
    "ignore evacuation", "do nothing", "stay outside",
    "drive through", "go toward the fire", "open windows",
    "drink tap water", "stop boiling", "leave shelter",
]

def count_extra_actions(actions, required_actions):
    """Count actions that don't match any required action substring (rough)."""
    if not isinstance(actions, list):
        return np.nan
    req = [norm(r) for r in (required_actions or [])]
    extras = 0
    for a in actions:
        a_n = norm(a)
        if not a_n:
            continue
        # if it matches none of the required actions (substring heuristic), count as extra
        if len(req) > 0 and not any(r in a_n or a_n in r for r in req):
            extras += 1
    return extras

def unsafe_flag(actions):
    if not isinstance(actions, list):
        return False
    joined = " ".join([norm(x) for x in actions])
    return any(p in joined for p in UNSAFE_PHRASES)

if required_map is not None:
    df["required_actions"] = df["alert_id"].map(required_map)
    df["extra_actions_count"] = df.apply(lambda r: count_extra_actions(r["actions_list"], r["required_actions"]), axis=1)
    df["unsafe_flag"] = df["actions_list"].apply(unsafe_flag)

    unsafe_tbl = df.groupby("variant_id").agg(
        unsafe_rate=("unsafe_flag", "mean"),
        mean_extra_actions=("extra_actions_count", "mean"),
    ).reset_index().sort_values("unsafe_rate", ascending=False)

    print("\nUnsafe / extra action diagnostics:")
    display(unsafe_tbl)


# --- Feature functions
def count_syllables(word):
    word = re.sub(r"[^a-z]", "", word.lower())
    if not word:
        return 0
    vowels = "aeiouy"
    count = 0
    prev_vowel = False
    for ch in word:
        is_vowel = ch in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    if word.endswith("e") and count > 1:
        count -= 1
    return max(count, 1)

def flesch_kincaid_grade(text):
    # Simple heuristic FK grade
    text = str(text)
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    words = re.findall(r"\b[\w']+\b", text.lower())
    if len(sentences) == 0 or len(words) == 0:
        return np.nan
    sylls = sum(count_syllables(w) for w in words)
    wps = len(words) / len(sentences)
    spw = sylls / len(words)
    return 0.39 * wps + 11.8 * spw - 15.59

def message_features(text):
    t = str(text)
    words = re.findall(r"\b[\w']+\b", t)
    lines = t.splitlines()
    sentences = [s for s in re.split(r"[.!?]+", t) if s.strip()]
    bullet_lines = [ln for ln in lines if ln.strip().startswith(("-", "•", "*"))]

    # slot heuristics
    has_time = bool(re.search(r"\b(today|tonight|tomorrow|until|am|pm|\d{1,2}:\d{2})\b", t.lower()))
    has_location = bool(re.search(r"\b(near|in|at|between|area|county|city|neighborhood|mile)\b", t.lower()))
    has_source = bool(re.search(r"\b(official|police|sheriff|fire department|emergency management|national weather service|nws)\b", t.lower()))
    has_url = bool(re.search(r"https?://|www\.", t.lower()))

    return {
        "char_len": len(t),
        "word_len": len(words),
        "sentence_count": len(sentences),
        "avg_words_per_sentence": (len(words)/len(sentences)) if len(sentences) else np.nan,
        "line_count": len(lines),
        "bullet_count": len(bullet_lines),
        "fk_grade": flesch_kincaid_grade(t),
        "has_time": has_time,
        "has_location": has_location,
        "has_source": has_source,
        "has_url": has_url,
    }

variant_text_df

