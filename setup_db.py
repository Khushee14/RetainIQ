import sqlite3
import pandas as pd

conn = sqlite3.connect("retainiq.db")

customers = pd.read_csv("data/telco.csv")
customers["TotalCharges"] = pd.to_numeric(customers["TotalCharges"], errors="coerce").fillna(0)
customers.to_sql("customers", conn, if_exists="replace", index=False)

employees = pd.read_csv("data/hr.csv")
employees.to_sql("employees", conn, if_exists="replace", index=False)

conn.close()
print("Tables created: customers, employees")