import pandas as pd
import streamlit as st
import altair as alt

# Use @st.cache_data for caching data transformations
@st.cache_data(allow_output_mutation=True)
def load_data():
    # Load the CSV files
    employees = pd.read_csv("employee.csv")
    branches = pd.read_csv("branch.csv")
    transactions = pd.read_csv("transactions.csv")

    # Merge datasets
    emp_branch = pd.merge(employees, branches, on='BranchID', how='left')
    df = pd.merge(transactions, emp_branch, on='EmployeeID', how='left')

    # Parse the 'Date' column
    df['Date'] = pd.to_datetime(df['Date'])
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month

    # Pivot table to get transaction sums by type per employee
    pivot_df = df.pivot_table(
        index=['EmployeeID', 'EmployeeName', 'BranchName', 'Year', 'Month'],
        columns='Type',
        values='Amount',
        aggfunc='sum',
        fill_value=0
    ).reset_index()

    # Flatten multi-index after pivot (if applicable)
    pivot_df.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in pivot_df.columns.values]

    # Convert columns to correct types
    pivot_df['BranchName'] = pivot_df['BranchName'].astype(str)
    pivot_df['Revenue'] = pd.to_numeric(pivot_df.get('Revenue', 0), errors='coerce').fillna(0)
    pivot_df['Expense'] = pd.to_numeric(pivot_df.get('Expense', 0), errors='coerce').fillna(0)
    pivot_df['Salary'] = pd.to_numeric(pivot_df.get('Salary', 0), errors='coerce').fillna(0)
    pivot_df['Net Income'] = pivot_df['Revenue'] - pivot_df['Expense'] - pivot_df['Salary']

    return pivot_df

# Load data
df = load_data()

st.title("Company Employee Dashboard with Transactions")

# Sidebar filters - Adding "All" as an option
years = sorted(df['Year'].dropna().unique())
months = sorted(df['Month'].dropna().unique())
branches = sorted(df['BranchName'].dropna().unique())
employees = sorted(df['EmployeeName'].dropna().unique())

# Select Year with "All" option
selected_year = st.sidebar.selectbox(
    "Select Year",
    options=["All"] + [str(year) for year in years],
    index=0
)

# Select Month with "All" option
month_names = {1:"Jan", 2:"Feb", 3:"Mar", 4:"Apr", 5:"May", 6:"Jun", 7:"Jul", 8:"Aug", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dec"}
selected_month = st.sidebar.selectbox(
    "Select Month",
    options=["All"] + [month_names[m] for m in months],
    index=0
)

# Select Branch with "All" option
selected_branches = st.sidebar.multiselect(
    "Select Branch(es)",
    options=["All"] + branches,
    default=["All"]
)

# Select Employee(s) with "All" option
selected_employees = st.sidebar.multiselect(
    "Select Employee(s)",
    options=["All"] + employees,
    default=["All"]
)

# Filter dataframe based on selections
filtered_df = df

if selected_year != "All":
    filtered_df = filtered_df[filtered_df['Year'] == int(selected_year)]

if selected_month != "All":
    month_num = [k for k, v in month_names.items() if v == selected_month][0]
    filtered_df = filtered_df[filtered_df['Month'] == month_num]

if selected_branches != ["All"]:
    filtered_df = filtered_df[filtered_df['BranchName'].isin(selected_branches)]

if selected_employees != ["All"]:
    filtered_df = filtered_df[filtered_df['EmployeeName'].isin(selected_employees)]

# Handle the interactive branch click (use session_state to store the clicked branch)
if 'clicked_branch' in st.session_state:
    clicked_branch = st.session_state.clicked_branch
    filtered_df = filtered_df[filtered_df['BranchName'] == clicked_branch]

# Calculate Net Income safely
filtered_df['Net Income'] = filtered_df.get('Revenue', 0) - filtered_df.get('Expense', 0) - filtered_df.get('Salary', 0)

# Show Company Overview Metrics
total_sales = filtered_df['Revenue'].sum()
total_expenses = filtered_df['Expense'].sum() + filtered_df['Salary'].sum()
net_income = total_sales - total_expenses
avg_customer_rating = 4.69  # example
total_branches = filtered_df['BranchName'].nunique()
top_performing_branches = filtered_df.groupby('BranchName')['Net Income'].sum().gt(0).sum()
total_employees = filtered_df['EmployeeID'].nunique()

# Show metrics in two rows
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

# Branch Summary with a bar chart
branch_summary = filtered_df.groupby("BranchName")[['Expense', 'Revenue', 'Salary', 'Net Income']].sum().reset_index()

st.subheader("Summary by Branch")

# Altair chart to show a clickable bar chart
click = alt.selection_single(
    fields=['BranchName'],
    bind='legend',  # binding to the legend so we can click on a legend item
    name="branch_click",
    clear="mouseout",  # clear the selection on mouseout
    empty="none"
)

chart = alt.Chart(branch_summary).mark_bar().encode(
    x='BranchName',
    y='Net Income',
    color=alt.condition(
        click,  # Change color when clicked
        alt.value("green"),
        alt.value("red")
    ),
    tooltip=['BranchName', 'Expense', 'Revenue', 'Salary', 'Net Income'],
    opacity=alt.condition(click, alt.value(1), alt.value(0.3))  # Highlight clicked bars
).add_selection(click).properties(width=700, height=400)

# Show the chart
st.altair_chart(chart, use_container_width=True)

# Listen for the click event and update the session state
if click.selected:
    selected_branch = click.selected["BranchName"]
    st.session_state.clicked_branch = selected_branch

# Show summary table with currency formatting
st.dataframe(branch_summary.style.format({
    'Expense': '${:,.2f}',
    'Revenue': '${:,.2f}',
    'Salary': '${:,.2f}',
    'Net Income': '${:,.2f}'
}))

st.markdown("---")

# Summary by Employee
st.subheader("Summary by Employee")

employee_summary = filtered_df.groupby("EmployeeName")[['Expense', 'Revenue', 'Salary', 'Net Income']].sum().reset_index()

# Show employee summary table with currency formatting
st.dataframe(employee_summary.style.format({
    'Expense': '${:,.2f}',
    'Revenue': '${:,.2f}',
    'Salary': '${:,.2f}',
    'Net Income': '${:,.2f}'
}))

st.markdown("---")

# Detailed Transactions by Employee
st.subheader("Detailed Transactions by Employee")

st.dataframe(filtered_df.style.format({
    'Revenue': '${:,.2f}',
    'Expense': '${:,.2f}',
    'Salary': '${:,.2f}',
    'Net Income': '${:,.2f}'
}))
