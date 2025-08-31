import pandas as pd
import streamlit as st

@st.cache_data
def load_data():
    employees = pd.read_csv("employee.csv")       # <-- changed from employees.csv to employee.csv
    branches = pd.read_csv("branch.csv")
    transactions = pd.read_csv("transactions.csv")

    # Join employee with branch to get branch name
    df_emp_branch = pd.merge(employees, branches, on="BranchID", how="left")

    # Join transactions with employee-branch info
    df = pd.merge(transactions, df_emp_branch, on="EmployeeID", how="left")

    # Convert Date column to datetime and extract year, month
    df['Date'] = pd.to_datetime(df['Date'])
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month

    # Pivot transactions to separate revenue, expenses, salary amounts
    # Here, just aggregate amount by Type per employee, year, month
    df_pivot = df.pivot_table(
        index=['EmployeeID', 'EmployeeName', 'BranchName', 'Year', 'Month'],
        columns='Type',
        values='Amount',
        aggfunc='sum',
        fill_value=0
    ).reset_index()

    return df_pivot

st.title("Company Employee Dashboard (CSV Version)")

df = load_data()
st.dataframe(df)

st.write("### Summary by Branch")
branch_summary = df.groupby("BranchName")[["Expense", "Revenue", "Salary"]].sum()
st.table(branch_summary)
