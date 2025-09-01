import pandas as pd
import streamlit as st
import altair as alt

st.set_page_config(page_title="Employee Dashboard", layout="wide")
st.title("📊 Company Employee Dashboard with Transactions")

# --- Sidebar: File Uploads ---
st.sidebar.header("📤 Upload CSV Files")

uploaded_employees = st.sidebar.file_uploader("Upload Employees CSV", type="csv")
uploaded_branches = st.sidebar.file_uploader("Upload Branches CSV", type="csv")
uploaded_transactions = st.sidebar.file_uploader("Upload Transactions CSV", type="csv")

# --- Function to Load and Process Data ---
def load_data(emp_file, branch_file, trans_file):
    employees = pd.read_csv(emp_file)
    branches = pd.read_csv(branch_file)
    transactions = pd.read_csv(trans_file)

    # Merge datasets
    emp_branch = pd.merge(employees, branches, on='BranchID', how='left')
    df = pd.merge(transactions, emp_branch, on='EmployeeID', how='left')

    # Parse dates
    df['Date'] = pd.to_datetime(df['Date'])
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month

    # Pivot table by transaction type
    pivot_df = df.pivot_table(
        index=['EmployeeID', 'EmployeeName', 'BranchName', 'Year', 'Month'],
        columns='Type',
        values='Amount',
        aggfunc='sum',
        fill_value=0
    ).reset_index()

    # Flatten columns
    pivot_df.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in pivot_df.columns.values]

    # Clean and compute Net Income
    pivot_df['BranchName'] = pivot_df['BranchName'].astype(str)
    pivot_df['Revenue'] = pd.to_numeric(pivot_df.get('Revenue', 0), errors='coerce').fillna(0)
    pivot_df['Expense'] = pd.to_numeric(pivot_df.get('Expense', 0), errors='coerce').fillna(0)
    pivot_df['Salary'] = pd.to_numeric(pivot_df.get('Salary', 0), errors='coerce').fillna(0)
    pivot_df['Net Income'] = pivot_df['Revenue'] - pivot_df['Expense'] - pivot_df['Salary']

    return pivot_df

