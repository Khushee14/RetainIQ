import pandas as pd

df = pd.read_csv("data/telco.csv")

print(df.shape)
churn_rate = (df["Churn"] == "Yes").mean()
print(f"Churn rate: {churn_rate:.1%}")
print(df.groupby("Contract")["Churn"].apply(lambda s: (s == "Yes").mean()))
print(df.columns.tolist())
print(df.head())