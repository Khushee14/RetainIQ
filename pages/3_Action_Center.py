import pandas as pd
import plotly.express as px
import streamlit as st

from src.db import add_actions, apply_outcomes, clear_actions, load_actions, update_actions
from src.scoring import (
    customer_actions, customer_reasons,
    employee_actions, employee_reasons,
    load_customers, load_employees,
)

st.set_page_config(page_title="Action Center", layout="wide")
st.title("Action Center")
st.caption("Turn risk flags into a to-do list, then track what happened.")

st.info(
    "**How this page works**\n\n"
    "1. **Find** the people most at risk and see what to do for each one.\n"
    "2. **Add** them to your to-do list.\n"
    "3. **Update** the status as you work, and record the result (Retained or Left).\n"
    "4. **Review** progress and results at the bottom."
)
st.warning(
    "Suggestions are for a person to review. Nothing happens automatically. "
    "Employee scores must not be used alone for hiring, firing, promotion or pay decisions."
)
if "custom_customers" in st.session_state or "custom_employees" in st.session_state:
    st.info(
        "You are using your own uploaded data. Cases from the demo data may still be "
        "on your list, so use **Reset the to-do list** at the bottom before you start."
    )
STATUSES = ["Pending", "In Progress", "Done"]
OUTCOMES = ["", "Retained", "Left", "Unknown"]


def build_pool(kind):
    if kind == "Customers":
        df = load_customers()
        pool = df[(df["Churned"] == 0) & (df["RiskLevel"] == "High")].copy()
        id_col, act_fn, why_fn = "customerID", customer_actions, customer_reasons
        extra_sort = ["MonthlyCharges"]
    else:
        df = load_employees()
        pool = df[(df["Left"] == 0) & (df["RiskLevel"] == "High")].copy()
        id_col, act_fn, why_fn = "EmployeeNumber", employee_actions, employee_reasons
        extra_sort = []

    if pool.empty:
        return pool

    pool["entity_id"] = pool[id_col]
    plans = pool.apply(act_fn, axis=1)
    pool["why_flagged"] = pool.apply(why_fn, axis=1)
    pool["plan_list"] = plans
    pool["primary_action"] = plans.apply(lambda a: a[0])
    pool["suggested_action"] = plans.apply(lambda a: "; ".join(a[:3]))
    pool["n_actions"] = plans.apply(len)
    return pool.sort_values(["RiskScore", "n_actions"] + extra_sort, ascending=False)


# =====================================================
# STEP 1: Find who to help
# =====================================================
st.header("Step 1: Find who to help")
kind = st.radio("Who do you want to look at?", ["Customers", "Employees"], horizontal=True)
entity_type = "Customer" if kind == "Customers" else "Employee"
who = "customers" if kind == "Customers" else "employees"

pool = build_pool(kind)

if pool.empty:
    st.success("No high-risk cases found.")
else:
    st.write(
        f"**{len(pool):,} {who}** are currently flagged as high risk and have not left yet."
    )

    counts = pd.Series([x for lst in pool["plan_list"] for x in lst]).value_counts()
    counts = counts.head(6).reset_index()
    counts.columns = ["Suggested action", "Number of cases"]
    fig = px.bar(
        counts.sort_values("Number of cases"),
        x="Number of cases", y="Suggested action", orientation="h",
        title="Most common suggested actions", color_discrete_sequence=["#8e5bd0"],
    )
    fig.update_layout(height=320, margin=dict(t=50, b=10))
    st.plotly_chart(fig, width="stretch")

    options = ["All"] + sorted(pool["primary_action"].unique())
    chosen = st.selectbox("Show only cases whose main action is:", options)
    if chosen != "All":
        pool = pool[pool["primary_action"] == chosen]

    n = st.number_input(
        "How many of the highest-risk cases do you want to work on?",
        min_value=1, max_value=len(pool), value=min(10, len(pool)),
    )
    top = pool.head(int(n))

    st.dataframe(
        top[["entity_id", "RiskScore", "why_flagged", "suggested_action"]],
        width="stretch", hide_index=True,
        column_config={
            "entity_id": "ID",
            "RiskScore": st.column_config.NumberColumn("Risk score (max 100)"),
            "why_flagged": "Why flagged",
            "suggested_action": "What to do",
        },
    )

    # =====================================================
    # STEP 2: Add to the to-do list
    # =====================================================
    st.header("Step 2: Add them to your to-do list")
    if st.button(f"Add these {int(n)} {who} to my to-do list", key="add_cases"):
        added = add_actions(entity_type, top)
        st.success(f"Added {added} new cases. {int(n) - added} were already on your list.")

