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

# --- Sidebar: File Uploads ---
st.sidebar.header("📤 Upload CSV Files")

uploaded_employees = st.sidebar.file_uploader("Upload Employees CSV", type="csv")
uploaded_branches = st.sidebar.file_uploader("Upload Branches CSV", type="csv")
uploaded_transactions = st.sidebar.file_uploader("Upload Transactions CSV", type="csv")

def load_data(emp_file, branch_file, trans_file):
    employees = pd.read_csv(emp_file)
    branches = pd.read_csv(branch_file)
    transactions = pd.read_csv(trans_file)

    # Merge employees with branches to get BranchName in employees df
    employees = pd.merge(employees, branches, on='BranchID', how='left')

    # Parse dates in transactions
    transactions['Date'] = pd.to_datetime(transactions['Date'])

    return employees, branches, transactions

def financials_by_branch_chart(df):
    # Your existing function unchanged ...
    pass

def monthly_company_performance_chart(df):
    # Your existing function unchanged ...
    pass

def monthly_performance_for_branch_chart(df, branch_name):
    # Your existing function unchanged ...
    pass

if uploaded_employees and uploaded_branches and uploaded_transactions:
    employees, branches, transactions = load_data(uploaded_employees, uploaded_branches, uploaded_transactions)

    # Prepare overview list
    branch_names = sorted(branches['BranchName'].dropna().unique())
    overview_options = ["📊 Company Overview"] + [f"📍 {branch}" for branch in branch_names]

    st.sidebar.header("📋 Select Overview")
    selected_overview = st.sidebar.radio("Choose Overview", overview_options)

    if selected_overview == "📊 Company Overview":
        # Compute company-wide metrics
        merged = pd.merge(transactions, employees, on='EmployeeID', how='left')
        total_sales = merged[merged['Type'] == 'Revenue']['Amount'].sum()
        total_expenses = merged[merged['Type'].isin(['Expense', 'Salary'])]['Amount'].sum()
        net_income = total_sales - total_expenses
        avg_customer_rating = 4.69  # Placeholder
        total_branches = branches['BranchName'].nunique()
        total_employees = employees['EmployeeID'].nunique()
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

        st.altair_chart(financials_by_branch_chart(merged), use_container_width=True)
        st.altair_chart(monthly_company_performance_chart(merged), use_container_width=True)

    else:
        # Branch overview
        selected_branch = selected_overview.replace("📍 ", "")

        # Get BranchID for the selected branch
        branch_id = branches[branches['BranchName'] == selected_branch]['BranchID'].values[0]

        # Employees in this branch
        branch_employees = employees[employees['BranchID'] == branch_id]

        # Transactions for employees in branch
        branch_emp_ids = branch_employees['EmployeeID'].unique()
        branch_trans = transactions[transactions['EmployeeID'].isin(branch_emp_ids)]

        # Calculate branch-level aggregates
        total_sales = branch_trans[branch_trans['Type'] == 'Revenue']['Amount'].sum()
        total_expenses = branch_trans[branch_trans['Type'].isin(['Expense', 'Salary'])]['Amount'].sum()
        net_income = total_sales - total_expenses
        avg_customer_rating = 4.69  # Placeholder
        total_employees = branch_employees['EmployeeID'].nunique()
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
        st.altair_chart(monthly_performance_for_branch_chart(branch_trans, selected_branch), use_container_width=True)

        # --- Individual Performance Table ---

        # Pivot employee transactions by Type
        pivot_emp = branch_trans.pivot_table(
            index='EmployeeID',
            columns='Type',
            values='Amount',
            aggfunc='sum',
            fill_value=0
        ).reset_index()

        # Merge with employee info (Name, Position)
        emp_perf = pd.merge(branch_employees, pivot_emp, on='EmployeeID', how='left').fillna(0)

        # Calculate Net Income per employee
        emp_perf['Net Income'] = emp_perf.get('Revenue', 0) - emp_perf.get('Expense', 0) - emp_perf.get('Salary', 0)

        # Calculate Status (Sales/Expense)
        def status_ratio(row):
            if row['Expense'] > 0:
                return f"{row['Revenue'] / row['Expense']:.1f}X"
            else:
                return "∞"
        emp_perf['Status (Sales/Expense)'] = emp_perf.apply(status_ratio, axis=1)

        # Add placeholder Customer Rating
        emp_perf['Customer Rating'] = "4.8 / 5.0"

        # Count transactions per employee
        trans_counts = branch_trans.groupby('EmployeeID').size().reset_index(name='Transactions')
        emp_perf = emp_perf.merge(trans_counts, on='EmployeeID', how='left').fillna({'Transactions': 0})

        # Select and rename columns for display
        display_cols = {
            'EmployeeName': 'Employee',
            'Position': 'Position',
            'Revenue': 'Sales',
            'Expense': 'Expenses',
            'Salary': 'Salary',
            'Net Income': 'Net Income',
            'Status (Sales/Expense)': 'Status (Sales/Expense)',
            'Customer Rating': 'Customer Rating',
            'Transactions': 'Transactions'
        }

        display_df = emp_perf[list(display_cols.keys())].rename(columns=display_cols)

        # Format currency columns
        for col in ['Sales', 'Expenses', 'Salary', 'Net Income']:
            display_df[col] = display_df[col].apply(lambda x: f"${x:,.0f}")

        st.markdown(f"### Individual Performance: {selected_branch}")
        st.dataframe(display_df)

else:
    st.info("Please upload all three CSV files (Employees, Branches, Transactions) from the sidebar to continue.")
