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

    # Flatten columns
    pivot_df.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in pivot_df.columns.values]

    # Clean and compute Net Income
    pivot_df['BranchName'] = pivot_df['BranchName'].astype(str)
    for col in ['Revenue', 'Expense', 'Salary']:
        if col not in pivot_df.columns:
            pivot_df[col] = 0
        else:
            pivot_df[col] = pd.to_numeric(pivot_df[col], errors='coerce').fillna(0)

    pivot_df['Net Income'] = pivot_df['Revenue'] - pivot_df['Expense'] - pivot_df['Salary']

    return pivot_df

# --- Chart: Financials by Branch ---
def financials_by_branch_chart(df):
    summary = df.groupby("BranchName")[["Revenue", "Expense", "Salary"]].sum().reset_index()
    summary["Total Expenses"] = summary["Expense"] + summary["Salary"]
    summary["Net Income"] = summary["Revenue"] - summary["Total Expenses"]
    summary["Net Income Category"] = summary["Net Income"].apply(lambda x: "Net Income (Good)" if x > 0 else "Net Income (Review)")

    bar_df = summary.melt(
        id_vars=["BranchName", "Net Income Category"],
        value_vars=["Revenue", "Total Expenses", "Net Income"],
        var_name="Metric",
        value_name="Amount"
    )

    bar_df["Display Label"] = bar_df.apply(lambda row: (
        "Net Income (Good)" if row["Metric"] == "Net Income" and row["Net Income Category"] == "Net Income (Good)"
        else "Net Income (Review)" if row["Metric"] == "Net Income"
        else row["Metric"]
    ), axis=1)

    color_scale = alt.Scale(domain=[
        "Net Income (Good)", "Net Income (Review)", "Total Expenses", "Revenue"
    ], range=["#2ecc71", "#f1c40f", "#e74c3c", "#9b59b6"])

    chart = alt.Chart(bar_df).mark_bar().encode(
        x=alt.X("BranchName:N", title="Branch", axis=alt.Axis(labelAngle=-30)),
        y=alt.Y("Amount:Q", title="Amount ($)", stack=None),
        color=alt.Color("Display Label:N", scale=color_scale, title="Metric"),
        tooltip=["BranchName", "Metric", "Amount"],
        xOffset='Display Label:N'
    ).properties(
        width=600,
        height=400,
        title="📊 Financials by Branch"
    )

    return chart

# --- Chart: 12-Month Company Performance ---
def monthly_company_performance_chart(df):
    df['Month_Year'] = df['Date'].dt.to_period('M').astype(str)
    monthly = df.groupby("Month_Year").agg({
        "Revenue": "sum",
        "Expense": "sum",
        "Salary": "sum"
    }).reset_index()

    monthly["Gross Sales"] = monthly["Revenue"]
    monthly["Total Expenses"] = monthly["Expense"] + monthly["Salary"]
    monthly["Net Sales"] = monthly["Revenue"] - monthly["Total Expenses"]

    bar_df = monthly.melt(
        id_vars=["Month_Year", "Net Sales"],
        value_vars=["Gross Sales", "Total Expenses"],
        var_name="Metric",
        value_name="Amount"
    )

    bar_color_scale = alt.Scale(
        domain=["Gross Sales", "Total Expenses"],
        range=["#9b59b6", "#e74c3c"]
    )

    bar_chart = alt.Chart(bar_df).mark_bar().encode(
        x=alt.X("Month_Year:N", title="Month", axis=alt.Axis(labelAngle=-45)),
        y=alt.Y("Amount:Q", title="Amount ($)", stack=None),
        color=alt.Color("Metric:N", scale=bar_color_scale, title=""),
        xOffset="Metric:N",
        tooltip=["Month_Year", "Metric", "Amount"]
    )

    line_chart = alt.Chart(monthly).mark_line(point=alt.OverlayMarkDef(color="#2ecc71", filled=True)).encode(
        x=alt.X("Month_Year:N"),
        y=alt.Y("Net Sales:Q"),
        color=alt.value("#2ecc71"),
        tooltip=["Month_Year", "Net Sales"]
    )

    chart = alt.layer(bar_chart, line_chart).properties(
        width=700,
        height=400,
        title="📅 12-Month Company Performance"
    )

    return chart

