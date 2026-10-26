import io
import re

import pandas as pd
import streamlit as st

from src.scoring import (
    NO_ID, NOT_AVAILABLE, as_text, standardize_customers, standardize_employees,
    useful_columns,
)

CHOOSE = "(choose a column)"

st.set_page_config(page_title="Use Your Own Data", layout="wide")
st.title("Use Your Own Data")
st.write(
    "Upload any customer or employee file. Your columns can have any names: you tell "
    "RetainIQ which column means what, and it scores the risk and updates the other pages."
)
st.info(
    "Your file is processed in memory for this browser session only. This app does not "
    "save it to the database or to disk, and refreshing the page returns to the demo data. "
    "If you try the public demo, use anonymised IDs and do not upload real personal data."
)

LEFT_WORDS = {"yes", "y", "true", "1", "churned", "churn", "left", "exited", "attrited",
              "cancelled", "canceled", "closed", "inactive", "resigned", "terminated"}
YES_WORDS = {"yes", "y", "true", "1"}


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


def load(up):
    try:
        return read_file(up.name, up.getvalue())
    except Exception as e:
        st.error(f"Could not read the file: {e}")
        return None


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


def column_picker(label, columns, names, key, required=False, id_field=False):
    if id_field:
        options = [NO_ID] + columns
    elif required:
        options = [CHOOSE] + columns
    else:
        options = [NOT_AVAILABLE] + columns
    g = guess_column(columns, names)
    idx = options.index(g) if g in options else 0
    return st.selectbox(label, options, index=idx, key=key)


def value_picker(label, series, is_default, key):
    vals = sorted(as_text(series).dropna().unique().tolist())
    if len(vals) > 60:
        st.warning("This column has too many different values to use here. Choose another column.")
        return []
    return st.multiselect(label, vals, default=[v for v in vals if is_default(v)], key=key)


def banner(kind):
    key = f"custom_{kind}"
    if key in st.session_state:
        st.success(
            f"Currently using **your uploaded {kind} data** ({len(st.session_state[key]):,} rows). "
            "Open the other pages to see results based on it."
        )
        if st.button(f"Switch back to demo {kind} data", key=f"reset_{kind}"):
            del st.session_state[key]
            st.rerun()
    else:
        st.info(f"Currently using the **demo {kind} dataset**.")


def preview(kind, prepared, info, rate_label, high_label, show_cols):
    st.subheader("Check the result")
    c1, c2, c3 = st.columns(3)
    c1.metric("Rows used", f"{info['rows_used']:,}", help=f"{info['rows_in']:,} rows in the file")
    c2.metric(rate_label, f"{info['rate']:.1%}")
    c3.metric(high_label, f"{info['high_risk']:,}")

    skipped = info["rows_in"] - info["rows_used"]
    if skipped:
        st.caption(f"{skipped:,} rows were skipped (missing ID or status).")
    if info["not_used"]:
        st.warning(
            "Not matched, so these rules are skipped: " + ", ".join(info["not_used"])
            + ". Scores are scaled to the fields you did match."
        )
    if info["points"] <= 30:
        st.error(
            "Very few scoring rules apply to this file, so the risk levels are only a rough "
            "guide. Match more columns (for example tenure, charges, overtime, satisfaction "
            "or income) for meaningful scores."
        )
    st.caption(
        f"Check that the {rate_label.lower()} looks right. If it does not, "
        "change which values mean 'left' above."
    )
    st.dataframe(
        prepared[useful_columns(prepared, show_cols)].head(10),
        width="stretch", hide_index=True,
    )
    if st.button(f"Use this {kind} data", key=f"use_{kind}", type="primary"):
        st.session_state[f"custom_{kind}"] = prepared
        st.rerun()


def customers_tab():
    banner("customers")
    up = st.file_uploader("Upload your customer file (CSV or Excel)",
                          type=["csv", "xlsx"], key="up_customers")
    if up is None:
        st.caption("Your columns can have any names. You will match them in the next step.")
        return
    raw = load(up)
    if raw is None:
        return

    tok = f"c_{up.name}_{up.size}"
    cols = list(raw.columns)
    st.write(f"File read: **{len(raw):,} rows** and **{len(cols)} columns**.")
    st.dataframe(raw.head(5), width="stretch", hide_index=True)

    st.subheader("Match your columns")
    st.caption("Fields marked * are required. If your file has no ID column, choose the "
               "'no ID column' option. Every extra field you match adds rules and "
               "improves the recommendations.")
    a, b = st.columns(2)
    with a:
        m_id = column_picker("Customer ID *", cols,
                             ["customerid", "custid", "clientid", "userid", "accountid", "id"],
                             f"{tok}_id", id_field=True)
        m_churn = column_picker("Churn status * (did the customer leave?)", cols,
                                ["churn", "churned", "exited", "attrition", "left", "status"],
                                f"{tok}_churn", required=True)
        m_contract = column_picker("Contract or plan type", cols,
                                   ["contract", "contracttype", "plan", "subscription"],
                                   f"{tok}_contract")
    with b:
        m_tenure = column_picker("Tenure (how long they have been a customer)", cols,
                                 ["tenure", "customertenure", "accountage"], f"{tok}_tenure")
        unit = st.selectbox("Tenure unit", ["Months", "Years", "Days"], key=f"{tok}_unit")
        m_charges = column_picker("Monthly charges or monthly revenue", cols,
                                  ["monthlycharges", "monthlybill", "monthlyrevenue",
                                   "monthlyfee", "monthlyspend", "arpu"], f"{tok}_charges")

    if m_churn == CHOOSE:
        st.info("Choose the churn status column to continue.")
        return

    churn_vals = value_picker(
        "Which value(s) in the churn column mean the customer LEFT? *",
        raw[m_churn], lambda v: v.lower() in LEFT_WORDS, f"{tok}_{m_churn}_left",
    )
    short_vals = []
    if m_contract != NOT_AVAILABLE:
        short_vals = value_picker(
            "Which value(s) mean a short, flexible contract (monthly, no commitment)?",
            raw[m_contract],
            lambda v: "month" in v.lower() or v.lower() in {"flexible", "none", "no contract"},
            f"{tok}_{m_contract}_short",
        )

    mapping = {"customerID": m_id, "Churn": m_churn, "Contract": m_contract,
               "tenure": m_tenure, "MonthlyCharges": m_charges}
    try:
        prepared, info = standardize_customers(raw, mapping, churn_vals, short_vals, unit)
    except ValueError as e:
        st.error(str(e))
        return
    except Exception as e:
        st.error(f"Something went wrong: {e}")
        return

    preview("customers", prepared, info, "Churn rate", "High-risk customers (not yet left)",
            ["customerID", "Churn", "Contract", "tenure", "MonthlyCharges", "RiskScore", "RiskLevel"])


