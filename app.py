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

    # Pivot to get sums of Amount by Type (Revenue, Expense, Salary) per Employee per Year/Month
    pivot_df = df.pivot_table(
        index=['EmployeeID', 'EmployeeName', 'BranchName', 'Year', 'Month'],
        columns='Type',
        values='Amount',
        aggfunc='sum',
        fill_value=0
    ).reset_index()

    return pivot_df

st.title("Company Employee Dashboard with Transactions")

df = load_data()

# Clean years and months lists for sidebar selectboxes
years = sorted(df['Year'].dropna().astype(int).unique().tolist())
months = sorted(df['Month'].dropna().astype(int).unique().tolist())

selected_year = st.sidebar.selectbox(
    "Select Year",
    [0] + years,
    format_func=lambda x: "All" if x == 0 else str(x)
)

selected_month = st.sidebar.selectbox(
    "Select Month",
    [0] + months,
    format_func=lambda x: "All" if x == 0 else str(x)
)

# Filter data based on selection
filtered_df = df.copy()
if selected_year != 0:
    filtered_df = filtered_df[filtered_df['Year'] == selected_year]
if selected_month != 0:
    filtered_df = filtered_df[filtered_df['Month'] == selected_month]

# Show detailed transaction info by employee and month
st.subheader("Detailed Transactions by Employee")
st.dataframe(filtered_df)

# Summary by Branch
st.subheader("Summary by Branch")
branch_summary = filtered_df.groupby("BranchName")[['Expense', 'Revenue', 'Salary']].sum()

# Calculate Net Income = Revenue - Expense - Salary
branch_summary['Net Income'] = branch_summary['Revenue'] - branch_summary['Expense'] - branch_summary['Salary']

# Format numbers nicely
branch_summary = branch_summary.style.format({
    'Expense': "${:,.2f}",
    'Revenue': "${:,.2f}",
    'Salary': "${:,.2f}",
    'Net Income': "${:,.2f}"
})

st.table(branch_summary)
