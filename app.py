import pandas as pd
import streamlit as st
import altair as alt

st.set_page_config(page_title="Branch Performance Dashboard", layout="wide")
st.title("📊 Company Overview")

# --- Blinking star function ---
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

# --- Performance Status Display (with Star) ---
def performance_status_display(ratio):
    if ratio >= 3:
        return blinking_star()  # Blinking star for PW
    elif ratio > 1:
        return "⭐"  # Single star for NPW with ratio > 1
    else:
        return ""  # No star for NPW with ratio <= 1

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
        index=['EmployeeID', 'EmployeeName', 'Position', 'BranchName', 'Year', 'Month', 'Date'],
        columns='Type',
        values='Amount',
        aggfunc='sum',
        fill_value=0
    ).reset_index()

    # Clean and compute Net Income
    for col in ['Revenue', 'Expense', 'Salary']:
        if col not in pivot_df.columns:
            pivot_df[col] = 0
        else:
            pivot_df[col] = pd.to_numeric(pivot_df[col], errors='coerce').fillna(0)

    pivot_df['Net Income'] = pivot_df['Revenue'] - pivot_df['Expense'] - pivot_df['Salary']
    return pivot_df

# --- Chart Functions Omitted for Brevity (unchanged) ---
# Keep financials_by_branch_chart(), monthly_company_performance_chart(), monthly_performance_for_branch_chart() as before

# You can paste those here if needed

# --- Main App Logic ---
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
        avg_customer_rating = 4.69
        total_branches = df['BranchName'].nunique()
        total_employees = df['EmployeeID'].nunique()
        performance_ratio = total_sales / total_expenses if total_expenses > 0 else float('inf')
        performance_status = "PW" if performance_ratio >= 3 else "NPW"
        perf_status_display = blinking_star() if performance_status == "PW" else ("⭐" if performance_ratio > 1 else "")

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Sales", f"${total_sales:,.0f}")
        col2.metric("Total Expenses", f"${total_expenses:,.0f}")
        col3.metric("Net Income", f"${net_income:,.0f}")

        col4, col5, col6 = st.columns(3)
        col4.metric("Avg. Customer Rating", f"{avg_customer_rating}")
        col5.metric("Total Branches", f"{total_branches}")
        col6.metric("Performance Ratio", f"{performance_ratio:.2f}x")

        st.markdown(f"**Performance Status:** {perf_status_display}", unsafe_allow_html=True)
        st.metric("Total Employees", total_employees)

        st.markdown("### 📈 Visualizations")
        st.altair_chart(financials_by_branch_chart(df), use_container_width=True)
        st.altair_chart(monthly_company_performance_chart(df), use_container_width=True)

    else:
        selected_branch = selected_overview.replace("📍 ", "")
        branch_df = df[df['BranchName'] == selected_branch]

        total_sales = branch_df['Revenue'].sum()
        total_expenses = branch_df['Expense'].sum() + branch_df['Salary'].sum()
        net_income = total_sales - total_expenses
        avg_customer_rating = 4.69  # Placeholder
        total_employees = branch_df['EmployeeID'].nunique()
        performance_ratio = total_sales / total_expenses if total_expenses > 0 else float('inf')
        performance_status = "PW" if performance_ratio >= 3 else "NPW"
        perf_status_display = blinking_star() if performance_status == "PW" else ("⭐" if performance_ratio > 1 else "")

        st.header(f"📍 Branch Overview: {selected_branch}")

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Sales", f"${total_sales:,.0f}")
        col2.metric("Total Expenses", f"${total_expenses:,.0f}")
        col3.metric("Net Income", f"${net_income:,.0f}")

        col4, col5 = st.columns(2)
        col4.metric("Avg. Customer Rating", f"{avg_customer_rating}")
        col5.metric("Total Employees", f"{total_employees}")

        st.markdown(f"**Performance Ratio:** {performance_ratio:.2f}x")
        st.markdown(f"**Performance Status:** {perf_status_display}", unsafe_allow_html=True)

        st.markdown("### 📈 Visualizations")
        st.altair_chart(monthly_performance_for_branch_chart(branch_df, selected_branch), use_container_width=True)

        # --- ✅ New: Individual Performance Summary ---
        st.markdown(f"### 🧑‍💼 Individual Performance: {selected_branch}")

        employee_perf = branch_df.groupby(['EmployeeID', 'EmployeeName', 'Position']).agg({
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

        employee_perf['Customer Rating'] = "4.8 / 5.0"  # placeholder

        # Format monetary columns
        for col in ['Sales', 'Expense', 'Salary', 'Net Income']:
            employee_perf[col] = employee_perf[col].apply(lambda x: f"${x:,.0f}")

        employee_perf = employee_perf[[
            'EmployeeName', 'Position', 'Sales', 'Expense', 'Salary', 'Net Income',
            'Status (Sales/Expense)', 'Customer Rating', 'Transactions'
        ]]

        st.dataframe(employee_perf, use_container_width=True)

else:
    st.info("Please upload all three CSV files (Employees, Branches, Transactions) from the sidebar to continue.")
