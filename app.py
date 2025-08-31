import pandas as pd
import streamlit as st
import altair as alt

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

df = load_data()

st.title("Company Employee Dashboard with Transactions")

# Sidebar filters - multi-select instead of single select for better filtering
years = sorted(df['Year'].dropna().unique())
months = sorted(df['Month'].dropna().unique())
branches = sorted(df['BranchName'].dropna().unique())

selected_years = st.sidebar.multiselect("Select Year(s)", options=years, default=years)
selected_months = st.sidebar.multiselect("Select Month(s)", options=months, default=months)
selected_branches = st.sidebar.multiselect("Select Branch(es)", options=branches, default=branches)

filtered_df = df[
    (df['Year'].isin(selected_years)) &
    (df['Month'].isin(selected_months)) &
    (df['BranchName'].isin(selected_branches))
]

# Calculate Net Income safely
filtered_df['Net Income'] = filtered_df.get('Revenue', 0) - filtered_df.get('Expense', 0) - filtered_df.get('Salary', 0)

# Company Overview Metrics
total_sales = filtered_df['Revenue'].sum()
total_expenses = filtered_df['Expense'].sum() + filtered_df['Salary'].sum()
net_income = total_sales - total_expenses
avg_customer_rating = 4.69  # hardcoded example
total_branches = filtered_df['BranchName'].nunique()
top_performing_branches = filtered_df.groupby('BranchName')['Net Income'].sum().gt(0).sum()
total_employees = filtered_df['EmployeeID'].nunique()

# Show metrics in two rows for better spacing
with st.container():
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Sales", f"${total_sales:,.0f}")
    col2.metric("Total Expenses", f"${total_expenses:,.0f}")
    col3.metric("Net Income", f"${net_income:,.0f}")
    col4.metric("Avg. Customer Rating", f"{avg_customer_rating:.2f}")

    col5, col6, col7 = st.columns(3)
    col5.metric("Total Branches", total_branches)
    col6.metric("Top Performing Branches", f"{top_performing_branches} / {total_branches}")
    col7.metric("Total Employees", total_employees)

st.markdown("---")

# Summary by Branch with a bar chart and table
branch_summary = filtered_df.groupby("BranchName")[['Expense', 'Revenue', 'Salary', 'Net Income']].sum().reset_index()

st.subheader("Summary by Branch")

# Bar chart for Net Income by Branch using Altair (interactive like Power BI)
chart = alt.Chart(branch_summary).mark_bar().encode(
    x='BranchName',
    y='Net Income',
    color=alt.condition(
        alt.datum['Net Income'] > 0,
        alt.value("green"),
        alt.value("red")
    ),
    tooltip=['BranchName', 'Expense', 'Revenue', 'Salary', 'Net Income']
).properties(width=700, height=400)

st.altair_chart(chart, use_container_width=True)

# Show table with formatting
st.dataframe(branch_summary.style.format({
    'Expense': '${:,.2f}',
    'Revenue': '${:,.2f}',
    'Salary': '${:,.2f}',
    'Net Income': '${:,.2f}'
}))

st.markdown("---")

# Detailed Transactions by Employee with sorting and filtering
st.subheader("Detailed Transactions by Employee")

st.dataframe(filtered_df.style.format({
    'Revenue': '${:,.2f}',
    'Expense': '${:,.2f}',
    'Salary': '${:,.2f}',
    'Net Income': '${:,.2f}'
}))

