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

    # Parse 'Date' only if present
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month

    # Pivot: Sum Amounts by Type (Revenue, Expense, Salary)
    pivot_df = df.pivot_table(
        index=['EmployeeID', 'EmployeeName', 'BranchName', 'Year', 'Month'],
        columns='Type',
        values='Amount',
        aggfunc='sum',
        fill_value=0
    ).reset_index()

    return pivot_df

# Streamlit UI
st.title("Company Employee Dashboard with Transactions")

df = load_data()

# Detailed table
st.subheader("Detailed Transactions by Employee")
st.dataframe(df)

# Branch summary
st.subheader("Summary by Branch")
branch_summary = df.groupby("BranchName")[['Expense', 'Revenue', 'Salary']].sum()
st.table(branch_summary)
