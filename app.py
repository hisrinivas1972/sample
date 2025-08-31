import pandas as pd
import streamlit as st

# Cache data loading for speed
@st.cache_data
def load_data():
    employees = pd.read_csv("employees.csv")
    branches = pd.read_csv("branches.csv")
    transactions = pd.read_csv("transactions.csv")

    # Merge employees with branches
    emp_branch = pd.merge(employees, branches, on="BranchID", how="left")

    # Merge transactions with employees & branches
    df = pd.merge(transactions, emp_branch, on="EmployeeID", how="left")

    # Convert Date column to datetime
    df['Date'] = pd.to_datetime(df['Date'])

    return df

st.title("Company Employee Transactions Dashboard")

df = load_data()

st.write("### Raw Data")
st.dataframe(df)

# Summary by Branch and Type (Revenue, Expense, Salary)
st.write("### Summary by Branch and Transaction Type")
summary = df.groupby(['BranchName', 'Type'])['Amount'].sum().reset_index()
st.dataframe(summary)

# Optional: Filter by Branch
branch_filter = st.selectbox("Select Branch", options=["All"] + df['BranchName'].dropna().unique().tolist())
if branch_filter != "All":
    filtered_df = df[df['BranchName'] == branch_filter]
else:
    filtered_df = df

st.write(f"### Transactions for Branch: {branch_filter}")
st.dataframe(filtered_df)