# --- If all files uploaded ---
if uploaded_employees and uploaded_branches and uploaded_transactions:
    df = load_data(uploaded_employees, uploaded_branches, uploaded_transactions)

    # Prepare filter values
    years = sorted(df['Year'].dropna().unique())
    months = sorted(df['Month'].dropna().unique())
    branches = sorted(df['BranchName'].dropna().unique())
    employees = sorted(df['EmployeeName'].dropna().unique())
    month_names = {1:"Jan", 2:"Feb", 3:"Mar", 4:"Apr", 5:"May", 6:"Jun",
                   7:"Jul", 8:"Aug", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dec"}

    # --- Sidebar Filters ---
    st.sidebar.header("📅 Filters")
    selected_year = st.sidebar.selectbox("Select Year", ["All"] + [str(year) for year in years], index=0)
    selected_month = st.sidebar.selectbox("Select Month", ["All"] + [month_names[m] for m in months], index=0)
    selected_branches = st.sidebar.multiselect("Select Branch(es)", ["All"] + branches, default=["All"])
    selected_employees = st.sidebar.multiselect("Select Employee(s)", ["All"] + employees, default=["All"])

    # --- Fetch Data Button ---
    fetch_data = st.sidebar.button("🔍 Fetch Data")

    if fetch_data:
        filtered_df = df.copy()

        # Apply filters
        if selected_year != "All":
            filtered_df = filtered_df[filtered_df['Year'] == int(selected_year)]

        if selected_month != "All":
            month_num = [k for k, v in month_names.items() if v == selected_month][0]
            filtered_df = filtered_df[filtered_df['Month'] == month_num]

        if selected_branches != ["All"]:
            filtered_df = filtered_df[filtered_df['BranchName'].isin(selected_branches)]

        if selected_employees != ["All"]:
            filtered_df = filtered_df[filtered_df['EmployeeName'].isin(selected_employees)]

        # Handle branch click via session state
        if 'clicked_branch' in st.session_state:
            clicked_branch = st.session_state.clicked_branch
            filtered_df = filtered_df[filtered_df['BranchName'] == clicked_branch]

        # Recalculate Net Income safely
        filtered_df['Net Income'] = filtered_df.get('Revenue', 0) - filtered_df.get('Expense', 0) - filtered_df.get('Salary', 0)

        # --- Metrics ---
        total_sales = filtered_df['Revenue'].sum()
        total_expenses = filtered_df['Expense'].sum() + filtered_df['Salary'].sum()
        net_income = total_sales - total_expenses
        avg_customer_rating = 4.69
        total_branches = filtered_df['BranchName'].nunique()
        top_performing_branches = filtered_df.groupby('BranchName')['Net Income'].sum().gt(0).sum()
        total_employees = filtered_df['EmployeeID'].nunique()

        # Calculate Performance Ratio per branch (Net Income / Total Expenses)
        branch_perf = filtered_df.groupby('BranchName').agg({
            'Net Income': 'sum',
            'Expense': 'sum',
            'Salary': 'sum'
        }).reset_index()
        branch_perf['Total Expenses'] = branch_perf['Expense'] + branch_perf['Salary']
        branch_perf['Performance Ratio'] = branch_perf.apply(
            lambda row: row['Net Income'] / row['Total Expenses'] if row['Total Expenses'] > 0 else 0, axis=1)
        branch_perf['Performance Status'] = branch_perf['Performance Ratio'].apply(lambda x: 'PW' if x >= 3 else 'NPW')

        # --- Show Metrics ---
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

        # --- Branch Summary ---
        st.subheader("📍 Summary by Branch")
        # Merge performance info to summary
        branch_summary = branch_perf.copy()
        branch_summary['Net Income'] = branch_summary['Net Income']
        branch_summary['Expense'] = branch_summary['Expense']
        branch_summary['Salary'] = branch_summary['Salary']
        branch_summary['Total Expenses'] = branch_summary['Total Expenses']

        branch_summary['Performance Status Label'] = branch_summary['Performance Status'].map({'PW': 'Performing Well', 'NPW': 'Not Performing Well'})

        st.dataframe(branch_summary.style.format({
            'Expense': '${:,.2f}',
            'Salary': '${:,.2f}',
            'Total Expenses': '${:,.2f}',
            'Net Income': '${:,.2f}'
        }).hide_index())

        # --- Financials by Branch Grouped Bar Chart ---
        st.subheader("🏢 Financials by Branch")

        # Split Net Income into Good and Review based on 3x rule
        branch_summary['Net Income (Good)'] = branch_summary.apply(
            lambda row: row['Net Income'] if row['Performance Ratio'] >= 3 else 0, axis=1)
        branch_summary['Net Income (Review)'] = branch_summary.apply(
            lambda row: row['Net Income'] if row['Performance Ratio'] < 3 else 0, axis=1)

        # Prepare data for grouped bar chart
        financials_melt = branch_summary.melt(
            id_vars='BranchName',
            value_vars=['Net Income (Good)', 'Net Income (Review)', 'Total Expenses', 'Net Income'],  # Changed Revenue to Net Income for clarity below
            var_name='Metric',
            value_name='Amount'
        )

        # Rename 'Net Income' to 'Total Sales' in financials_melt (adjust if you want actual Revenue here)
        # Actually you want Total Sales (Revenue) — let's get it from filtered_df grouped by branch:
        branch_revenue = filtered_df.groupby('BranchName')['Revenue'].sum().reset_index()
        financials_melt = financials_melt.merge(branch_revenue, on='BranchName', how='left', suffixes=('', '_Revenue'))
        financials_melt.loc[financials_melt['Metric'] == 'Net Income', 'Metric'] = 'Total Sales'
        financials_melt.loc[financials_melt['Metric'] == 'Total Sales', 'Amount'] = financials_melt['Revenue']

        financials_melt = financials_melt.drop(columns=['Revenue'])

        # Grouped bar chart with side-by-side bars (xOffset)
        bar_chart = alt.Chart(financials_melt).mark_bar().encode(
            x=alt.X('BranchName:N', title='Branch'),
            y=alt.Y('Amount:Q', title='Amount ($)'),
            color=alt.Color('Metric:N', scale=alt.Scale(scheme='category10')),
            tooltip=[alt.Tooltip('BranchName:N'), alt.Tooltip('Metric:N'), alt.Tooltip('Amount:Q', format='$,.2f')],
            xOffset='Metric:N'  # this creates side-by-side grouped bars
        ).properties(
            width=800,
            height=400
        )

        st.altair_chart(bar_chart, use_container_width=True)

        st.markdown("---")

        # --- Employee Summary ---
        st.subheader("🧑‍💼 Summary by Employee")

        employee_summary = filtered_df.groupby("EmployeeName").agg({
            'Expense': 'sum',
            'Revenue': 'sum',
            'Salary': 'sum',
            'Net Income': 'sum'
        }).reset_index()

        # Calculate Performance Ratio per employee (Net Income / Expenses+Salary)
        employee_summary['Total Expenses'] = employee_summary['Expense'] + employee_summary['Salary']
        employee_summary['Performance Ratio'] = employee_summary.apply(
            lambda row: row['Net Income'] / row['Total Expenses'] if row['Total Expenses'] > 0 else 0, axis=1)
        employee_summary['Performance Status'] = employee_summary['Performance Ratio'].apply(lambda x: 'PW' if x >= 3 else 'NPW')
        employee_summary['Performance Status Label'] = employee_summary['Performance Status'].map({'PW': 'Performing Well', 'NPW': 'Not Performing Well'})

        st.dataframe(employee_summary.style.format({
            'Expense': '${:,.2f}',
            'Revenue': '${:,.2f}',
            'Salary': '${:,.2f}',
            'Net Income': '${:,.2f}'
        }).hide_index())

        st.markdown("---")

        # --- 12-Month Company Net Income Trend ---
        st.subheader("📅 12-Month Company Net Income Trend")

        monthly_perf = filtered_df.groupby(['Year', 'Month']).agg({
            'Net Income': 'sum'
        }).reset_index()

        # Create string for Year-Month like 2023-01
        monthly_perf['Month'] = monthly_perf['Month'].astype(int)
        monthly_perf['MonthStr'] = monthly_perf.apply(lambda row: f"{row['Year']}-{row['Month']:02d}", axis=1)

        monthly_chart = alt.Chart(monthly_perf).mark_line(point=True).encode(
            x=alt.X('MonthStr', sort=alt.SortField(field='MonthStr', order='ascending'), title='Month'),
            y=alt.Y('Net Income', title='Net Income ($)'),
            tooltip=[alt.Tooltip('MonthStr', title='Month'), alt.Tooltip('Net Income', format='$,.2f')]
        ).properties(width=800, height=400)

        st.altair_chart(monthly_chart, use_container_width=True)

        # --- Detailed Transactions by Employee ---
        st.subheader("📄 Detailed Transactions by Employee")
        st.dataframe(filtered_df.style.format({
            'Revenue': '${:,.2f}',
            'Expense': '${:,.2f}',
            'Salary': '${:,.2f}',
            'Net Income': '${:,.2f}'
        }))

    else:
        st.info("👈 Use the filters and click **Fetch Data** to update the dashboard.")
else:
    st.warning("🚨 Please upload all three CSV files in the sidebar to get started.")
