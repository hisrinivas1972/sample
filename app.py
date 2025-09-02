import pandas as pd
import streamlit as st
import altair as alt

st.set_page_config(page_title="Branch Performance Dashboard", layout="wide")

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

# --- Sidebar Upload ---
st.sidebar.header("📤 Upload CSV Files")
uploaded_employees = st.sidebar.file_uploader("Upload Employees CSV", type="csv")
uploaded_branches = st.sidebar.file_uploader("Upload Branches CSV", type="csv")
uploaded_transactions = st.sidebar.file_uploader("Upload Transactions CSV", type="csv")

# --- Load and Process Data ---
def load_data(emp_file, branch_file, trans_file):
    employees = pd.read_csv(emp_file)
    branches = pd.read_csv(branch_file)
    transactions = pd.read_csv(trans_file)

    # Parse date safely
    transactions['Date'] = pd.to_datetime(transactions['Date'], errors='coerce', dayfirst=True)

    # Merge
    emp_branch = pd.merge(employees, branches, on='BranchID', how='left')
    df = pd.merge(transactions, emp_branch, on='EmployeeID', how='left')

    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month

    return df

# --- Financials by Branch Chart ---
def financials_by_branch_chart(df):
    summary = df.groupby("BranchName")[["Amount"]].sum().reset_index()
    pivot = df.pivot_table(index='BranchName', columns='Type', values='Amount', aggfunc='sum', fill_value=0).reset_index()
    if 'Salary' not in pivot: pivot['Salary'] = 0
    if 'Expense' not in pivot: pivot['Expense'] = 0
    if 'Revenue' not in pivot: pivot['Revenue'] = 0
    pivot['Total Expenses'] = pivot['Expense'] + pivot['Salary']
    pivot['Net Income'] = pivot['Revenue'] - pivot['Total Expenses']
    pivot["Net Income Category"] = pivot["Net Income"].apply(lambda x: "Net Income (Good)" if x > 0 else "Net Income (Review)")

    bar_df = pivot.melt(
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
        color=alt.Color("Display Label:N", scale=color_scale),
        tooltip=["BranchName", "Metric", "Amount"],
        xOffset='Display Label:N'
    ).properties(width=600, height=400, title="📊 Financials by Branch")

    return chart

# --- Monthly Performance Chart ---
def monthly_performance_chart(df, title="📅 12-Month Performance"):
    df['Month_Year'] = df['Date'].dt.to_period('M').astype(str)
    pivot = df.pivot_table(index='Month_Year', columns='Type', values='Amount', aggfunc='sum', fill_value=0).reset_index()
    if 'Salary' not in pivot: pivot['Salary'] = 0
    if 'Expense' not in pivot: pivot['Expense'] = 0
    if 'Revenue' not in pivot: pivot['Revenue'] = 0

    pivot["Gross Sales"] = pivot["Revenue"]
    pivot["Total Expenses"] = pivot["Expense"] + pivot["Salary"]
    pivot["Net Sales"] = pivot["Gross Sales"] - pivot["Total Expenses"]

    bar_df = pivot.melt(
        id_vars=["Month_Year", "Net Sales"],
        value_vars=["Gross Sales", "Total Expenses"],
        var_name="Metric",
        value_name="Amount"
    )

    color = alt.Scale(domain=["Gross Sales", "Total Expenses"], range=["#9b59b6", "#e74c3c"])

    bar_chart = alt.Chart(bar_df).mark_bar().encode(
        x=alt.X("Month_Year:N", title="Month", axis=alt.Axis(labelAngle=-45)),
        y=alt.Y("Amount:Q", title="Amount ($)", stack=None),
        color=alt.Color("Metric:N", scale=color),
        xOffset="Metric:N",
        tooltip=["Month_Year", "Metric", "Amount"]
    )

    line_chart = alt.Chart(pivot).mark_line(point=True).encode(
        x=alt.X("Month_Year:N"),
        y=alt.Y("Net Sales:Q"),
        color=alt.value("#2ecc71"),
        tooltip=["Month_Year", "Net Sales"]
    )

    return alt.layer(bar_chart, line_chart).properties(width=700, height=400, title=title)

