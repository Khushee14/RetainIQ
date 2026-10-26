import io
import re

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.db import add_actions
from src.exports import to_excel_bytes
from src.scoring import as_text

st.set_page_config(page_title="Learn From My Data", layout="wide")
st.title("Learn From My Data")
st.write(
    "Upload any customer or employee file. Your columns can have any names and there is "
    "no fixed format. RetainIQ learns from your data which columns are linked to people "
    "leaving, scores everyone, and shows who to talk to first."
)
st.info(
    "Your file is processed in memory for this browser session only. It is not saved "
    "to disk. If you try the public demo, use anonymised data."
)

NO_ID = "(no ID column - use row numbers)"
CHOOSE = "(choose a column)"
LEFT_WORDS = {"yes", "y", "true", "1", "churned", "churn", "left", "exited", "attrited",
              "cancelled", "canceled", "closed", "inactive", "resigned", "terminated"}


@st.cache_data
def read_file(name, data):
    buf = io.BytesIO(data)
    if name.lower().endswith(".csv"):
        try:
            df = pd.read_csv(buf, encoding="utf-8-sig")
        except UnicodeDecodeError:
            buf.seek(0)
            df = pd.read_csv(buf, encoding="latin-1")
    else:
        df = pd.read_excel(buf)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def guess_column(columns, names):
    norm = {c: re.sub(r"[^a-z0-9]", "", str(c).lower()) for c in columns}
    for n in names:
        for c, k in norm.items():
            if k == n:
                return c
    for n in names:
        if len(n) < 5:
            continue
        for c, k in norm.items():
            if n in k:
                return c
    return None


def is_num(s):
    return pd.api.types.is_numeric_dtype(s)


def bin_series(s):
    """Turn a column into groups so churn can be compared between groups."""
    if is_num(s) and s.nunique() > 10:
        try:
            return pd.qcut(s, 4, duplicates="drop").astype(str).replace("nan", "Missing")
        except ValueError:
            pass
    return as_text(s).fillna("Missing")