def employees_tab():
    banner("employees")
    up = st.file_uploader("Upload your employee file (CSV or Excel)",
                          type=["csv", "xlsx"], key="up_employees")
    if up is None:
        st.caption("Your columns can have any names. You will match them in the next step.")
        return
    raw = load(up)
    if raw is None:
        return

    tok = f"e_{up.name}_{up.size}"
    cols = list(raw.columns)
    st.write(f"File read: **{len(raw):,} rows** and **{len(cols)} columns**.")
    st.dataframe(raw.head(5), width="stretch", hide_index=True)

    st.subheader("Match your columns")
    st.caption("Fields marked * are required. If your file has no ID column, choose the "
               "'no ID column' option. Every extra field you match adds rules and "
               "improves the recommendations.")
    a, b = st.columns(2)
    with a:
        m_id = column_picker("Employee ID *", cols,
                             ["employeenumber", "employeeid", "empid", "empno", "staffid", "id"],
                             f"{tok}_id", id_field=True)
        m_att = column_picker("Attrition status * (did the employee leave?)", cols,
                              ["attrition", "churn", "left", "resigned", "turnover", "exited",
                               "terminated", "status"], f"{tok}_att", required=True)
        m_dept = column_picker("Department", cols,
                               ["department", "dept", "team", "function"], f"{tok}_dept")
        m_role = column_picker("Job role", cols,
                               ["jobrole", "role", "jobtitle", "position", "designation"],
                               f"{tok}_role")
        m_ot = column_picker("Overtime", cols, ["overtime"], f"{tok}_ot")
    with b:
        m_years = column_picker("Time at the company", cols,
                                ["yearsatcompany", "tenure", "yearsofservice", "yearsincompany",
                                 "workexperience"], f"{tok}_years")
        unit = st.selectbox("Time at the company is in", ["Years", "Months", "Days"],
                            key=f"{tok}_unit")
        m_inc = column_picker("Monthly income / salary", cols,
                              ["monthlyincome", "monthlysalary", "salary", "income"],
                              f"{tok}_inc")
        m_sat = column_picker("Job satisfaction rating", cols,
                              ["jobsatisfaction", "satisfaction", "satisfactionlevel"],
                              f"{tok}_sat")
        m_wlb = column_picker("Work-life balance rating", cols,
                              ["worklifebalance", "wlb"], f"{tok}_wlb")
        higher = st.checkbox("For rating columns, a higher number means better",
                             value=True, key=f"{tok}_higher")

    if m_att == CHOOSE:
        st.info("Choose the attrition status column to continue.")
        return

    left_vals = value_picker(
        "Which value(s) in the attrition column mean the employee LEFT? *",
        raw[m_att], lambda v: v.lower() in LEFT_WORDS, f"{tok}_{m_att}_left",
    )
    ot_vals = []
    if m_ot != NOT_AVAILABLE:
        ot_vals = value_picker(
            "Which value(s) in the overtime column mean they DO work overtime?",
            raw[m_ot], lambda v: v.lower() in YES_WORDS, f"{tok}_{m_ot}_ot",
        )

    mapping = {"EmployeeNumber": m_id, "Attrition": m_att, "Department": m_dept,
               "JobRole": m_role, "OverTime": m_ot, "YearsAtCompany": m_years,
               "MonthlyIncome": m_inc, "JobSatisfaction": m_sat, "WorkLifeBalance": m_wlb}
    try:
        prepared, info = standardize_employees(raw, mapping, left_vals, ot_vals, unit, higher)
    except ValueError as e:
        st.error(str(e))
        return
    except Exception as e:
        st.error(f"Something went wrong: {e}")
        return

    preview("employees", prepared, info, "Attrition rate", "High-risk employees (still employed)",
            ["EmployeeNumber", "Attrition", "Department", "JobRole", "OverTime",
             "JobSatisfaction", "YearsAtCompany", "MonthlyIncome", "RiskScore", "RiskLevel"])


tab1, tab2 = st.tabs(["Customers", "Employees"])
with tab1:
    customers_tab()
with tab2:
    employees_tab()