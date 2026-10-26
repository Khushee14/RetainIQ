import numbers

import pandas as pd
import streamlit as st

NOT_AVAILABLE = "(not available)"
NO_ID = "(no ID column - use row numbers)"


def as_text(s):
    """Convert a column to clean text (1.0 becomes '1', blanks stay empty)."""
    def f(v):
        if pd.isna(v):
            return None
        if isinstance(v, numbers.Real) and float(v).is_integer():
            return str(int(v))
        return str(v).strip()
    return s.map(f)


def _risk_level(score):
    return pd.cut(score, bins=[-1, 29, 54, 100], labels=["Low", "Medium", "High"])


def _low_flag(series):
    """True for the low end of a rating scale (bottom third of its range)."""
    s = pd.to_numeric(series, errors="coerce")
    lo, hi = s.min(), s.max()
    if pd.isna(lo) or lo == hi:
        return pd.Series(False, index=series.index)
    return s <= lo + (hi - lo) / 3


def useful_columns(df, cols):
    """Keep only columns that actually contain information."""
    keep = []
    for c in cols:
        s = df[c]
        if c in ("customerID", "EmployeeNumber", "RiskScore") or (
            s.notna().any() and not s.astype(str).isin(["Unknown", "Not provided"]).all()
        ):
            keep.append(c)
    return keep


# =====================================================
# Scoring (standard column names)
# =====================================================
def prepare_customers(df, charge_hi=70.0, charge_vhi=80.0, available_points=90):
    df = df.copy()
    df["customerID"] = df["customerID"].astype(str)
    df["tenure"] = pd.to_numeric(df["tenure"], errors="coerce")
    df["MonthlyCharges"] = pd.to_numeric(df["MonthlyCharges"], errors="coerce")
    df["Churned"] = (df["Churn"] == "Yes").astype(int)

    df["ShortContract"] = df["Contract"] == "Month-to-month"
    df["LowTenure"] = df["tenure"] < 12
    df["NewCustomer"] = df["tenure"] < 6
    df["HighCharge"] = df["MonthlyCharges"] > charge_hi
    df["VeryHighCharge"] = df["MonthlyCharges"] > charge_vhi

    raw_score = (
        df["ShortContract"] * 30
        + df["LowTenure"] * 25
        + df["HighCharge"] * 15
        + (df["TechSupport"] == "No") * 10
        + (df["InternetService"] == "Fiber optic") * 10
    )
    df["RiskScore"] = (raw_score * 90 / available_points).round().astype(int)
    df["RiskLevel"] = _risk_level(df["RiskScore"])
    return df.reset_index(drop=True)