def build_model(num_cols, cat_cols, kind):
    logistic = kind.startswith("Logistic")
    parts = []
    if num_cols:
        steps = [("imp", SimpleImputer(strategy="median"))]
        if logistic:
            steps.append(("sc", StandardScaler()))
        parts.append(("num", Pipeline(steps), num_cols))
    if cat_cols:
        parts.append(("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols))
    clf = (
        LogisticRegression(max_iter=1000)
        if logistic
        else RandomForestClassifier(n_estimators=150, max_depth=10, min_samples_leaf=20,
                                    n_jobs=-1, random_state=42)
    )
    return Pipeline([("pre", ColumnTransformer(parts)), ("clf", clf)])


def run(raw, target, left_vals, id_col, feats, model_kind, kind):
    d = raw[raw[target].notna()].reset_index(drop=True)
    y = as_text(d[target]).isin([str(v) for v in left_vals]).astype(int)
    rate = float(y.mean())
    if y.sum() < 20 or (len(y) - y.sum()) < 20:
        raise ValueError(
            "Too few examples of one outcome. Check which values mean 'left': "
            f"{int(y.sum())} left and {int(len(y) - y.sum())} stayed."
        )

    if id_col == NO_ID:
        prefix = "C" if kind == "Customers" else "E"
        ids = pd.Series([f"{prefix}{i + 1}" for i in range(len(d))])
    else:
        ids = as_text(d[id_col])
        if ids.isna().any() or ids.nunique() < len(ids):
            raise ValueError(
                f"'{id_col}' cannot be an ID because it has repeated or empty values. "
                f"Choose another column or '{NO_ID}'."
            )

    X = pd.DataFrame(index=d.index)
    num_cols, cat_cols = [], []
    for c in feats:
        if is_num(d[c]):
            X[c] = pd.to_numeric(d[c], errors="coerce")
            num_cols.append(c)
        else:
            X[c] = as_text(d[c]).fillna("Missing")
            cat_cols.append(c)

    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, stratify=y, random_state=42)
    if len(Xtr) > 40000:
        keep = Xtr.sample(40000, random_state=42).index
        Xtr, ytr = Xtr.loc[keep], ytr.loc[keep]

    model = build_model(num_cols, cat_cols, model_kind)
    model.fit(Xtr, ytr)
    p_te = model.predict_proba(Xte)[:, 1]
    auc = float(roc_auc_score(yte, p_te))
    acc = float(accuracy_score(yte, p_te >= 0.5))
    base = float(max(yte.mean(), 1 - yte.mean()))

    prob = model.predict_proba(X)[:, 1]
    score = (pd.Series(prob).rank(pct=True) * 100).round().astype(int)
    level = pd.cut(score, bins=[-1, 49, 79, 100], labels=["Low", "Medium", "High"]).astype(str)

    n_min = max(30, int(0.01 * len(d)))
    binned = {c: bin_series(d[c]) for c in feats}
    lifts = pd.DataFrame(index=d.index)
    rate_maps = {}
    drivers = []
    for c in feats:
        g = y.groupby(binned[c]).agg(["mean", "count"])
        g = g[g["count"] >= n_min]
        if len(g) < 2:
            continue
        rate_maps[c] = g["mean"].to_dict()
        lift = binned[c].map(g["mean"] / rate).fillna(0)
        lifts[c] = lift.where(lift >= 1.15, 0)
        drivers.append({"Column": c, "Gap": float(g["mean"].max() - g["mean"].min())})

    return {
        "d": d, "ids": ids, "y": y, "prob": prob, "score": score, "level": level,
        "auc": auc, "acc": acc, "base": base, "rate": rate, "binned": binned,
        "rate_maps": rate_maps, "lifts": lifts, "n_min": n_min,
        "drivers": pd.DataFrame(drivers), "kind": kind, "rows_in": len(raw),
    }


def reasons_for(idx, res, top=3):
    lifts, binned, rate_maps, overall = (
        res["lifts"], res["binned"], res["rate_maps"], res["rate"],
    )
    if lifts.shape[1] == 0:
        return ["" for _ in idx]
    cols = list(lifts.columns)
    L = lifts.loc[idx].to_numpy()
    order = np.argsort(-L, axis=1)[:, :top]
    out = []
    for r, row_idx in enumerate(idx):
        parts = []
        for j in order[r]:
            if L[r, j] <= 0:
                continue
            c = cols[j]
            v = binned[c].loc[row_idx]
            parts.append(f"{c} = {v} (left: {rate_maps[c][v]:.0%} vs {overall:.0%} overall)")
        out.append("; ".join(parts))
    return out


# =====================================================
# Upload
# =====================================================
up = st.file_uploader("Upload your file (CSV or Excel)", type=["csv", "xlsx"], key="learn_up")
if up is None:
    st.stop()

try:
    raw = read_file(up.name, up.getvalue())
except Exception as e:
    st.error(f"Could not read the file: {e}")
    st.stop()

tok = f"l_{up.name}_{up.size}"
cols = list(raw.columns)
st.write(f"File read: **{len(raw):,} rows** and **{len(cols)} columns**.")
st.dataframe(raw.head(5), width="stretch", hide_index=True)

# =====================================================
# Step 1: set up
# =====================================================
st.subheader("1. Tell RetainIQ about your file")
kind = st.radio("This file is about", ["Customers", "Employees"], horizontal=True, key=f"{tok}_kind")
who = "customer" if kind == "Customers" else "employee"

g_target = guess_column(cols, ["churn", "churned", "attrition", "exited", "left", "resigned",
                               "turnover", "status"])
t_opts = [CHOOSE] + cols
target = st.selectbox(
    f"Which column says whether the {who} LEFT? *", t_opts,
    index=t_opts.index(g_target) if g_target in t_opts else 0, key=f"{tok}_target",
)
if target == CHOOSE:
    st.info("Choose the column that says whether the person left.")
    st.stop()

values = sorted(as_text(raw[target]).dropna().unique().tolist())
if len(values) > 30:
    st.error("This column has too many different values to be a left / stayed column. Choose another.")
    st.stop()
left_vals = st.multiselect(
    f"Which value(s) mean the {who} LEFT? *", values,
    default=[v for v in values if v.lower() in LEFT_WORDS], key=f"{tok}_{target}_left",
)
if not left_vals:
    st.info("Select at least one value that means the person left.")
    st.stop()

g_id = guess_column(cols, ["customerid", "employeeid", "employeenumber", "empid", "custid",
                           "clientid", "userid", "id"])
id_opts = [NO_ID] + cols
id_col = st.selectbox(
    "ID column (optional)", id_opts,
    index=id_opts.index(g_id) if g_id in id_opts else 0, key=f"{tok}_id",
)

candidates, skipped = [], []
for c in cols:
    if c in (target, id_col):
        continue
    s = raw[c]
    if s.nunique() < 2 or (not is_num(s) and s.nunique() > 50):
        skipped.append(c)
    else:
        candidates.append(c)
if skipped:
    st.caption("Not offered (constant or too many different text values): " + ", ".join(skipped))
feats = st.multiselect(
    "Columns the model may learn from", candidates, default=candidates, key=f"{tok}_feats",
    help="Leave out any column that is only known after the person has left.",
)
if not feats:
    st.info("Select at least one column to learn from.")
    st.stop()

model_kind = st.selectbox(
    "Model",
    ["Logistic Regression (fast, easy to explain)", "Random Forest (slower, can find complex patterns)"],
    key=f"{tok}_model",
)

sig = (target, tuple(left_vals), id_col, tuple(feats), model_kind, kind)
res_key = f"{tok}_res"

if st.button("Train the model and score everyone", type="primary", key=f"{tok}_train"):
    try:
        with st.spinner("Training the model..."):
            res = run(raw, target, left_vals, id_col, feats, model_kind, kind)
        res["sig"] = sig
        st.session_state[res_key] = res
    except ValueError as e:
        st.session_state.pop(res_key, None)
        st.error(str(e))
        st.stop()
    except Exception as e:
        st.session_state.pop(res_key, None)
        st.error(f"Something went wrong: {e}")
        st.stop()

res = st.session_state.get(res_key)
if res is None:
    st.info("Press **Train the model and score everyone** to continue.")
    st.stop()
if res["sig"] != sig:
    st.warning("You changed a setting. Press **Train the model and score everyone** again.")
    st.stop()

# =====================================================
# Step 2: how good is the model
# =====================================================
st.subheader("2. What the data says")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Rows used", f"{len(res['d']):,}")
m2.metric(f"{'Churn' if kind == 'Customers' else 'Attrition'} rate", f"{res['rate']:.1%}")
m3.metric("Model score (AUC)", f"{res['auc']:.2f}",
          help="0.50 means no better than a coin flip. 1.00 is perfect. Measured on rows "
               "the model had not seen during training.")
m4.metric("Accuracy vs guessing", f"{res['acc']:.0%} vs {res['base']:.0%}",
          help="Accuracy of the model compared with always guessing the most common outcome.")

if res["auc"] < 0.55:
    st.error(
        "The model found almost no link between these columns and who left (AUC close to 0.50). "
        "Risk scores from this file are essentially random, so do not act on them. "
        "The file may simply not contain the real reasons people leave."
    )
elif res["auc"] < 0.65:
    st.warning("The link is weak. Treat the scores as a rough guide only.")
else:
    st.success("The model finds a useful pattern in this data.")

st.caption(
    "These are associations in your data, not proven causes. Scores are percentile ranks "
    "(100 = highest predicted risk). High = top 20%, Medium = next 30%."
)

drivers = res["drivers"]
if not drivers.empty:
    fig = px.bar(
        drivers.sort_values("Gap"), x="Gap", y="Column", orientation="h",
        title="How much the leaving rate differs between groups, by column",
        color_discrete_sequence=["#8e5bd0"],
    )
    fig.update_xaxes(tickformat=".0%", title="Gap between highest and lowest group")
    fig.update_layout(height=max(300, 40 * len(drivers)))
    st.plotly_chart(fig, width="stretch")

    pick = st.selectbox("Look inside a column", list(drivers["Column"]), key=f"{tok}_inspect")
    g = res["y"].groupby(res["binned"][pick]).agg(rate="mean", people="count").reset_index()
    g.columns = ["Group", "Left rate", "People"]
    g = g[g["People"] >= res["n_min"]]
    fig2 = px.bar(g, x="Group", y="Left rate", title=f"Left rate by {pick}",
                  color_discrete_sequence=["#b06ad8"])
    fig2.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig2, width="stretch")

