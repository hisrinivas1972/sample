import pandas as pd
import streamlit as st

@st.cache_data
def load_data():
    employees = pd.read_csv("employee.csv")
    branches = pd.read_csv("branch.csv")
    transactions = pd.read_csv("transactions.csv")

    emp_branch = pd.merge(employees, branches, on='BranchID', how='left')
    df = pd.merge(transactions, emp_branch, on='EmployeeID', how='left')

    df['Date'] = pd.to_datetime(df['Date'])
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month

    pivot_df = df.pivot_table(
        index=['EmployeeID', 'EmployeeName', 'BranchName', 'Year', 'Month'],
        columns='Type',
        values='Amount',
        aggfunc='sum',
        fill_value=0
    ).reset_index()

    return pivot_df, employees, branches

# Load all data
df, employees, branches = load_data()

# Sidebar filters for year/month
years = sorted(df['Year'].dropna().unique())
months = sorted(df['Month'].dropna().unique())

selected_year = st.sidebar.selectbox(
    "Select Year",
    [0] + years.tolist(),
    format_func=lambda x: "All" if x == 0 else str(x)
)

selected_month = st.sidebar.selectbox(
    "Select Month",
    [0] + months.tolist(),
    format_func=lambda x: "All" if x == 0 else str(x)
)

filtered_df = df.copy()
if selected_year != 0:
    filtered_df = filtered_df[filtered_df['Year'] == selected_year]
if selected_month != 0:
    filtered_df = filtered_df[filtered_df['Month'] == selected_month]

# Calculate KPIs for dashboard
total_sales = filtered_df['Revenue'].sum()
total_expenses = filtered_df['Expense'].sum()
total_salary = filtered_df['Salary'].sum()
net_income = total_sales - total_expenses - total_salary

total_branches = branches['BranchID'].nunique()
total_employees = employees['EmployeeID'].nunique()

# For demo, assuming Avg Customer Rating fixed as 4.69 (no data in your CSV)
avg_customer_rating = 4.69

# For Top Performing Branches, just show branches with positive net income count
branch_summary = filtered_df.groupby('BranchName')[['Revenue', 'Expense', 'Salary']].sum()
branch_summary['Net Income'] = branch_summary['Revenue'] - branch_summary['Expense'] - branch_summary['Salary']
top_performing_count = (branch_summary['Net Income'] > 0).sum()
total_branches_count = branch_summary.shape[0]

# Streamlit layout: Dashboard KPIs using columns for nice side-by-side cards
st.title("Company Overview")
st.subheader("Performance Dashboard")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Sales", f"${total_sales:,.0f}")
col2.metric("Total Expenses", f"${total_expenses + total_salary:,.0f}")  # Expenses + Salary as total cost
col3.metric("Net Income", f"${net_income:,.0f}")
col4.metric("Avg. Customer Rating", f"{avg_customer_rating:.2f}")

col5, col6, col7 = st.columns(3)
col5.metric("Total Branches", total_branches)
col6.metric("Top Performing Branches", f"{top_performing_count} / {total_branches_count}")
col7.metric("Total Employees", total_employees)

# Show detailed transactions below
st.subheader("Detailed Transactions by Employee")
st.dataframe(filtered_df)

# Summary by Branch with formatting
st.subheader("Summary by Branch")
formatted_summary = branch_summary.style.format({
    'Expense': '{:,.2f}',
    'Revenue': '{:,.2f}',
    'Salary': '{:,.2f}',
    'Net Income': '{:,.2f}'
})
st.table(formatted_summary)