def prepare_employees(df, available_points=95):
    df = df.copy()
    df["EmployeeNumber"] = df["EmployeeNumber"].astype(str)
    for c in ["JobSatisfaction", "YearsAtCompany", "MonthlyIncome", "WorkLifeBalance",
              "YearsSinceLastPromotion", "EnvironmentSatisfaction", "TrainingTimesLastYear"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["Left"] = (df["Attrition"] == "Yes").astype(int)

    dept_median = df.groupby("Department")["MonthlyIncome"].transform("median")
    df["BelowDeptMedian"] = df["MonthlyIncome"] < dept_median
    df["LowSatisfaction"] = _low_flag(df["JobSatisfaction"])
    df["LowWLB"] = _low_flag(df["WorkLifeBalance"])
    df["LowEnv"] = _low_flag(df["EnvironmentSatisfaction"])
    df["NewHire"] = df["YearsAtCompany"] < 3

    raw_score = (
        (df["OverTime"] == "Yes") * 30
        + df["LowSatisfaction"] * 20
        + df["NewHire"] * 20
        + df["BelowDeptMedian"] * 15
        + df["LowWLB"] * 10
    )
    df["RiskScore"] = (raw_score * 95 / available_points).round().astype(int)
    df["RiskLevel"] = _risk_level(df["RiskScore"])
    return df.reset_index(drop=True)


# =====================================================
# Demo data and session data
# =====================================================
@st.cache_data
def _demo_customers():
    raw = pd.read_csv("data/telco.csv")
    return prepare_customers(raw)


@st.cache_data
def _demo_employees():
    raw = pd.read_csv("data/hr.csv")
    return prepare_employees(raw)


def load_customers():
    if "custom_customers" in st.session_state:
        return st.session_state["custom_customers"].copy()
    return _demo_customers()


def load_employees():
    if "custom_employees" in st.session_state:
        return st.session_state["custom_employees"].copy()
    return _demo_employees()


# =====================================================
# Column matching for the user's own files
# =====================================================
def _pick(raw, m, field):
    c = m.get(field)
    if c and c not in (NOT_AVAILABLE, NO_ID) and c in raw.columns:
        return raw[c]
    return None


def _check_unique(ids, col):
    n_unique = ids.nunique()
    if n_unique < len(ids):
        raise ValueError(
            f"'{col}' cannot be used as an ID: it has only {n_unique:,} different values "
            f"in {len(ids):,} rows. Choose a different column, or choose '{NO_ID}'."
        )


def _get_ids(raw, col, prefix):
    """Use the chosen ID column, or create row numbers when the file has no ID."""
    if col in (None, NO_ID, NOT_AVAILABLE) or col not in raw.columns:
        ids = pd.Series([f"{prefix}{i + 1}" for i in range(len(raw))], index=raw.index)
        return raw, ids
    ids = as_text(raw[col])
    ok = ids.notna()
    raw, ids = raw[ok], ids[ok]
    _check_unique(ids, col)
    return raw, ids


def standardize_customers(raw, m, churn_values, short_values, tenure_unit="Months"):
    rows_in = len(raw)
    if _pick(raw, m, "Churn") is None:
        raise ValueError("Please choose the churn status column.")
    if not churn_values:
        raise ValueError("Select at least one value that means the customer LEFT.")

    raw = raw[raw[m["Churn"]].notna()]
    raw, ids = _get_ids(raw, m.get("customerID"), "C")
    if raw.empty:
        raise ValueError("No usable rows: every row is missing an ID or a churn status.")

    d = pd.DataFrame(index=raw.index)
    d["customerID"] = ids
    left = as_text(raw[m["Churn"]]).isin([str(v) for v in churn_values])
    d["Churn"] = left.map({True: "Yes", False: "No"})

    not_used = []
    pts = 0

    ct = _pick(raw, m, "Contract")
    if ct is not None and short_values:
        t = as_text(ct)
        d["Contract"] = t.where(~t.isin([str(v) for v in short_values]), "Month-to-month")
        d["Contract"] = d["Contract"].fillna("Not provided")
        pts += 30
    else:
        d["Contract"] = "Not provided" if ct is None else as_text(ct).fillna("Not provided")
        not_used.append("Contract type")

    tn = _pick(raw, m, "tenure")
    if tn is not None:
        v = pd.to_numeric(tn, errors="coerce")
        if tenure_unit == "Years":
            v = v * 12
        elif tenure_unit == "Days":
            v = v / 30.44
        d["tenure"] = v.round(1)
    else:
        d["tenure"] = float("nan")
    if d["tenure"].notna().any():
        pts += 25
    else:
        not_used.append("Tenure")

    mc = _pick(raw, m, "MonthlyCharges")
    d["MonthlyCharges"] = pd.to_numeric(mc, errors="coerce") if mc is not None else float("nan")
    if d["MonthlyCharges"].notna().any():
        pts += 15
    else:
        not_used.append("Monthly charges")

    if pts == 0:
        raise ValueError(
            "Match at least one of: contract type, tenure or monthly charges. "
            "Without them there is nothing to score."
        )

    d["TechSupport"] = "Unknown"
    d["InternetService"] = "Unknown"
    d["OnlineSecurity"] = "Unknown"
    d["PaymentMethod"] = "Unknown"
    d["SeniorCitizen"] = 0

    vals = d["MonthlyCharges"].dropna()
    hi, vhi = (vals.quantile(0.70), vals.quantile(0.85)) if len(vals) else (70.0, 80.0)
    prepared = prepare_customers(d, hi, vhi, pts)

    rate = float(prepared["Churned"].mean())
    if rate in (0.0, 1.0):
        raise ValueError(
            f"The churn rate comes out as {rate:.0%}. Check which values mean the customer LEFT."
        )

    info = {
        "rows_in": rows_in,
        "rows_used": len(prepared),
        "rate": rate,
        "high_risk": int(((prepared["Churned"] == 0) & (prepared["RiskLevel"] == "High")).sum()),
        "not_used": not_used,
        "points": pts,
    }
    return prepared, info


def standardize_employees(raw, m, left_values, overtime_yes_values,
                          tenure_unit="Years", higher_is_better=True):
    rows_in = len(raw)
    if _pick(raw, m, "Attrition") is None:
        raise ValueError("Please choose the attrition status column.")
    if not left_values:
        raise ValueError("Select at least one value that means the employee LEFT.")

    raw = raw[raw[m["Attrition"]].notna()]
    raw, ids = _get_ids(raw, m.get("EmployeeNumber"), "E")
    if raw.empty:
        raise ValueError("No usable rows: every row is missing an ID or an attrition status.")

    d = pd.DataFrame(index=raw.index)
    d["EmployeeNumber"] = ids
    left = as_text(raw[m["Attrition"]]).isin([str(v) for v in left_values])
    d["Attrition"] = left.map({True: "Yes", False: "No"})

    not_used = []
    pts = 0

    dept = _pick(raw, m, "Department")
    d["Department"] = as_text(dept).fillna("Not provided") if dept is not None else "Not provided"
    role = _pick(raw, m, "JobRole")
    d["JobRole"] = as_text(role).fillna("Not provided") if role is not None else "Not provided"

    ot = _pick(raw, m, "OverTime")
    if ot is not None and overtime_yes_values:
        t = as_text(ot)
        d["OverTime"] = t.isin([str(v) for v in overtime_yes_values]).map(
            {True: "Yes", False: "No"}
        ).where(t.notna(), "Unknown")
        pts += 30
    else:
        d["OverTime"] = "Unknown"
        not_used.append("Overtime")

    def rating(field):
        s = _pick(raw, m, field)
        if s is None:
            return float("nan")
        v = pd.to_numeric(s, errors="coerce")
        if not higher_is_better and v.notna().any():
            v = v.max() + v.min() - v
        return v

    d["JobSatisfaction"] = rating("JobSatisfaction")
    if d["JobSatisfaction"].notna().any():
        pts += 20
    else:
        not_used.append("Job satisfaction")

    yrs = _pick(raw, m, "YearsAtCompany")
    if yrs is not None:
        v = pd.to_numeric(yrs, errors="coerce")
        if tenure_unit == "Months":
            v = v / 12
        elif tenure_unit == "Days":
            v = v / 365.25
        d["YearsAtCompany"] = v.round(2)
    else:
        d["YearsAtCompany"] = float("nan")
    if d["YearsAtCompany"].notna().any():
        pts += 20
    else:
        not_used.append("Years at company")

    inc = _pick(raw, m, "MonthlyIncome")
    d["MonthlyIncome"] = pd.to_numeric(inc, errors="coerce") if inc is not None else float("nan")
    if d["MonthlyIncome"].notna().any():
        pts += 15
    else:
        not_used.append("Monthly income")

    d["WorkLifeBalance"] = rating("WorkLifeBalance")
    if d["WorkLifeBalance"].notna().any():
        pts += 10
    else:
        not_used.append("Work-life balance")

    if pts == 0:
        raise ValueError(
            "Match at least one of: overtime, job satisfaction, years at company, "
            "monthly income or work-life balance. Without them there is nothing to score."
        )

    d["YearsSinceLastPromotion"] = float("nan")
    d["BusinessTravel"] = "Not provided"
    d["EnvironmentSatisfaction"] = float("nan")
    d["TrainingTimesLastYear"] = float("nan")

    prepared = prepare_employees(d, pts)

    rate = float(prepared["Left"].mean())
    if rate in (0.0, 1.0):
        raise ValueError(
            f"The attrition rate comes out as {rate:.0%}. Check which values mean the employee LEFT."
        )

    info = {
        "rows_in": rows_in,
        "rows_used": len(prepared),
        "rate": rate,
        "high_risk": int(((prepared["Left"] == 0) & (prepared["RiskLevel"] == "High")).sum()),
        "not_used": not_used,
        "points": pts,
    }
    return prepared, info


# =====================================================
# Reasons and recommended actions
# =====================================================
def customer_reasons(row):
    r = []
    if row["ShortContract"]:
        r.append("Month-to-month contract")
    if row["LowTenure"]:
        r.append("Tenure under 12 months")
    if row["HighCharge"]:
        r.append("High monthly charges")
    if row["TechSupport"] == "No":
        r.append("No tech support")
    if row["InternetService"] == "Fiber optic":
        r.append("Fiber optic service")
    return ", ".join(r)


def customer_actions(row):
    a = []
    if row["ShortContract"]:
        if row["VeryHighCharge"]:
            a.append("Offer a discounted annual plan (high monthly bill)")
        elif row["NewCustomer"]:
            a.append("Welcome call and incentive to move to a longer plan")
        else:
            a.append("Offer a discounted annual plan")
    if row["TechSupport"] == "No" and row["InternetService"] != "No":
        a.append("Offer a free tech support trial")
    if row["OnlineSecurity"] == "No":
        a.append("Offer a free online security add-on")
    if row["PaymentMethod"] == "Electronic check":
        a.append("Encourage auto-pay with a small discount")
    if row["SeniorCitizen"] == 1:
        a.append("Assign a dedicated support contact")
    if row["InternetService"] == "Fiber optic" and row["HighCharge"]:
        a.append("Review the plan and offer a better-value bundle")
    if row["HighCharge"] and not row["ShortContract"]:
        a.append("Review the plan and offer a better-value option")
    if row["LowTenure"]:
        a.append("Onboarding check-in call")
    if not a:
        a.append("Personal follow-up call from the account team")
    return a


def employee_reasons(row):
    r = []
    if row["OverTime"] == "Yes":
        r.append("Works overtime")
    if row["LowSatisfaction"]:
        r.append("Low job satisfaction")
    if row["NewHire"]:
        r.append("Under 3 years at company")
    if row["BelowDeptMedian"]:
        r.append("Paid below department median")
    if row["LowWLB"]:
        r.append("Low work-life balance")
    return ", ".join(r)


def employee_actions(row):
    a = []
    if row["OverTime"] == "Yes":
        a.append("Manager 1:1 and workload review")
    if row["LowSatisfaction"]:
        a.append("Stay interview about job satisfaction")
    if row["BelowDeptMedian"]:
        a.append("HR to review pay against the department benchmark")
    if row["YearsSinceLastPromotion"] >= 4:
        a.append("Discuss career growth and promotion path")
    if row["LowWLB"]:
        a.append("Discuss flexible working options")
    if row["BusinessTravel"] == "Travel_Frequently":
        a.append("Review the travel load")
    if row["LowEnv"]:
        a.append("Check team and workplace environment")
    if row["NewHire"]:
        a.append("Mentoring and onboarding check-in")
    if row["TrainingTimesLastYear"] <= 1:
        a.append("Offer training and development opportunities")
    if not a:
        a.append("Manager check-in conversation")
    return a