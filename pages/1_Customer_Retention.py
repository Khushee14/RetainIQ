import math

import pandas as pd
import plotly.express as px
import streamlit as st

from src.exports import to_excel_bytes
from src.scoring import load_customers, useful_columns

st.set_page_config(page_title="Customer Retention", layout="wide")
st.title("Customer Retention")

if "custom_customers" in st.session_state:
    st.info("Showing **your uploaded customer data**.")
else:
    st.caption(
        "Showing the demo dataset (IBM Telco sample). "
        "Upload your own on the **Use Your Own Data** page."
    )

df = load_customers()

# ---------- Sidebar filters ----------
st.sidebar.header("Filters")
mask = pd.Series(True, index=df.index)

contract_options = sorted(df["Contract"].unique())
if len(contract_options) > 1:
    chosen = st.sidebar.multiselect("Contract type", contract_options, default=contract_options)
    mask &= df["Contract"].isin(chosen)

if df["tenure"].notna().any():
    t_min, t_max = math.floor(df["tenure"].min()), math.ceil(df["tenure"].max())
    if t_min < t_max:
        lo, hi = st.sidebar.slider("Tenure (months)", t_min, t_max, (t_min, t_max))
        mask &= df["tenure"].between(lo, hi) | df["tenure"].isna()

filtered = df[mask]
if filtered.empty:
    st.warning("No customers match these filters.")
    st.stop()

# ---------- KPI cards ----------
active = filtered[filtered["Churned"] == 0]
high_risk = active[active["RiskLevel"] == "High"]
has_charges = df["MonthlyCharges"].notna().any()
revenue_at_risk = high_risk["MonthlyCharges"].sum() * 12

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total customers", f"{len(filtered):,}")
c2.metric("Churn rate", f"{filtered['Churned'].mean():.1%}")
c3.metric("High-risk active customers", f"{len(high_risk):,}")
c4.metric("Annual revenue at risk", f"${revenue_at_risk:,.0f}" if has_charges else "n/a")

# ---------- Charts (only the ones the data supports) ----------
figs = []

if filtered["Contract"].nunique() > 1:
    d = filtered.groupby("Contract")["Churned"].mean().reset_index()
    f = px.bar(d, x="Contract", y="Churned", title="Churn rate by contract type",
               labels={"Churned": "Churn rate"})
    f.update_yaxes(tickformat=".0%")
    figs.append(f)

if filtered["tenure"].notna().any():
    figs.append(px.histogram(filtered.dropna(subset=["tenure"]), x="tenure", color="Churn",
                             nbins=36, title="Customers by tenure (months)", barmode="overlay"))

rc = active["RiskLevel"].value_counts().reindex(["Low", "Medium", "High"]).reset_index()
rc.columns = ["RiskLevel", "Customers"]
figs.append(px.bar(rc, x="RiskLevel", y="Customers", title="Active customers by risk level"))

if filtered["InternetService"].nunique() > 1:
    d = filtered.groupby("InternetService")["Churned"].mean().reset_index()
    f = px.bar(d, x="InternetService", y="Churned", title="Churn rate by internet service",
               labels={"Churned": "Churn rate"})
    f.update_yaxes(tickformat=".0%")
    figs.append(f)

for i in range(0, len(figs), 2):
    for col, fig in zip(st.columns(2), figs[i:i + 2]):
        col.plotly_chart(fig, width="stretch")

# ---------- High-risk table ----------
st.subheader("High-risk customers who haven't left yet")
st.caption(
    "Risk score is based on contract type, tenure, monthly charges, tech support "
    "and internet service, using the fields available in the data. These factors are "
    "associated with churn, not proven causes."
)
cols = useful_columns(high_risk, ["customerID", "Contract", "tenure", "MonthlyCharges",
                                  "TechSupport", "InternetService", "RiskScore"])
table = high_risk.sort_values("RiskScore", ascending=False)[cols]
st.dataframe(table, width="stretch", hide_index=True)

st.download_button(
    "Download high-risk customers (Excel)",
    data=to_excel_bytes(table),
    file_name="high_risk_customers.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    key="dl_customers",
)