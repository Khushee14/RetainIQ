import os

from src.scoring import load_customers, load_employees

os.makedirs("powerbi", exist_ok=True)

customers = load_customers()
customers["RiskLevel"] = customers["RiskLevel"].astype(str)
customers.to_csv("powerbi/customers_scored.csv", index=False)

employees = load_employees()
employees["RiskLevel"] = employees["RiskLevel"].astype(str)
employees.to_csv("powerbi/employees_scored.csv", index=False)

print("Exported to powerbi/ folder")
