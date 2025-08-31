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

    return pivot_df

st.title("Company Employee Dashboard with Transactions")

df = load_data()

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

if selected_year != 0:
    df = df[df['Year'] == selected_year]
if selected_month != 0:
    df = df[df['Month'] == selected_month]

df['Net Income'] = df.get('Revenue', 0) - df.get('Expense', 0) - df.get('Salary', 0)

# Calculate summaries for company overview
total_sales = df['Revenue'].sum()
total_expenses = df['Expense'].sum() + df['Salary'].sum()
net_income = total_sales - total_expenses
avg_customer_rating = 4.69  # static for now
total_branches = df['BranchName'].nunique()
top_performing_branches = (df.groupby('BranchName')['Net Income'].sum() > 0).sum()
total_employees = df['EmployeeID'].nunique()

# Show overview metrics
st.markdown("## Company Overview")
cols = st.columns(4)
cols[0].metric("Total Sales", f"${total_sales:,.0f}")
cols[1].metric("Total Expenses", f"${total_expenses:,.0f}")
cols[2].metric("Net Income", f"${net_income:,.0f}")
cols[3].metric("Avg. Customer Rating", f"{avg_customer_rating:.2f}")

cols2 = st.columns(3)
cols2[0].metric("Total Branches", total_branches)
cols2[1].metric("Top Performing Branches", f"{top_performing_branches} / {total_branches}")
cols2[2].metric("Total Employees", total_employees)

# Let user pick which detail to view
option = st.radio(
    "Select detail to view",
    ('Detailed Transactions', 'Summary by Branch', 'Total Sales Details', 'Total Expenses Details', 'Net Income Details')
)

if option == 'Detailed Transactions':
    st.subheader("Detailed Transactions by Employee")
    st.dataframe(df)

elif option == 'Summary by Branch':
    st.subheader("Summary by Branch")
    branch_summary = df.groupby("BranchName")[['Expense', 'Revenue', 'Salary', 'Net Income']].sum()
    st.table(branch_summary.style.format("{:,.2f}"))

elif option == 'Total Sales Details':
    st.subheader("Total Sales Details")
    sales_by_branch = df.groupby("BranchName")['Revenue'].sum().sort_values(ascending=False)
    st.bar_chart(sales_by_branch)

elif option == 'Total Expenses Details':
    st.subheader("Total Expenses Details")
    expenses_by_branch = df.groupby("BranchName")[['Expense', 'Salary']].sum()
    expenses_by_branch['Total Expenses'] = expenses_by_branch.sum(axis=1)
    st.bar_chart(expenses_by_branch['Total Expenses'])

elif option == 'Net Income Details':
    st.subheader("Net Income Details")
    net_income_by_branch = df.groupby("BranchName")['Net Income'].sum().sort_values(ascending=False)
    st.bar_chart(net_income_by_branch)