# --- Chart: 12-Month Branch Performance (filtered) ---
def monthly_performance_for_branch_chart(df, branch_name):
    df['Month_Year'] = df['Date'].dt.to_period('M').astype(str)
    monthly = df.groupby("Month_Year").agg({
        "Revenue": "sum",
        "Expense": "sum",
        "Salary": "sum"
    }).reset_index()

    monthly["Gross Sales"] = monthly["Revenue"]
    monthly["Total Expenses"] = monthly["Expense"] + monthly["Salary"]
    monthly["Net Sales"] = monthly["Revenue"] - monthly["Total Expenses"]

    bar_df = monthly.melt(
        id_vars=["Month_Year", "Net Sales"],
        value_vars=["Gross Sales", "Total Expenses"],
        var_name="Metric",
        value_name="Amount"
    )

    bar_color_scale = alt.Scale(
        domain=["Gross Sales", "Total Expenses"],
        range=["#9b59b6", "#e74c3c"]
    )

    bar_chart = alt.Chart(bar_df).mark_bar().encode(
        x=alt.X("Month_Year:N", title="Month", axis=alt.Axis(labelAngle=-45)),
        y=alt.Y("Amount:Q", title="Amount ($)", stack=None),
        color=alt.Color("Metric:N", scale=bar_color_scale, title=""),
        xOffset="Metric:N",
        tooltip=["Month_Year", "Metric", "Amount"]
    )

    line_chart = alt.Chart(monthly).mark_line(point=alt.OverlayMarkDef(color="#2ecc71", filled=True)).encode(
        x=alt.X("Month_Year:N"),
        y=alt.Y("Net Sales:Q"),
        color=alt.value("#2ecc71"),
        tooltip=["Month_Year", "Net Sales"]
    )

    chart = alt.layer(bar_chart, line_chart).properties(
        width=700,
        height=400,
        title=f"📅 12-Month Performance: {branch_name}"
    )

    return chart

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
        total_salary = df['Salary'].sum()
        net_income = total_sales - total_expenses
        performance_ratio = total_sales / total_expenses if total_expenses > 0 else float('inf')
        perf_status_display = blinking_star() if performance_ratio >= 3 else ("⭐" if performance_ratio > 1 else "")
        total_branches = df['BranchName'].nunique()
        total_employees = df['EmployeeID'].nunique()
        customer_rating = "4.8 / 5.0"  # placeholder

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Sales", f"${total_sales:,.0f}")
        col2.metric("Expenses", f"${total_expenses:,.0f}")
        col3.metric("Salary", f"${total_salary:,.0f}")
        col4.metric("Net Income", f"${net_income:,.0f}")

        col5, col6, col7 = st.columns(3)
        col5.metric("Performance Ratio (Sales/Expenses)", f"{performance_ratio:.1f}X")
        col6.metric("Customer Rating", customer_rating)
        col7.metric("Branches", total_branches)

        st.markdown(f"**Status:** {perf_status_display}", unsafe_allow_html=True)

        st.metric("Total Employees", total_employees)

        st.markdown("### 📈 Visualizations")

        st.altair_chart(financials_by_branch_chart(df), use_container_width=True)
        st.altair_chart(monthly_company_performance_chart(df), use_container_width=True)

    else:
        selected_branch = selected_overview.replace("📍 ", "")
        branch_df = df[df['BranchName'] == selected_branch]

        total_sales = branch_df['Revenue'].sum()
        total_expenses = branch_df['Expense'].sum() + branch_df['Salary'].sum()
        total_salary = branch_df['Salary'].sum()
        net_income = total_sales - total_expenses
        performance_ratio = total_sales / total_expenses if total_expenses > 0 else float('inf')
        perf_status_display = blinking_star() if performance_ratio >= 3 else ("⭐" if performance_ratio > 1 else "")
        total_employees = branch_df['EmployeeID'].nunique()
        customer_rating = "4.8 / 5.0"  # placeholder

        st.header(f"📍 Branch Overview: {selected_branch}")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Sales", f"${total_sales:,.0f}")
        col2.metric("Expenses", f"${total_expenses:,.0f}")
        col3.metric("Salary", f"${total_salary:,.0f}")
        col4.metric("Net Income", f"${net_income:,.0f}")

        col5, col6 = st.columns(2)
        col5.metric("Performance Ratio (Sales/Expenses)", f"{performance_ratio:.1f}X")
        col6.metric("Customer Rating", customer_rating)

        st.markdown(f"**Status:** {perf_status_display}", unsafe_allow_html=True)

        st.markdown("### 📈 Visualizations")

        st.altair_chart(monthly_performance_for_branch_chart(branch_df, selected_branch), use_container_width=True)

        # Individual Employee Performance Table
        st.markdown("### 🧑‍💼 Individual Performance")

        individual_cols = ['Date', 'EmployeeID', 'EmployeeName', 'Position', 'Revenue', 'Expense', 'Salary', 'Net Income']
        performance_table = branch_df[individual_cols].copy()

        # Compute Status (Sales/Expenses) for each employee
        performance_table['Total Expenses'] = performance_table['Expense'] + performance_table['Salary']
        performance_table['Status (Sales/Expense)'] = performance_table.apply(
            lambda row: f"{(row['Revenue'] / row['Total Expenses']):.1f}X" if row['Total Expenses'] > 0 else "∞", axis=1
        )
        # Add Customer Rating column (placeholder)
        performance_table['Customer Rating'] = "4.8 / 5.0"  # Placeholder, replace if available

        # Add Transactions count per employee
        trans_count = df.groupby('EmployeeID')['Date'].count().reset_index().rename(columns={'Date':'Transactions'})
        performance_table = performance_table.merge(trans_count, on='EmployeeID', how='left')

        performance_table_display_cols = ['EmployeeName', 'Position', 'Revenue', 'Expense', 'Salary', 'Net Income', 'Status (Sales/Expense)', 'Customer Rating', 'Transactions']
        performance_table_display = performance_table[performance_table_display_cols]

        # Format currency columns
        for col in ['Revenue', 'Expense', 'Salary', 'Net Income']:
            performance_table_display[col] = performance_table_display[col].apply(lambda x: f"${x:,.0f}")

        st.dataframe(performance_table_display.style.set_properties(**{'text-align': 'center'}))

else:
    st.warning("Please upload all three CSV files in the sidebar to load data.")

