import os

import streamlit as st

st.set_page_config(page_title="Power BI Dashboard", layout="wide")
st.title("Power BI Dashboard")
st.write(
    "The same customer data, scored in Python and visualised in Power BI "
    "with DAX measures (churn rate, high-risk customers, revenue at risk) "
    "and slicers for contract type and tenure."
)

path = "powerbi/customer_dashboard.png"
if os.path.exists(path):
    st.subheader("Customer Retention dashboard")
    st.image(path, width="stretch")
else:
    st.info("Add customer_dashboard.png to the powerbi folder to show it here.")

pbix = "powerbi/RetainIQ.pbix"
if os.path.exists(pbix):
    with open(pbix, "rb") as f:
        st.download_button(
            "Download the Power BI file (.pbix)",
            data=f.read(),
            file_name="RetainIQ.pbix",
            mime="application/octet-stream",
        )