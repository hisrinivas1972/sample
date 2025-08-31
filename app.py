import pandas as pd
import streamlit as st

@st.cache_data
def load_data():
    # Load CSV files
    employees = pd.read_csv("employee.csv")
    branches = pd.read_csv("branch.csv")
    transactions = pd.read_csv("transactions.csv")

    # Merge employees with branches
    emp_branch = pd.merge(employees, branches, on='BranchID', how='left')

    # Merge transactions with employee + branch info
    df = pd.merge(transactions, emp_branch, on='EmployeeID', how='left')

    # Parse date
    df['Date'] = pd.to_datetime(df['Date'])
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month

    return df

# Load data
df = load_data()

st.title("Company Employee Dashboard with Transactions")

# Sidebar filters
years = sorted(df['Year'].unique())
months = sorted(df['Month'].unique())

selected_year = st.sidebar.selectbox("Select Year", [0] + years, format_func=lambda x: "All" if x == 0 else x)
selected_month = st.sidebar.selectbox("Select Month", [0] + months, format_func=lambda x: "All" if x == 0 else x)

# Apply filters
filtered_df = df.copy()
if selected_year != 0:
    filtered_df = filtered_df[filtered_df['Year'] == selected_year]
if selected_month != 0:
    filtered_df = filtered_df[filtered_df['Month'] == selected_month]

# Pivot for transaction summary per employee
pivot_df = filtered_df.pivot_table(
    index=['EmployeeID', 'EmployeeName', 'BranchName', 'Year', 'Month'],
    columns='Type',
    values='Amount',
    aggfunc='sum',
    fill_value=0
).reset_index()

# Display detailed transactions
st.subheader("Detailed Transactions by Employee")
st.dataframe(pivot_df)

# Summary by branch with Net Income
st.subheader("Summary by Branch")

branch_summary = pivot_df.groupby("BranchName")[['Expense', 'Revenue', 'Salary']].sum()
branch_summary["Net Income"] = branch_summary["Revenue"] - branch_summary["Expense"] - branch_summary["Salary"]
branch_summary = branch_summary.round(2)

st.table(branch_summary)
