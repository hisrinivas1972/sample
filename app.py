import pandas as pd
import streamlit as st

@st.cache_data
def load_data():
    # Load CSV files
    employees = pd.read_csv("employee.csv")
    branches = pd.read_csv("branch.csv")
    transactions = pd.read_csv("transactions.csv")

    # Merge employees with branches to get branch names
    emp_branch = pd.merge(employees, branches, on='BranchID', how='left')

    # LEFT JOIN: Include all employees even if they don't have transactions
    df = pd.merge(emp_branch, transactions, on='EmployeeID', how='left')

    # Parse 'Date' safely
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month

    # Pivot table for transaction types
    pivot_df = df.pivot_table(
        index=['EmployeeID', 'EmployeeName', 'BranchID', 'BranchName', 'Year', 'Month'],
        columns='Type',
        values='Amount',
        aggfunc='sum',
        fill_value=0
    ).reset_index()

    return pivot_df, branches

# Streamlit UI
st.title("Company Employee Dashboard with Transactions")

df, branches = load_data()

# Show all employee-level transactions
st.subheader("Detailed Transactions by Employee")
st.dataframe(df)

# Create summary by branch (include all branches)
st.subheader("Summary by Branch")
branch_summary = df.groupby(['BranchID', 'BranchName'])[['Expense', 'Revenue', 'Salary']].sum().reset_index()

# Ensure all branches appear, even if no transactions
full_summary = pd.merge(branches, branch_summary, on=['BranchID', 'BranchName'], how='left').fillna(0)

st.table(full_summary)
