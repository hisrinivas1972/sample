import pandas as pd
import streamlit as st
import altair as alt

st.set_page_config(page_title="Branch Performance Dashboard", layout="wide")
st.title("📊 Company Overview")

# CSS for blinking star
def blinking_star_css():
    css = """
    <style>
    @keyframes blink {
        0% { opacity: 1; }
        50% { opacity: 0; }
        100% { opacity: 1; }
    }
    .blink {
        animation: blink 1s infinite;
        font-weight: bold;
        color: gold;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def blinking_star():
    return '<span class="blink">⭐✨</span>'

def performance_status_display(ratio):
    if ratio >= 3:
        return blinking_star()  # blinking star for PW
    elif ratio > 1:
        return "⭐"  # single star for NPW with ratio > 1
    else:
        return ""  # no star for NPW with ratio <= 1

blinking_star_css()

# Sidebar uploads
st.sidebar.header("📤 Upload CSV Files")
uploaded_employees = st.sidebar.file_uploader("Upload Employees CSV", type="csv")
uploaded_branches = st.sidebar.file_uploader("Upload Branches CSV", type="csv")
uploaded_transactions = st.sidebar.file_uploader("Upload Transactions CSV", type="csv")

def load_data(emp_file, branch_file, trans_file):
    employees = pd.read_csv(emp_file)
    branches = pd.read_csv(branch_file)
    transactions = pd.read_csv(trans_file)

    employees.rename(columns=lambda x: x.strip(), inplace=True)
    branches.rename(columns=lambda x: x.strip(), inplace=True)
    transactions.rename(columns=lambda x: x.strip(), inplace=True)

    # Merge employees with branches on BranchID
    emp_branch = pd.merge(employees, branches, on='BranchID', how='left')

    # Merge transactions with emp_branch on EmployeeID
    df = pd.merge(transactions, emp_branch, on='EmployeeID', how='left')

    # Fix types
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)

    return df, employees, branches

if uploaded_employees and uploaded_branches and uploaded_transactions:
    df, employees, branches = load_data(uploaded_employees, uploaded_branches, uploaded_transactions)

    # Ensure BranchName exists for selection
    if 'BranchName' not in df.columns:
        st.error("BranchName column missing after merging data.")
        st.stop()

    st.sidebar.header("Branch Selection")
    branches_list = df['BranchName'].dropna().unique()
    selected_branch = st.sidebar.selectbox("Select Branch", sorted(branches_list))

    # Filter data for selected branch
    df_branch = df[df['BranchName'] == selected_branch].copy()
    branch_id = df_branch['BranchID'].iloc[0]
    employees_branch = employees[employees['BranchID'] == branch_id]

    # Calculate branch summary metrics
    sales = df_branch[df_branch['Type'].str.lower() == 'revenue']['Amount'].sum()
    expenses = df_branch[df_branch['Type'].str.lower() == 'expense']['Amount'].sum()
    net_income = sales - expenses
    emp_count = employees_branch['EmployeeID'].nunique()

    # Performance ratio Sales / Expenses (avoid div0)
    perf_ratio = sales / (expenses + 1e-6)

    # Calculate employee performance ratio and needs review count
    emp_perf = df_branch.groupby(['EmployeeID', 'Type'])['Amount'].sum().unstack(fill_value=0)
    emp_perf['PerformanceRatio'] = emp_perf.get('Revenue', 0) / (emp_perf.get('Expense', 0) + 1e-6)
    needs_review_count = (emp_perf['PerformanceRatio'] < 1).sum()

    # Branch Avg. Customer Rating
    if 'CustomerRating' in employees_branch.columns:
        avg_rating = round(employees_branch['CustomerRating'].mean(), 2)
    else:
        avg_rating = "N/A"

    # Branch Summary display
    st.markdown(f"""
    ## Branch Summary: **{selected_branch}**

    | Metric                  | Value           |
    |-------------------------|-----------------|
    | Branch Sales            | ${sales:,.0f}   |
    | Branch Expenses         | ${expenses:,.0f}|
    | Branch Net Income       | ${net_income:,.0f} |
    | Employees               | {emp_count}     |
    | Needs Review            | {needs_review_count} Employee(s) |
    | Performance (Sales/Expense) | {perf_ratio:.1f}X |
    | Branch Avg. Rating      | {avg_rating}    |
    """)

    # 12-Month Performance Chart
    st.header(f"📅 12-Month Company Performance for {selected_branch}")

    # Prepare monthly summary
    df_branch['Month'] = df_branch['Date'].dt.to_period('M').dt.to_timestamp()
    monthly = df_branch[df_branch['Type'].isin(['Revenue', 'Expense'])].groupby(['Month', 'Type'])['Amount'].sum().unstack(fill_value=0)
    monthly['Net Sales'] = monthly.get('Revenue', 0) - monthly.get('Expense', 0)
    monthly = monthly.reset_index()

    base = alt.Chart(monthly).encode(
        x=alt.X('Month:T', title='', axis=alt.Axis(format='%b %y'))
    )
    bars_exp = base.mark_bar(color='red').encode(
        y=alt.Y('Expense:Q', axis=alt.Axis(title='$')),
        tooltip=[alt.Tooltip('Month:T', title='Month'), alt.Tooltip('Expense:Q', title='Expenses', format=',.0f')]
    )
    bars_rev = base.mark_bar(color='purple').encode(
        y='Revenue:Q',
        tooltip=[alt.Tooltip('Month:T', title='Month'), alt.Tooltip('Revenue:Q', title='Gross Sales', format=',.0f')]
    )
    line_net = base.mark_line(point=alt.PointParams(color='white', filled=True)).encode(
        y='Net Sales:Q',
        tooltip=[alt.Tooltip('Month:T', title='Month'), alt.Tooltip('Net Sales:Q', title='Net Sales', format=',.0f')]
    )

    chart = alt.layer(bars_exp, bars_rev, line_net).resolve_scale(y='shared').properties(
        width=800, height=400
    )
    st.altair_chart(chart, use_container_width=True)

    # Employee Performance Table
    st.header(f"👨‍💼 Employee Performance: {selected_branch}")

    # Aggregate employee metrics
    emp_data = df_branch.pivot_table(
        index=['EmployeeID', 'EmployeeName', 'Position', 'CustomerRating'],
        columns='Type',
        values='Amount',
        aggfunc='sum',
        fill_value=0
    ).reset_index()

    # Ensure all columns present
    for col in ['Revenue', 'Expense', 'Salary']:
        if col not in emp_data.columns:
            emp_data[col] = 0

    emp_data['Net Income'] = emp_data['Revenue'] - emp_data['Expense'] - emp_data['Salary']
    emp_data['PerformanceRatio'] = emp_data['Revenue'] / (emp_data['Expense'] + 1e-6)
    emp_data['Status (Sales/Expense)'] = emp_data['PerformanceRatio'].apply(performance_status_display)

    # Rename columns for display
    emp_data.rename(columns={
        'EmployeeName': 'Employee',
        'Revenue': 'Sales',
        'Expense': 'Expenses',
        'CustomerRating': 'Customer Rating'
    }, inplace=True)

    display_cols = ['Employee', 'Position', 'Sales', 'Expenses', 'Salary', 'Net Income', 'Status (Sales/Expense)', 'Customer Rating']
    display_emp = emp_data[display_cols].sort_values('Employee')

    def highlight_net_income(val):
        if isinstance(val, (int, float)):
            if val > 0:
                return 'background-color: #d4edda'  # light green
            elif val < 0:
                return 'background-color: #f8d7da'  # light red
        return ''

    st.dataframe(display_emp.style.applymap(highlight_net_income, subset=['Net Income']), height=600)

else:
    st.warning("🚨 Please upload Employees, Branches, and Transactions CSV files to proceed.")
