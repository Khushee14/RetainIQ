import pandas as pd
import plotly.express as px
import streamlit as st

from src.exports import to_excel_bytes
from src.scoring import load_employees, useful_columns

st.set_page_config(page_title="Employee Retention", layout="wide")
st.title("Employee Retention")
st.info(
    "Risk scores are for human review only. Do not use them alone for hiring, "
    "firing, promotion or pay decisions."
)

if "custom_employees" in st.session_state:
    st.info("Showing **your uploaded employee data**.")
else:
    st.caption(
        "Showing the demo dataset (IBM HR sample). "
        "Upload your own on the **Use Your Own Data** page."
    )

df = load_employees()
df["TenureBand"] = pd.cut(
    df["YearsAtCompany"],
    bins=[-1, 2, 5, 10, float("inf")],
    labels=["0-2 yrs", "3-5 yrs", "6-10 yrs", "10+ yrs"],
)

# ---------- Sidebar filters ----------
st.sidebar.header("Filters")
mask = pd.Series(True, index=df.index)

dept_options = sorted(df["Department"].unique())
if len(dept_options) > 1:
    chosen = st.sidebar.multiselect("Department", dept_options, default=dept_options)
    mask &= df["Department"].isin(chosen)

ot_options = sorted(df["OverTime"].unique())
if len(ot_options) > 1:
    chosen = st.sidebar.multiselect("Overtime", ot_options, default=ot_options)
    mask &= df["OverTime"].isin(chosen)

filtered = df[mask]
if filtered.empty:
    st.warning("No employees match these filters.")
    st.stop()

# ---------- KPI cards ----------
current = filtered[filtered["Left"] == 0]
high_risk = current[current["RiskLevel"] == "High"]
avg_income = filtered["MonthlyIncome"].mean()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total employees", f"{len(filtered):,}")
c2.metric("Attrition rate", f"{filtered['Left'].mean():.1%}")
c3.metric("High-risk current employees", f"{len(high_risk):,}")
c4.metric("Avg monthly income", f"${avg_income:,.0f}" if pd.notna(avg_income) else "n/a")

# ---------- Charts (only the ones the data supports) ----------
figs = []

if filtered["Department"].nunique() > 1:
    d = filtered.groupby("Department")["Left"].mean().reset_index()
    f = px.bar(d, x="Department", y="Left", title="Attrition rate by department",
               labels={"Left": "Attrition rate"})
    f.update_yaxes(tickformat=".0%")
    figs.append(f)

if filtered["YearsAtCompany"].notna().any():
    d = filtered.groupby("TenureBand", observed=True)["Left"].mean().reset_index()
    f = px.bar(d, x="TenureBand", y="Left", title="Attrition rate by tenure",
               labels={"Left": "Attrition rate", "TenureBand": "Years at company"})
    f.update_yaxes(tickformat=".0%")
    figs.append(f)

if filtered["OverTime"].nunique() > 1:
    d = filtered.groupby("OverTime")["Left"].mean().reset_index()
    f = px.bar(d, x="OverTime", y="Left", title="Attrition rate by overtime",
               labels={"Left": "Attrition rate"})
    f.update_yaxes(tickformat=".0%")
    figs.append(f)

rc = current["RiskLevel"].value_counts().reindex(["Low", "Medium", "High"]).reset_index()
rc.columns = ["RiskLevel", "Employees"]
figs.append(px.bar(rc, x="RiskLevel", y="Employees", title="Current employees by risk level"))

for i in range(0, len(figs), 2):
    for col, fig in zip(st.columns(2), figs[i:i + 2]):
        col.plotly_chart(fig, width="stretch")

# ---------- High-risk table ----------
st.subheader("High-risk employees who are still with the company")
st.caption(
    "Risk score is based on overtime, job satisfaction, tenure, pay compared with "
    "the department median, and work-life balance, using the fields available in the data. "
    "These factors are associated with attrition, not proven causes."
)
cols = useful_columns(high_risk, ["EmployeeNumber", "Department", "JobRole", "OverTime",
                                  "JobSatisfaction", "YearsAtCompany", "MonthlyIncome",
                                  "RiskScore"])
table = high_risk.sort_values("RiskScore", ascending=False)[cols]
st.dataframe(table, width="stretch", hide_index=True)

st.download_button(
    "Download high-risk employees (Excel)",
    data=to_excel_bytes(table),
    file_name="high_risk_employees.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    key="dl_employees",
)