# --- Individual Employee Table ---
def show_employee_table(df):
    emp_summary = df.pivot_table(index=['EmployeeID', 'EmployeeName'], columns='Type', values='Amount', aggfunc='sum', fill_value=0).reset_index()
    if 'Salary' not in emp_summary: emp_summary['Salary'] = 0
    if 'Expense' not in emp_summary: emp_summary['Expense'] = 0
    if 'Revenue' not in emp_summary: emp_summary['Revenue'] = 0

    emp_summary["Net Income"] = emp_summary["Revenue"] - emp_summary["Expense"] - emp_summary["Salary"]
    emp_summary["Performance Ratio"] = emp_summary["Revenue"] / (emp_summary["Expense"] + emp_summary["Salary"]).replace(0, 1)
    emp_summary["Status"] = emp_summary["Performance Ratio"].apply(performance_status_display)
    emp_summary["Customer Rating"] = 4.69  # Placeholder

    st.markdown("### 🧑‍💼 Individual Performance")
    st.dataframe(emp_summary[[
        "EmployeeID", "EmployeeName", "Revenue", "Expense", "Salary", "Net Income", "Performance Ratio", "Status", "Customer Rating"
    ]].rename(columns={
        "Revenue": "Sales",
        "Expense": "Expenses"
    }))

# --- Main App Logic ---
if uploaded_employees and uploaded_branches and uploaded_transactions:
    df = load_data(uploaded_employees, uploaded_branches, uploaded_transactions)

    branches = sorted(df['BranchName'].dropna().unique())
    options = ["📊 Company Overview"] + [f"📍 {branch}" for branch in branches]
    selected = st.sidebar.radio("Choose Overview", options)

    if selected == "📊 Company Overview":
        st.title("📊 Company Overview")
        overall_df = df.copy()

    else:
        selected_branch = selected.replace("📍 ", "")
        st.title(f"📍 Branch Overview: {selected_branch}")
        overall_df = df[df['BranchName'] == selected_branch]

    # Compute stats
    total_sales = overall_df[df['Type'] == 'Revenue']['Amount'].sum()
    total_expense = overall_df[df['Type'] == 'Expense']['Amount'].sum()
    total_salary = overall_df[df['Type'] == 'Salary']['Amount'].sum()
    total_expenses = total_expense + total_salary
    net_income = total_sales - total_expenses
    employees_count = overall_df['EmployeeID'].nunique()
    branches_count = df['BranchName'].nunique()
    avg_rating = 4.69
    perf_ratio = total_sales / total_expenses if total_expenses > 0 else 0
    perf_status = performance_status_display(perf_ratio)

    # Show metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Sales", f"${total_sales:,.0f}")
    col2.metric("Total Expenses", f"${total_expenses:,.0f}")
    col3.metric("Net Income", f"${net_income:,.0f}")

    col4, col5, col6 = st.columns(3)
    col4.metric("Avg. Customer Rating", f"{avg_rating}")
    col5.metric("Total Branches", f"{branches_count}" if selected == "📊 Company Overview" else "1")
    col6.metric("Performance Ratio", f"{perf_ratio:.2f}x")

    st.markdown(f"**Performance Status:** {perf_status}", unsafe_allow_html=True)
    st.metric("Total Employees", employees_count)

    # Charts
    st.markdown("### 📈 Visualizations")
    if selected == "📊 Company Overview":
        st.altair_chart(financials_by_branch_chart(df), use_container_width=True)
        st.altair_chart(monthly_performance_chart(df, title="📅 12-Month Company Performance"), use_container_width=True)
    else:
        st.altair_chart(monthly_performance_chart(overall_df, title=f"📅 12-Month Branch Performance: {selected_branch}"), use_container_width=True)

    # Employee table
    show_employee_table(overall_df)

else:
    st.info("Please upload all three CSV files to continue.")
