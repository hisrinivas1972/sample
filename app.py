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

years = sorted([int(y) for y in df['Year'].dropna().unique()])
months = sorted([int(m) for m in df['Month'].dropna().unique()])

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

filtered_df = df.copy()
if selected_year != 0:
    filtered_df = filtered_df[filtered_df['Year'] == selected_year]
if selected_month != 0:
    filtered_df = filtered_df[filtered_df['Month'] == selected_month]

st.subheader("Detailed Transactions by Employee")
st.dataframe(filtered_df)

st.subheader("Summary by Branch")
branch_summary = filtered_df.groupby("BranchName")[['Expense', 'Revenue', 'Salary']].sum()
branch_summary['Net Income'] = branch_summary['Revenue'] - branch_summary['Expense'] - branch_summary['Salary']

# Format numbers nicely
formatted_summary = branch_summary.style.format({
    'Expense': '{:,.2f}',
    'Revenue': '{:,.2f}',
    'Salary': '{:,.2f}',
    'Net Income': '{:,.2f}'
})

st.table(formatted_summary)
