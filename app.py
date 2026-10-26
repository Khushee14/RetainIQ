import os

import plotly.express as px
import streamlit as st

from src.scoring import load_customers, load_employees

st.set_page_config(
    page_title="RetainIQ — AI Attrition Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Modern CSS with Smooth Transitions & Glassmorphism ----------
st.markdown(
    """
    <style>
    /* Global Smooth Transition & Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(12px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 4rem;
        max-width: 1250px;
        animation: fadeIn 0.7s cubic-bezier(0.16, 1, 0.3, 1);
    }
    
    /* Hero Banner */
    .hero {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #9333ea 100%);
        padding: 3rem 2.5rem;
        border-radius: 24px;
        color: #fff;
        box-shadow: 0 20px 40px rgba(124, 58, 237, 0.25);
        border: 1px solid rgba(255, 255, 255, 0.15);
        position: relative;
        overflow: hidden;
    }
    .hero .title {
        font-size: 3.4rem !important;
        font-weight: 800;
        line-height: 1.1;
        color: #fff;
        letter-spacing: -1px;
        margin-bottom: 0.5rem;
    }
    .hero .tag {
        font-size: 1.15rem;
        opacity: 0.95;
        margin: 0.8rem 0 1.5rem 0;
        color: #ede9fe;
        line-height: 1.6;
    }
    .badge {
        display: inline-block;
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.25);
        padding: 0.4rem 1rem;
        border-radius: 999px;
        margin: 0 0.5rem 0.5rem 0;
        font-size: 0.88rem;
        font-weight: 600;
        color: #fff;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* Live KPI Cards with Hover Lift */
    .kpi {
        background: linear-gradient(145deg, rgba(124, 58, 237, 0.08) 0%, rgba(79, 70, 229, 0.12) 100%);
        border: 1px solid rgba(139, 92, 246, 0.25);
        border-radius: 18px;
        padding: 1.3rem 1.4rem;
        backdrop-filter: blur(10px);
        transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
    }
    .kpi:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 25px rgba(124, 58, 237, 0.15);
        border-color: rgba(139, 92, 246, 0.5);
    }
    .kpi .label {
        font-size: 0.85rem;
        opacity: 0.8;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .kpi .value {
        font-size: 2.1rem;
        font-weight: 800;
        margin-top: 0.2rem;
    }
    
    /* Interactive Section Cards */
    .card {
        background: linear-gradient(145deg, rgba(30, 27, 75, 0.4) 0%, rgba(15, 23, 42, 0.5) 100%);
        border: 1px solid rgba(139, 92, 246, 0.25);
        border-radius: 20px;
        padding: 1.8rem;
        min-height: 250px;
        backdrop-filter: blur(12px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.15);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 14px 32px rgba(124, 58, 237, 0.25);
        border-color: rgba(167, 139, 250, 0.6);
    }
    .card .head {
        font-size: 1.4rem;
        font-weight: 700;
        margin-bottom: 0.75rem;
        color: #fff;
    }
    .card ul {
        margin: 0;
        padding-left: 1.2rem;
        color: #cbd5e1;
        line-height: 1.7;
    }
    
    /* How it works Step Cards */
    .step {
        background: rgba(30, 27, 75, 0.35);
        border: 1px solid rgba(139, 92, 246, 0.2);
        border-radius: 16px;
        padding: 1.3rem;
        text-align: center;
        min-height: 150px;
        backdrop-filter: blur(8px);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .step:hover {
        transform: translateY(-3px);
        border-color: rgba(139, 92, 246, 0.4);
    }
    .step .num {
        font-size: 1.8rem;
        margin-bottom: 0.4rem;
    }
    .step .name {
        font-weight: 700;
        margin: 0.2rem 0;
        color: #fff;
    }
    .step .desc {
        font-size: 0.88rem;
        color: #94a3b8;
    }
    
    .foot {
        text-align: center;
        opacity: 0.8;
        font-size: 0.95rem;
        padding: 2.5rem 0 1rem 0;
        border-top: 1px solid rgba(139, 92, 246, 0.2);
        margin-top: 3rem;
        color: #cbd5e1;
    }
    
    h3 {
        color: #fff !important;
        font-weight: 700 !important;
        letter-spacing: -0.3px;
        margin-top: 1.5rem !important;
        margin-bottom: 1rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

cust = load_customers()
emp = load_employees()

# ---------- Hero ----------
hero_html = """
<div class="hero">
<div class="title">📊 RetainIQ</div>
<div class="tag">Know who is about to leave, understand why, and act before they go.<br>
One powerful platform for customer churn and employee attrition intelligence.</div>
<span class="badge">👥 Customer Retention</span>
<span class="badge">🧑‍💼 Employee Retention</span>
<span class="badge">⚡ Risk Scoring</span>
<span class="badge">📌 Action Tracking</span>
</div>
"""
hero_image = "assets/hero.jpg"
if os.path.exists(hero_image):
    left, right = st.columns([3, 2], gap="large")
    left.markdown(hero_html, unsafe_allow_html=True)
    right.image(hero_image, width="stretch")
else:
    st.markdown(hero_html, unsafe_allow_html=True)

st.write("")

# ---------- Live KPIs ----------
active_c = cust[cust["Churned"] == 0]
rev_risk = active_c[active_c["RiskLevel"] == "High"]["MonthlyCharges"].sum() * 12
active_e = emp[emp["Left"] == 0]

kpis = [
    ("Customers analysed", f"{len(cust):,}"),
    ("Churn rate", f"{cust['Churned'].mean():.1%}"),
    ("Annual revenue at risk", f"${rev_risk:,.0f}"),
    ("Employees analysed", f"{len(emp):,}"),
    ("Attrition rate", f"{emp['Left'].mean():.1%}"),
]
for col, (label, value) in zip(st.columns(5, gap="medium"), kpis):
    col.markdown(
        f'<div class="kpi"><div class="label">{label}</div><div class="value">{value}</div></div>',
        unsafe_allow_html=True,
    )

st.write("")

# ---------- Two modules ----------
st.subheader("🧭 Choose a section")
m1, m2 = st.columns(2, gap="large")

m1.markdown(
    """
<div class="card">
<div class="head">👥 Customer Retention</div>
<ul>
<li>Which customers are likely to leave, and why</li>
<li>Churn by contract, tenure and internet service</li>
<li>Annual revenue at risk</li>
<li>Suggested win-back actions per customer</li>
</ul>
</div>
""",
    unsafe_allow_html=True,
)
m1.write("")
m1.page_link("pages/1_Customer_Retention.py", label="Open Customer Retention", icon="👥")

m2.markdown(
    """
<div class="card">
<div class="head">🧑‍💼 Employee Retention</div>
<ul>
<li>Which employees may be at risk of resigning</li>
<li>Attrition by department, tenure and overtime</li>
<li>Risk flags for human review only</li>
<li>Suggested retention conversations for HR</li>
</ul>
</div>
""",
    unsafe_allow_html=True,
)
m2.write("")
m2.page_link("pages/2_Employee_Retention.py", label="Open Employee Retention", icon="🧑‍💼")

st.write("")

# ---------- How it works ----------
st.subheader("⚙️ How it works")
steps = [
    ("1️⃣", "Load data", "Customer and HR records"),
    ("2️⃣", "Score risk", "Explainable rule-based scores"),
    ("3️⃣", "Recommend", "A suggested action for each case"),
    ("4️⃣", "Track", "Status, owner and outcome"),
]
for col, (num, name, desc) in zip(st.columns(4, gap="medium"), steps):
    col.markdown(
        f'<div class="step"><div class="num">{num}</div><div class="name">{name}</div>'
        f'<div class="desc">{desc}</div></div>',
        unsafe_allow_html=True,
    )

st.write("")

# ---------- Key findings ----------
st.subheader("📈 Key findings from the data")
c1, c2 = st.columns(2, gap="large")

by_contract = cust.groupby("Contract")["Churned"].mean().reset_index()
fig1 = px.bar(
    by_contract, x="Contract", y="Churned",
    title="Customer churn rate by contract type",
    color_discrete_sequence=["#a78bfa"],
)
fig1.update_yaxes(tickformat=".0%", title="Churn rate")
fig1.update_layout(
    height=340,
    margin=dict(t=50, b=10, l=10, r=10),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#f3f4f6"),
    title_font=dict(size=15, color="#ffffff")
)
c1.plotly_chart(fig1, width="stretch")

by_dept = emp.groupby("Department")["Left"].mean().reset_index()
fig2 = px.bar(
    by_dept, x="Department", y="Left",
    title="Employee attrition rate by department",
    color_discrete_sequence=["#c084fc"],
)
fig2.update_yaxes(tickformat=".0%", title="Attrition rate")
fig2.update_layout(
    height=340,
    margin=dict(t=50, b=10, l=10, r=10),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#f3f4f6"),
    title_font=dict(size=15, color="#ffffff")
)
c2.plotly_chart(fig2, width="stretch")

# ---------- Tech and responsible use ----------
st.subheader("🛠️ Built with")
st.markdown(
    '<span class="badge" style="background:rgba(124, 58, 237, 0.2); border:1px solid rgba(139, 92, 246, 0.4)">Python</span>'
    '<span class="badge" style="background:rgba(124, 58, 237, 0.2); border:1px solid rgba(139, 92, 246, 0.4)">Pandas</span>'
    '<span class="badge" style="background:rgba(124, 58, 237, 0.2); border:1px solid rgba(139, 92, 246, 0.4)">SQL / SQLite</span>'
    '<span class="badge" style="background:rgba(124, 58, 237, 0.2); border:1px solid rgba(139, 92, 246, 0.4)">Streamlit</span>'
    '<span class="badge" style="background:rgba(124, 58, 237, 0.2); border:1px solid rgba(139, 92, 246, 0.4)">Plotly</span>'
    '<span class="badge" style="background:rgba(124, 58, 237, 0.2); border:1px solid rgba(139, 92, 246, 0.4)">Excel</span>'
    '<span class="badge" style="background:rgba(124, 58, 237, 0.2); border:1px solid rgba(139, 92, 246, 0.4)">Power BI</span>',
    unsafe_allow_html=True,
)

st.info(
    "**Responsible use:** risk scores show associations, not proven causes. "
    "Employee scores are for human review only and must not be used alone "
    "for hiring, firing, promotion or pay decisions."
)

st.markdown(
    '<div class="foot">Built by Khushi · MBA Business Analytics portfolio project</div>',
    unsafe_allow_html=True,
)