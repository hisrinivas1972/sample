import pandas as pd
import streamlit as st

@st.cache_data
def load_data():
    # Load CSVs
    employees = pd.read_csv("employee.csv")
    branches = pd.read_csv("branch.csv")
    transactions = pd.read_csv("transactions.csv")

    # Merge employees with branches
    emp_branch = pd.merge(employees, branches, on='BranchID', how='left')

    # Merge transactions with full employee data
    df = pd.merge(transactions, emp_branch, on='EmployeeID', how='left')

    # Parse Date and extract Year, Month
    df['Date'] = pd.to_datetime(df['Date'])
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month

    # Pivot data for summary view
    pivot_df = df.pivot_table(
        index=['EmployeeID', 'EmployeeName', 'BranchName', 'Year', 'Month'],
        columns='Type',
        values='Amount',
        aggfunc='sum',
        fill_value=0
    ).reset_index()

    return pivot_df

# Streamlit UI
st.title("Company Employee Dashboard with Filters")

df = load_data()

# --- Sidebar Filters ---
st.sidebar.header("Filter Options")

# Year filter
years = sorted(df["Year"].unique())
selected_year = st.sidebar.selectbox("Select Year", ["All"] + [str(y) for y in years])

# Month filter
months = sorted(df["Month"].unique())
selected_month = st.sidebar.selectbox("Select Month", ["All"] + [str(m) for m in months])

# Apply filters
filtered_df = df.copy()

if selected_year != "All":
    filtered_df = filtered_df[filtered_df["Year"] == int(selected_year)]

if selected_month != "All":
    filtered_df = filtered_df[filtered_df["Month"] == int(selected_month)]

# --- Output ---
st.subheader("Detailed Transactions by Employee")
st.dataframe(filtered_df)

st.subheader("Summary by Branch")
branch_summary = filtered_df.groupby("BranchName")[["Expense", "Revenue", "Salary"]].sum()
st.table(branch_summary)
