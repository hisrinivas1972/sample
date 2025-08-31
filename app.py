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

    # Merge transactions with employee-branch info
    df = pd.merge(transactions, emp_branch, on='EmployeeID', how='left')

    # Parse 'Date' and extract Year and Month
    df['Date'] = pd.to_datetime(df['Date'])
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month

    # Pivot to get sums of Amount by Type per Employee per Year/Month
    pivot_df = df.pivot_table(
        index=['EmployeeID', 'EmployeeName', 'BranchName', 'Year', 'Month'],
        columns='Type',
        values='Amount',
        aggfunc='sum',
        fill_value=0
    ).reset_index()

    return pivot_df

# Streamlit App
st.title("📊 Company Employee Dashboard with Transactions")

df = load_data()

# --- 📅 Filter Section ---
st.sidebar.header("Filter by Date")

# Get unique years and months
years = sorted(df["Year"].unique())
months = sorted(df["Month"].unique())

# Year and Month filters
selected_year = st.sidebar.selectbox("Select Year", years)
selected_month = st.sidebar.selectbox("Select Month", [0] + months, format_func=lambda x: "All" if x == 0 else x)

# Apply filters
if selected_month == 0:
    filtered_df = df[df["Year"] == selected_year]
else:
    filtered_df = df[(df["Year"] == selected_year) & (df["Month"] == selected_month)]

# --- 📋 Detailed View ---
st.subheader(f"Detailed Transactions for {selected_year}" + (f", Month {selected_month}" if selected_month else ""))
st.dataframe(filtered_df)

# --- 📌 Summary by Branch ---
st.subheader("Summary by Branch")
branch_summary = filtered_df.groupby("BranchName")[['Expense', 'Revenue', 'Salary']].sum()
st.table(branch_summary)