# =====================================================
# Step 3: who to talk to
# =====================================================
st.subheader(f"3. Who is most at risk (not left yet)")
if kind == "Employees":
    st.warning(
        "Scores are for human review only. Do not use them alone for hiring, firing, "
        "promotion or pay decisions."
    )

pool = pd.DataFrame({
    "ID": res["ids"], "RiskScore": res["score"], "RiskLevel": res["level"],
    "prob": res["prob"], "left": res["y"],
})
not_left = pool[pool["left"] == 0].sort_values("prob", ascending=False)
high = int((not_left["RiskLevel"] == "High").sum())
st.write(f"**{high:,}** people who have not left are in the High-risk group.")

n = st.number_input("How many of the highest-risk people to show", min_value=1,
                    max_value=max(1, len(not_left)), value=min(25, max(1, len(not_left))),
                    key=f"{tok}_n")
top = not_left.head(int(n)).copy()
top["Why flagged"] = reasons_for(top.index, res)
table = top[["ID", "RiskScore", "RiskLevel", "Why flagged"]]
st.dataframe(table, width="stretch", hide_index=True)

st.download_button(
    "Download this list (Excel)", data=to_excel_bytes(table),
    file_name="highest_risk_list.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    key=f"{tok}_dl",
)

st.markdown("**Add them to the Action Center to-do list**")
st.caption(
    "RetainIQ cannot know your products or policies, so the suggested action is a "
    "follow-up focused on the factors above. Edit the plan with your own team."
)
if st.button(f"Add these {int(n)} to my to-do list", key=f"{tok}_add"):
    cases = pd.DataFrame({
        "entity_id": top["ID"].values,
        "RiskScore": top["RiskScore"].values,
        "suggested_action": [
            ("Personal follow-up. Main factors: " + w) if w else "Personal follow-up conversation"
            for w in top["Why flagged"]
        ],
    })
    added = add_actions("Customer" if kind == "Customers" else "Employee", cases)
    st.success(f"Added {added} new cases. Open the Action Center to track them.")