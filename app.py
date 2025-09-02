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

# --- Performance Status Display ---
def performance_status_display(ratio):
    if ratio >= 3:
        return blinking_star()
    elif ratio > 1:
        return "⭐"
    else:
        return ""

# --- Sidebar: File Uploads ---
st.sidebar.header("📤 Upload CSV Files")

uploaded_employees = st.sidebar.file_uploader("Upload Employees CSV", type="csv")
uploaded_branches = st.sidebar.file_uploader("Upload Branches CSV", type="csv")
uploaded_transactions = st.sidebar.file_uploader("Upload Transactions CSV", type="csv")

# --- Load & Process Data ---
def load_data(emp_file, branch_file, trans_file):
    employees = pd.read_csv(emp_file)
    branches = pd.read_csv(branch_file)
    transactions = pd.read_csv(trans_file)

    emp_branch = pd.merge(employees, branches, on='BranchID', how='left')
    df = pd.merge(transactions, emp_branch, on='EmployeeID', how='left')

    df['Date'] = pd.to_datetime(df['Date'])
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month

    pivot_df = df.pivot_table(
        index=['EmployeeID', 'EmployeeName', 'BranchName', 'Year', 'Month', 'Date'],
        columns='Type',
        values='Amount',
        aggfunc='sum',
        fill_value=0
    ).reset_index()

    pivot_df.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in pivot_df.columns.values]

    pivot_df['BranchName'] = pivot_df['BranchName'].astype(str)
    for col in ['Revenue', 'Expense', 'Salary']:
        if col not in pivot_df.columns:
            pivot_df[col] = 0
        else:
            pivot_df[col] = pd.to_numeric(pivot_df[col], errors='coerce').fillna(0)

    pivot_df['Net Income'] = pivot_df['Revenue'] - pivot_df['Expense'] - pivot_df['Salary']
    return pivot_df

# --- Visualization: Financials by Branch ---
def financials_by_branch_chart(df):
    summary = df.groupby("BranchName")[["Revenue", "Expense", "Salary"]].sum().reset_index()
    summary_melted = summary.melt(id_vars="BranchName", var_name="Financial Type", value_name="Amount")

    chart = alt.Chart(summary_melted).mark_bar().encode(
        x=alt.X("BranchName:N", title="Branch", sort='-y'),
        y=alt.Y("Amount:Q", title="Amount ($)"),
        color="Financial Type:N",
        tooltip=["BranchName", "Financial Type", "Amount"]
    ).properties(
        width=400,
        height=300,
        title="📊 Financials by Branch"
    )
    return chart

# --- Visualization: 12-Month Company Performance ---
def monthly_company_performance_chart(df):
    df['Month_Year'] = df['Date'].dt.to_period('M').astype(str)
    monthly = df.groupby("Month_Year")[["Revenue", "Expense"]].sum().reset_index()
    monthly_melted = monthly.melt(id_vars="Month_Year", var_name="Type", value_name="Amount")

    chart = alt.Chart(monthly_melted).mark_bar().encode(
        x=alt.X("Month_Year:N", title="Month", sort=monthly['Month_Year'].tolist()),
        y=alt.Y("Amount:Q", title="Amount ($)"),
        color="Type:N",
        tooltip=["Month_Year", "Type", "Amount"]
    ).properties(
        width=500,
        height=300,
        title="📅 12-Month Company Performance"
    )
    return chart

# --- Main App ---
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
        performance_status = blinking_star() if performance_ratio >= 3 else "⭐"

        st.subheader("📊 Company Overview Metrics")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Sales", f"${total_sales:,.0f}")
        col2.metric("Total Expenses", f"${total_expenses:,.0f}")
        col3.metric("Net Income", f"${net_income:,.0f}")
        col4.metric("Avg. Customer Rating", f"{avg_customer_rating:.2f}")

        col5, col6, col7, col8 = st.columns(4)
        col5.metric("Total Branches", total_branches)
        col6.metric("Performance Ratio", f"{performance_ratio:.2f}x")
        col7.markdown(f"**Performance Status:** {performance_status}", unsafe_allow_html=True)
        col8.metric("Total Employees", total_employees)

        # 📈 Charts Section
        st.markdown("## 📈 Financial Visualizations")
        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            st.altair_chart(financials_by_branch_chart(df), use_container_width=True)

        with col_chart2:
            st.altair_chart(monthly_company_performance_chart(df), use_container_width=True)

    else:
        branch_name = selected_overview.replace("📍 ", "")
        filtered_df = df[df['BranchName'] == branch_name]

        # Branch-level Summary
        branch_summary = filtered_df.groupby("BranchName")[['Expense', 'Revenue', 'Salary', 'Net Income']].sum().reset_index()
        emp_count = filtered_df.groupby("BranchName")['EmployeeID'].nunique().reset_index().rename(columns={'EmployeeID': 'Total Employees'})
        branch_summary = branch_summary.merge(emp_count, on='BranchName', how='left')

        branch_summary['Performance Ratio'] = branch_summary.apply(
            lambda row: row['Revenue'] / (row['Expense'] + row['Salary']) if (row['Expense'] + row['Salary']) > 0 else float('inf'),
            axis=1
        )
        branch_summary['Performance Status'] = branch_summary['Performance Ratio'].apply(performance_status_display)

        st.subheader(f"📍 Branch Overview: {branch_name}")
        for _, row in branch_summary.iterrows():
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Sales", f"${row['Revenue']:,.0f}")
            col2.metric("Total Expenses", f"${row['Expense'] + row['Salary']:,.0f}")
            col3.metric("Net Income", f"${row['Net Income']:,.0f}")
            col4.metric("Total Employees", row['Total Employees'])

            col5, col6 = st.columns(2)
            col5.metric("Performance Ratio", f"{row['Performance Ratio']:.2f}x")
            col6.markdown(f"**Performance Status:** {row['Performance Status']}", unsafe_allow_html=True)

        # Employee-level Summary
        st.subheader(f"🧑‍💼 Employee Summary: {branch_name}")
        emp_summary = filtered_df.groupby(["EmployeeName", "BranchName"])[['Expense', 'Revenue', 'Salary', 'Net Income']].sum().reset_index()

        emp_summary['Performance Ratio'] = emp_summary.apply(
            lambda row: row['Revenue'] / (row['Expense'] + row['Salary']) if (row['Expense'] + row['Salary']) > 0 else float('inf'),
            axis=1
        )
        emp_summary['Performance Status'] = emp_summary['Performance Ratio'].apply(performance_status_display)

        for _, row in emp_summary.iterrows():
            col1, col2, col3, col4 = st.columns(4)
            col1.metric(f"{row['EmployeeName']} - Sales", f"${row['Revenue']:,.0f}")
            col2.metric(f"{row['EmployeeName']} - Expenses", f"${row['Expense'] + row['Salary']:,.0f}")
            col3.metric(f"{row['EmployeeName']} - Net Income", f"${row['Net Income']:,.0f}")
            col4.metric(f"{row['EmployeeName']} - Branch", row['BranchName'])

            col5, col6 = st.columns(2)
            col5.metric("Performance Ratio", f"{row['Performance Ratio']:.2f}x")
            col6.markdown(f"**Performance Status:** {row['Performance Status']}", unsafe_allow_html=True)

else:
    st.warning("🚨 Please upload all three CSV files in the sidebar to get started.")
