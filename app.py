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

    # Calculate Net Income
    pivot_df['Net Income'] = pivot_df.get('Revenue', 0) - pivot_df.get('Expense', 0) - pivot_df.get('Salary', 0)

    # Dummy customer rating for example
    pivot_df['Customer Rating'] = 4.5

    return pivot_df, branches

# Load data
df, branches = load_data()

st.title("Company Employee Dashboard with Transactions")

# Sidebar filters for Year and Month
years = sorted(df['Year'].unique().tolist())
selected_year = st.sidebar.selectbox("Select Year", [0] + years, format_func=lambda x: "All" if x == 0 else x)

months = sorted(df['Month'].unique().tolist())
selected_month = st.sidebar.selectbox("Select Month", [0] + months, format_func=lambda x: "All" if x == 0 else x)

# Filter dataframe by selected year and month
filtered_df = df.copy()
if selected_year != 0:
    filtered_df = filtered_df[filtered_df['Year'] == selected_year]
if selected_month != 0:
    filtered_df = filtered_df[filtered_df['Month'] == selected_month]

# Show detailed transactions by employee
st.subheader("Detailed Transactions by Employee")
st.dataframe(filtered_df)

# Summary by Branch
st.subheader("Summary by Branch")
branch_summary = filtered_df.groupby("BranchName")[['Expense', 'Revenue', 'Salary', 'Net Income']].sum()
st.table(branch_summary)

# Company Overview Metrics
st.subheader("Company Overview")

total_sales = filtered_df['Revenue'].sum()
total_expenses = filtered_df['Expense'].sum()
net_income = filtered_df['Net Income'].sum()
avg_customer_rating = filtered_df['Customer Rating'].mean()
total_branches = branches['BranchID'].nunique()
total_employees = filtered_df['EmployeeID'].nunique()
top_performing_branches = (branch_summary['Net Income'] > 0).sum()

col1, col2, col3 = st.columns(3)
col1.metric("Total Sales", f"${total_sales:,.2f}")
col2.metric("Total Expenses", f"${total_expenses:,.2f}")
col3.metric("Net Income", f"${net_income:,.2f}")

col4, col5, col6 = st.columns(3)
col4.metric("Avg. Customer Rating", f"{avg_customer_rating:.2f}")
col5.metric("Total Branches", f"{total_branches}")
col6.metric("Top Performing Branches", f"{top_performing_branches} / {total_branches}")

st.metric("Total Employees", f"{total_employees}")
