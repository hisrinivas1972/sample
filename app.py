import pandas as pd
import streamlit as st
import altair as alt

st.set_page_config(page_title="Branch Performance Dashboard", layout="wide")
st.title("📊 Company Overview")

def blinking_star():
    blinking_css = """
    <style>
    @keyframes blink {
        0% { opacity: 1; }
        50% { opacity: 0; }
        100% { opacity: 1; }
    }
    .blink {
        animation: blink 1s infinite;
        font-size: 24px;
        color: gold;
        font-weight: bold;
    }
    </style>
    """
    st.markdown(blinking_css, unsafe_allow_html=True)
    return '<span class="blink">⭐✨</span>'

st.sidebar.header("📤 Upload CSV Files")
uploaded_employees = st.sidebar.file_uploader("Upload Employees CSV", type="csv")
uploaded_branches = st.sidebar.file_uploader("Upload Branches CSV", type="csv")
uploaded_transactions = st.sidebar.file_uploader("Upload Transactions CSV", type="csv")

def load_data(emp_file, branch_file, trans_file):
    employees = pd.read_csv(emp_file)
    branches = pd.read_csv(branch_file)
    transactions = pd.read_csv(trans_file)

    emp_branch = pd.merge(employees, branches, on='BranchID', how='left')
    df = pd.merge(transactions, emp_branch, on='EmployeeID', how='left')

    df['Date'] = pd.to_datetime(df['Date'])
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month

    pivot_index = ['EmployeeID', 'EmployeeName', 'BranchName', 'Year', 'Month', 'Date']
    if 'Position' in df.columns:
        pivot_index.insert(2, 'Position')

    pivot_df = df.pivot_table(
        index=pivot_index,
        columns='Type',
        values='Amount',
        aggfunc='sum',
        fill_value=0
    ).reset_index()

    for col in ['Revenue', 'Expense', 'Salary']:
        if col not in pivot_df.columns:
            pivot_df[col] = 0
        else:
            pivot_df[col] = pd.to_numeric(pivot_df[col], errors='coerce').fillna(0)

    pivot_df['Net Income'] = pivot_df['Revenue'] - pivot_df['Expense'] - pivot_df['Salary']
    return pivot_df

# ---- Chart: Financials by Branch ----
def financials_by_branch_chart(df):
    # Group by BranchName, sum revenue, expense, salary
    summary = df.groupby('BranchName').agg({
        'Revenue': 'sum',
        'Expense': 'sum',
        'Salary': 'sum'
    }).reset_index()
    summary = summary.melt(id_vars='BranchName', value_vars=['Revenue', 'Expense', 'Salary'],
                           var_name='Type', value_name='Amount')

    chart = alt.Chart(summary).mark_bar().encode(
        x=alt.X('BranchName:N', sort='-y', title='Branch'),
        y=alt.Y('Amount:Q', title='Amount ($)'),
        color=alt.Color('Type:N', title='Financial Type'),
        tooltip=['BranchName', 'Type', alt.Tooltip('Amount', format='$,.2f')]
    ).properties(
        title="Financial Overview by Branch",
        width=700,
        height=400
    )
    return chart

# ---- Chart: Monthly Company Performance ----
def monthly_company_performance_chart(df):
    # Aggregate monthly revenue and expenses for the company
    monthly = df.groupby(['Year', 'Month']).agg({
        'Revenue': 'sum',
        'Expense': 'sum',
        'Salary': 'sum'
    }).reset_index()
    monthly['Date'] = pd.to_datetime(monthly[['Year', 'Month']].assign(DAY=1))

    monthly = monthly.melt(id_vars='Date', value_vars=['Revenue', 'Expense', 'Salary'],
                           var_name='Type', value_name='Amount')

    chart = alt.Chart(monthly).mark_line(point=True).encode(
        x=alt.X('Date:T', title='Month'),
        y=alt.Y('Amount:Q', title='Amount ($)'),
        color=alt.Color('Type:N', title='Financial Type'),
        tooltip=[alt.Tooltip('Date', title='Month', format='%b %Y'), 'Type', alt.Tooltip('Amount', format='$,.2f')]
    ).properties(
        title="Monthly Company Performance",
        width=700,
        height=400
    )
    return chart

# ---- Chart: Monthly Performance for a Branch ----
def monthly_performance_for_branch_chart(df, branch_name):
    branch_monthly = df[df['BranchName'] == branch_name].groupby(['Year', 'Month']).agg({
        'Revenue': 'sum',
        'Expense': 'sum',
        'Salary': 'sum'
    }).reset_index()
    branch_monthly['Date'] = pd.to_datetime(branch_monthly[['Year', 'Month']].assign(DAY=1))

    branch_monthly = branch_monthly.melt(id_vars='Date', value_vars=['Revenue', 'Expense', 'Salary'],
                                        var_name='Type', value_name='Amount')

    chart = alt.Chart(branch_monthly).mark_line(point=True).encode(
        x=alt.X('Date:T', title='Month'),
        y=alt.Y('Amount:Q', title='Amount ($)'),
        color=alt.Color('Type:N', title='Financial Type'),
        tooltip=[alt.Tooltip('Date', title='Month', format='%b %Y'), 'Type', alt.Tooltip('Amount', format='$,.2f')]
    ).properties(
        title=f"Monthly Performance for {branch_name}",
        width=700,
        height=400
    )
    return chart

