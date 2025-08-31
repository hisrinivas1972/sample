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
        index=['EmployeeID', 'EmployeeName', 'BranchName', 'Position', 'Year', 'Month'],
        columns='Type',
        values='Amount',
        aggfunc='sum',
        fill_value=0
    ).reset_index()

    # Compute Net Income per employee per period
    pivot_df['Net Income'] = pivot_df.get('Revenue', 0) - pivot_df.get('Expense', 0) - pivot_df.get('Salary', 0)

    # Add a dummy Customer Rating column (replace with real if available)
    pivot_df['Customer Rating'] = 4.5  # static example rating

    return pivot_df, branches

df, branches = load_data()

st.title("Branch Performance Dashboard")

# Select branch to analyze
branch_list = df['BranchName'].unique()
selected_branch = st.selectbox("Select Branch", branch_list)

branch_df = df[df['BranchName'] == selected_branch]

# Summary metrics for selected branch
total_sales = branch_df['Revenue'].sum()
total_expenses = branch_df['Expense'].sum() + branch_df['Salary'].sum()
net_income = total_sales - total_expenses
num_employees = branch_df['EmployeeID'].nunique()

# Employees needing review (example: net income < 0 or sales/expense ratio < 1)
employees_summary = branch_df.groupby(['EmployeeID', 'EmployeeName', 'Position']).agg({
    'Revenue': 'sum',
    'Expense': 'sum',
    'Salary': 'sum',
    'Net Income': 'sum'
}).reset_index()

employees_summary['Sales_Expense_Ratio'] = employees_summary.apply(
    lambda row: row['Revenue'] / row['Expense'] if row['Expense'] > 0 else float('inf'),
    axis=1
)

needs_review = employees_summary[(employees_summary['Net Income'] < 0) | (employees_summary['Sales_Expense_Ratio'] < 1)]
num_needs_review = needs_review.shape[0]

# Branch average rating (dummy avg from employees)
branch_avg_rating = branch_df['Customer Rating'].mean()

# Performance ratio (Sales / Expense)
performance_ratio = total_sales / total_expenses if total_expenses > 0 else float('inf')

# Show summary
st.header(f"Branch Overview: {selected_branch}")

cols = st.columns(3)
cols[0].metric("Branch Sales", f"${total_sales:,.0f}")
cols[1].metric("Branch Expenses", f"${total_expenses:,.0f}")
cols[2].metric("Branch Net Income", f"${net_income:,.0f}")

cols2 = st.columns(3)
cols2[0].metric("Employees", num_employees)
cols2[1].metric("Needs Review", f"{num_needs_review} Employee(s)")
cols2[2].metric("Performance (Sales/Expense)", f"{performance_ratio:.2f}X")

st.metric("Branch Avg. Rating", f"{branch_avg_rating:.2f}")

# 12-Month Performance Chart
st.subheader("12-Month Branch Performance")

# Aggregate monthly data for 12 months from latest date
latest_date = branch_df['Year'].max() * 100 + branch_df['Month'].max()  # e.g. 202508 for August 2025
months_to_show = 12

# Prepare monthly aggregated data
monthly_summary = branch_df.groupby(['Year', 'Month']).agg({
    'Expense': 'sum',
    'Revenue': 'sum'
}).reset_index()

monthly_summary['Net Sales'] = monthly_summary['Revenue'] - monthly_summary['Expense']

# Create a "YearMonth" for sorting and filtering last 12 months
monthly_summary['YearMonth'] = monthly_summary['Year'] * 100 + monthly_summary['Month']

monthly_summary = monthly_summary.sort_values('YearMonth').tail(months_to_show)

# Plot expenses, gross sales (Revenue), net sales by month
chart_data = monthly_summary.set_index(
    pd.to_datetime(monthly_summary['Year'].astype(str) + '-' + monthly_summary['Month'].astype(str))
)[['Expense', 'Revenue', 'Net Sales']]

st.line_chart(chart_data)

# Individual Employee Performance
st.subheader("Individual Employee Performance")

# Show employee detailed table
emp_display = employees_summary.copy()
emp_display['Status (Sales/Expense)'] = emp_display['Sales_Expense_Ratio'].apply(lambda x: f"{x:.2f}X")
emp_display['Customer Rating'] = branch_avg_rating  # static example

emp_display = emp_display[[
    'EmployeeName', 'Position', 'Revenue', 'Expense', 'Salary', 'Net Income', 'Status (Sales/Expense)', 'Customer Rating'
]]

emp_display.columns = ['Employee', 'Position', 'Sales', 'Expenses', 'Salary', 'Net Income', 'Status (Sales/Expense)', 'Customer Rating']

st.dataframe(emp_display.style.format({
    'Sales': '${:,.2f}',
    'Expenses': '${:,.2f}',
    'Salary': '${:,.2f}',
    'Net Income': '${:,.2f}',
    'Customer Rating': '{:.2f}',
    'Status (Sales/Expense)': '{}'
}))
