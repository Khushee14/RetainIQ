# RetainIQ — Customer Churn & Employee Attrition Intelligence

An interactive business analytics platform built with Python, Streamlit, SQL, and Power BI to analyze customer churn and employee attrition, identify risk levels, and generate actionable retention recommendations.

## 🚀 Key Features

### 1. Customer Retention Analytics
- Analyze customer churn patterns and retention metrics.
- Identify customers who may be at risk of leaving.
- Explore churn trends across contracts, services, and customer segments.
- Highlight potential churn drivers to support retention planning.

### 2. Employee Retention Analytics
- Analyze employee attrition patterns and workforce metrics.
- Identify employees with elevated attrition risk using available data.
- Explore relevant factors associated with employee turnover.
- Support HR teams in developing data-driven retention strategies.

### 3. Risk Scoring & Classification
- Calculate risk scores using the implemented scoring logic.
- Classify records into risk categories.
- Present relevant risk indicators to support decision-making.

### 4. Action Center
- Organize customer and employee retention interventions.
- Track follow-up actions and their status.
- Support structured retention planning for business teams.

### 5. SQL Insights
- Explore analytics derived from the SQLite database.
- Examine churn, attrition, and other available business metrics.
- Demonstrate how SQL supports business reporting and analysis.

### 6. Power BI Integration
- Export analytics datasets for Power BI reporting.
- Generate CSV or Excel reports using the available export utilities.
- Prepare data for additional business intelligence dashboards.

### 7. Custom Data Upload
- Upload supported datasets for analysis.
- Apply available scoring logic to compatible data.
- Explore retention insights using custom business data.

### 8. Learn From Data
- Explore analytical findings and relevant business insights.
- Understand how retention metrics can inform business decisions.

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| Streamlit | Interactive web application |
| Pandas | Data processing and analysis |
| NumPy | Numerical operations |
| SQLite | Database storage and SQL analysis |
| Plotly | Interactive visualizations |
| Matplotlib | Data visualization |
| Power BI | Business intelligence reporting |
| CSV / Excel | Data export and reporting |

## 📂 Project Structure

```text
retainiq/
│
├── app.py
├── explore.py
├── setup_db.py
├── export_powerbi.py
├── requirements.txt
├── README.md
├── retainiq.db
│
├── data/
│   └── Raw datasets
│
├── pages/
│   ├── 1_Customer_Retention.py
│   ├── 2_Employee_Retention.py
│   ├── 3_Action_Center.py
│   ├── 4_SQL_Insights.py
│   ├── 5_Power_BI_Dashboard.py
│   ├── 6_Use_Your_Own_Data.py
│   └── 7_Learn_From_Data.py
│
├── src/
│   ├── __init__.py
│   ├── db.py
│   ├── exports.py
│   └── scoring.py
│
└── powerbi/
    └── Exported reporting datasets
```

*Note: The structure above describes the intended project organization. The actual contents of each directory depend on the files included in your repository.*

## ⚙️ Installation and Setup

### Prerequisites

Make sure you have the following installed:

- Python 3.9 or later
- Git (optional, for cloning the repository)
- Visual Studio Code (recommended)

### Step 1: Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd retainiq
```

Alternatively, download the repository as a ZIP file and extract it.

### Step 2: Create a Virtual Environment

**Windows:**

```bash
python -m venv venv
```

Activate the environment:

```bash
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Initialize the Database

If the database needs to be created or initialized, run:

```bash
python setup_db.py
```

If your repository already contains a populated `retainiq.db`, check the database setup script before running it to ensure existing data will not be overwritten.

### Step 5: Launch the Application

```bash
streamlit run app.py
```

Streamlit will display a local URL, usually:

```text
http://localhost:8501
```

Open this address in your browser to use RetainIQ.

## 📊 Business Value

RetainIQ demonstrates how data analytics can support retention-related business decisions.

**For customer success teams:**
- Identify customer segments with elevated churn risk.
- Understand patterns associated with customer churn.
- Prioritize retention outreach and follow-up actions.

**For HR teams:**
- Examine employee attrition patterns.
- Identify workforce segments requiring further investigation.
- Support employee engagement and retention planning.

**For business analysts:**
- Explore business data using Python, SQL, and interactive dashboards.
- Generate structured reports for business intelligence tools.
- Translate analytical findings into actionable recommendations.

## 🔄 Application Workflow

```text
Business Data
     ↓
Data Processing & Validation
     ↓
Risk Scoring & Analytics
     ↓
Interactive Streamlit Dashboards
     ↓
Retention Recommendations
     ↓
Action Tracking & Reporting
     ↓
Power BI / CSV / Excel Exports
```

## 🎯 Project Objectives

- Combine customer churn and employee attrition analytics in one platform.
- Demonstrate practical applications of Python, SQL, and business analytics.
- Present retention-related insights through interactive dashboards.
- Support data-informed prioritization and retention planning.
- Connect analytical outputs with reporting and follow-up workflows.

## 🔒 Data & Privacy

- Use authorized datasets and remove unnecessary personal information before uploading data.
- Do not commit passwords, API keys, confidential business data, or sensitive employee/customer records to GitHub.
- Review database contents and exported files before publishing the repository.
- This project is an analytics and decision-support tool, not a substitute for human judgment.

## ⚠️ Limitations

- Risk scores depend on the available dataset and the scoring logic implemented in the application.
- Risk classifications should not automatically be interpreted as statistically validated machine learning predictions.
- Retention recommendations require business context and human review.
- Compatibility with custom datasets depends on the application's implemented validation and scoring requirements.
- Production deployment requires additional testing, security controls, access management, and performance validation.

## 🚀 Future Enhancements

- Integrate validated machine learning models for churn and attrition prediction.
- Add model evaluation metrics such as precision, recall, F1-score, and ROC-AUC where applicable.
- Improve explainability with feature importance and model-specific explanation methods.
- Introduce role-based access for HR and customer success teams.
- Add scheduled reporting and deployment to a hosted environment.
- Enhance intervention tracking with measurable retention outcomes.

## 👩‍💻 Built With

**RetainIQ — Turning retention data into actionable business insights.**

Developed as a business analytics project exploring customer retention, employee attrition, SQL, Python, and interactive business intelligence.

---

*Disclaimer: RetainIQ is intended for analytical and educational purposes. Its predictive capabilities and production readiness depend on the actual implementation, data quality, and validation performed.*