if uploaded_employees and uploaded_branches and uploaded_transactions:
    df = load_data(uploaded_employees, uploaded_branches, uploaded_transactions)

    branches = sorted(df['BranchName'].dropna().unique())
    overview_options = ["📊 Company Overview"] + [f"📍 {branch}" for branch in branches]

    st.sidebar.header("📋 Select Overview")
    selected_overview = st.sidebar.radio("Choose Overview", overview_options)

    if selected_overview == "📊 Company Overview":
        total_sales = df['Revenue'].sum()
        total_expenses = df['Expense'].sum() + df['Salary'].sum()
        net_income = total_sales - total_expenses
        performance_ratio = total_sales / total_expenses if total_expenses > 0 else float('inf')
        perf_status_display = blinking_star() if performance_ratio >= 3 else ("⭐" if performance_ratio > 1 else "")
        total_branches = df['BranchName'].nunique()
        total_employees = df['EmployeeID'].nunique()

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Sales", f"${total_sales:,.0f}")
        col2.metric("Total Expenses", f"${total_expenses:,.0f}")
        col3.metric("Net Income", f"${net_income:,.0f}")

        col4, col5, col6 = st.columns(3)
        col4.metric("Performance Ratio", f"{performance_ratio:.2f}x")
        col5.metric("Total Branches", total_branches)
        col6.metric("Total Employees", total_employees)

        st.markdown(f"**Performance Status:** {perf_status_display}", unsafe_allow_html=True)
        st.markdown("### 📈 Visualizations")
        st.altair_chart(financials_by_branch_chart(df), use_container_width=True)
        st.altair_chart(monthly_company_performance_chart(df), use_container_width=True)

    else:
        selected_branch = selected_overview.replace("📍 ", "")
        branch_df = df[df['BranchName'] == selected_branch]

        total_sales = branch_df['Revenue'].sum()
        total_expenses = branch_df['Expense'].sum() + branch_df['Salary'].sum()
        net_income = total_sales - total_expenses
        performance_ratio = total_sales / total_expenses if total_expenses > 0 else float('inf')
        perf_status_display = blinking_star() if performance_ratio >= 3 else ("⭐" if performance_ratio > 1 else "")
        total_employees = branch_df['EmployeeID'].nunique()

        st.header(f"📍 Branch Overview: {selected_branch}")

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Sales", f"${total_sales:,.0f}")
        col2.metric("Total Expenses", f"${total_expenses:,.0f}")
        col3.metric("Net Income", f"${net_income:,.0f}")

        col4, col5 = st.columns(2)
        col4.metric("Performance Ratio", f"{performance_ratio:.2f}x")
        col5.metric("Total Employees", f"{total_employees}")

        st.markdown(f"**Performance Status:** {perf_status_display}", unsafe_allow_html=True)

        st.markdown("### 📈 Visualizations")
        st.altair_chart(monthly_performance_for_branch_chart(branch_df, selected_branch), use_container_width=True)

        # Individual Performance Table
        st.markdown(f"### 🧑‍💼 Individual Performance: {selected_branch}")

        group_fields = ['EmployeeID', 'EmployeeName']
        if 'Position' in branch_df.columns:
            group_fields.append('Position')

        employee_perf = branch_df.groupby(group_fields).agg({
            'Revenue': 'sum',
            'Expense': 'sum',
            'Salary': 'sum',
            'Net Income': 'sum',
            'Date': 'count'
        }).reset_index()

        employee_perf.rename(columns={
            'Revenue': 'Sales',
            'Date': 'Transactions'
        }, inplace=True)

        employee_perf['Status (Sales/Expense)'] = employee_perf.apply(
            lambda row: f"{(row['Sales'] / (row['Expense'] + row['Salary'])):.1f}X" if (row['Expense'] + row['Salary']) > 0 else "∞",
            axis=1
        )

        employee_perf['Customer Rating'] = "4.8 / 5.0"  # Placeholder

        for col in ['Sales', 'Expense', 'Salary', 'Net Income']:
            employee_perf[col] = employee_perf[col].apply(lambda x: f"${x:,.0f}")

        display_cols = ['EmployeeName']
        if 'Position' in employee_perf.columns:
            display_cols.append('Position')
        display_cols += ['Sales', 'Expense', 'Salary', 'Net Income',
                         'Status (Sales/Expense)', 'Customer Rating', 'Transactions']

        employee_perf = employee_perf[display_cols]
        st.dataframe(employee_perf, use_container_width=True)

else:
    st.info("Please upload all three CSV files (Employees, Branches, Transactions) from the sidebar to continue.")
