import pandas as pd
import streamlit as st

@st.cache_data
def load_data():
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

# Sidebar filters
years = sorted(df['Year'].dropna().unique())
months = sorted(df['Month'].dropna().unique())

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

# Apply filters
if selected_year != 0:
    df = df[df['Year'] == selected_year]
if selected_month != 0:
    df = df[df['Month'] == selected_month]

# Calculate Net Income per row
df['Net Income'] = df.get('Revenue', 0) - df.get('Expense', 0) - df.get('Salary', 0)

# Detailed transactions table
st.subheader("Detailed Transactions by Employee")
st.dataframe(df)

# Summary by branch with Net Income
st.subheader("Summary by Branch")
branch_summary = df.groupby("BranchName")[['Expense', 'Revenue', 'Salary', 'Net Income']].sum()
st.table(branch_summary.style.format("{:,.2f}"))

# Company Overview Dashboard
total_sales = df['Revenue'].sum()
total_expenses = df['Expense'].sum() + df['Salary'].sum()
net_income = total_sales - total_expenses
avg_customer_rating = 4.69  # Static example, replace if dynamic
total_branches = df['BranchName'].nunique()
top_performing_branches = (branch_summary['Net Income'] > 0).sum()
total_employees = df['EmployeeID'].nunique()

st.markdown("---")

with st.container():
    st.markdown("## Company Overview")
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Sales", f"${total_sales:,.0f}")
    col2.metric("Total Expenses", f"${total_expenses:,.0f}")
    col3.metric("Net Income", f"${net_income:,.0f}")
    col4.metric("Avg. Customer Rating", f"{avg_customer_rating:.2f}")

    col5, col6, col7 = st.columns(3)
    col5.metric("Total Branches", total_branches)
    col6.metric("Top Performing Branches", f"{top_performing_branches} / {total_branches}")
    col7.metric("Total Employees", total_employees)