# =====================================================
# STEP 3: Work through the list
# =====================================================
st.header("Step 3: Work through your list")
actions = load_actions()

if actions.empty:
    st.write("Your to-do list is empty. Add cases in Step 2.")
    st.stop()

st.caption(
    "Click a cell to change it. **Status** shows how far along you are. "
    "**Result** is what happened in the end. Click **Save changes** when you finish editing."
)

edited = st.data_editor(
    actions,
    hide_index=True,
    width="stretch",
    key="tracker",
    column_order=["entity_type", "entity_id", "status", "outcome",
                  "owner", "suggested_action"],
    disabled=["action_id", "entity_type", "entity_id", "risk_score",
              "suggested_action", "created_date", "updated_date"],
    column_config={
        "entity_type": "Type",
        "entity_id": "ID",
        "suggested_action": "What to do",
        "status": st.column_config.SelectboxColumn("Status", options=STATUSES),
        "owner": st.column_config.TextColumn("Owner"),
        "outcome": st.column_config.SelectboxColumn(
            "Result", options=OUTCOMES,
            help="Retained = stayed. Left = churned or resigned. Unknown = not clear yet.",
        ),
    },
)

if st.button("Save changes", key="save_changes"):
    update_actions(edited)
    st.success("Saved.")


# =====================================================
# STEP 4: Review
# =====================================================
st.header("Step 4: Review progress and results")
actions = load_actions()

st.subheader("Progress")
p1, p2, p3, p4 = st.columns(4)
p1.metric("Cases on your list", len(actions))
p2.metric("Not started", int((actions["status"] == "Pending").sum()))
p3.metric("In progress", int((actions["status"] == "In Progress").sum()))
p4.metric("Completed", int((actions["status"] == "Done").sum()))

st.subheader("Results")
decided = actions[actions["outcome"].isin(["Retained", "Left"])]
n_dec = len(decided)
n_ret = int((decided["outcome"] == "Retained").sum())

done_no_result = int(
    ((actions["status"] == "Done") & (~actions["outcome"].isin(["Retained", "Left"]))).sum()
)

if n_dec == 0:
    st.info(
        "No results recorded yet. When you finish with someone, set their **Result** "
        "to Retained or Left in Step 3 and click Save. The retention success rate "
        "will appear here."
    )
else:
    r1, r2, r3 = st.columns(3)
    r1.metric("Cases with a result", n_dec)
    r2.metric("Retained", n_ret)
    r3.metric(
        "Retention success rate", f"{n_ret / n_dec:.0%}",
        help="Retained divided by (Retained + Left). Cases marked Unknown or blank are not counted.",
    )
    st.caption(f"{n_ret} of {n_dec} cases with a recorded result were retained.")

    if n_dec < 10:
        st.warning(
            f"Only {n_dec} results so far, so this percentage can jump around a lot. "
            "Treat it as a test of the tracking feature, not as a finding."
        )

    by_type = (
        decided.groupby("entity_type")["outcome"]
        .agg(cases="count", retained=lambda s: int((s == "Retained").sum()))
        .reset_index()
    )
    if len(by_type) > 1:
        by_type["success rate"] = (by_type["retained"] / by_type["cases"]).map("{:.0%}".format)
        st.dataframe(
            by_type.rename(columns={"entity_type": "Type", "cases": "Cases with a result",
                                    "retained": "Retained"}),
            hide_index=True, width="stretch",
        )

if done_no_result:
    st.warning(
        f"{done_no_result} cases are marked Done but have no Result. "
        "Set their Result so they count here."
    )

with st.expander("Reset the to-do list"):
    st.write("This deletes every case on your list so you can start fresh.")
    if st.button("Delete all cases", key="delete_all"):
        clear_actions()
        st.rerun()