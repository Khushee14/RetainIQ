import sqlite3

import pandas as pd
import streamlit as st

st.set_page_config(page_title="SQL Insights", layout="wide")
st.title("SQL Insights")
st.caption("Each result below comes from a SQL query on the RetainIQ database.")

QUERIES = {
    "Customers: churn rate by contract": """
SELECT Contract,
       COUNT(*) AS customers,
       SUM(Churn = 'Yes') AS churned,
       ROUND(100.0 * SUM(Churn = 'Yes') / COUNT(*), 1) AS churn_pct
FROM customers
GROUP BY Contract
ORDER BY churn_pct DESC;
""",
    "Customers: monthly revenue lost to churn": """
SELECT Contract,
       ROUND(SUM(MonthlyCharges), 0) AS monthly_revenue_lost_usd
FROM customers
WHERE Churn = 'Yes'
GROUP BY Contract
ORDER BY monthly_revenue_lost_usd DESC;
""",
    "Customers: churn by tenure band": """
SELECT CASE
         WHEN tenure < 12 THEN '1. 0-11 months'
         WHEN tenure < 24 THEN '2. 12-23 months'
         WHEN tenure < 48 THEN '3. 24-47 months'
         ELSE '4. 48+ months'
       END AS tenure_band,
       COUNT(*) AS customers,
       ROUND(100.0 * SUM(Churn = 'Yes') / COUNT(*), 1) AS churn_pct
FROM customers
GROUP BY tenure_band
ORDER BY tenure_band;
""",
    "Employees: attrition by department": """
SELECT Department,
       COUNT(*) AS employees,
       SUM(Attrition = 'Yes') AS left_company,
       ROUND(100.0 * SUM(Attrition = 'Yes') / COUNT(*), 1) AS attrition_pct
FROM employees
GROUP BY Department
ORDER BY attrition_pct DESC;
""",
    "Employees: overtime vs attrition": """
SELECT OverTime,
       COUNT(*) AS employees,
       ROUND(100.0 * SUM(Attrition = 'Yes') / COUNT(*), 1) AS attrition_pct
FROM employees
GROUP BY OverTime;
""",
    "Employees: job roles ranked by attrition (window function)": """
SELECT JobRole,
       COUNT(*) AS employees,
       ROUND(100.0 * SUM(Attrition = 'Yes') / COUNT(*), 1) AS attrition_pct,
       RANK() OVER (ORDER BY 1.0 * SUM(Attrition = 'Yes') / COUNT(*) DESC) AS attrition_rank
FROM employees
GROUP BY JobRole
ORDER BY attrition_rank;
""",
}

choice = st.selectbox("Choose an analysis", list(QUERIES.keys()))
sql = QUERIES[choice]

st.code(sql, language="sql")

with sqlite3.connect("retainiq.db") as conn:
    result = pd.read_sql(sql, conn)

st.dataframe(result, use_container_width=True, hide_index=True)
