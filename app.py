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
        index=['EmployeeID', 'EmployeeName', 'BranchName', 'Year', 'Month', 'Date'],
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

# --- Main App Logic ---
if uploaded_employees and uploaded_branches and uploaded_transactions:
    df = load_data(uploaded_employees, uploaded_branches, uploaded_transactions)

    # Sidebar overview selection
    branches = sorted(df['BranchName'].dropna().unique())
    overview_options = ["📊 Company Overview"] + [f"📍 {branch}" for branch in branches]

    st.sidebar.header("📋 Select Overview")
    selected_overview = st.sidebar.radio("Choose Overview", overview_options)

    if selected_overview == "📊 Company Overview":
        total_sales = df['Revenue'].sum()
        total_expenses = df['Expense'].sum() + df['Salary'].sum()
        net_income = total_sales - total_expenses
        avg_customer_rating = 4.69  # Placeholder or replace with real data
        total_branches = df['BranchName'].nunique()
        total_employees = df['EmployeeID'].nunique()

        performance_ratio = total_sales / total_expenses if total_expenses > 0 else float('inf')
        performance_status = "PW" if performance_ratio >= 3 else "NPW"
        perf_status_display = blinking_star() if performance_status == "PW" else "⭐"

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Sales", f"${total_sales:,.0f}")
        col2.metric("Total Expenses", f"${total_expenses:,.0f}")
        col3.metric("Net Income", f"${net_income:,.0f}")
        col4.metric("Avg. Customer Rating", f"{avg_customer_rating:.2f}")

        col5, col6, col7, col8 = st.columns(4)
        col5.metric("Total Branches", total_branches)
        col6.metric("Performance Ratio", f"{performance_ratio:.2f}x")
        col7.markdown(f"**Performance Status:** {perf_status_display}", unsafe_allow_html=True)
        col8.metric("Total Employees", total_employees)

        # Show charts side by side
        st.subheader("📈 Visualizations")
        c1, c2 = st.columns(2)
        with c1:
            st.altair_chart(financials_by_branch_chart(df), use_container_width=True)
        with c2:
            st.altair_chart(monthly_company_performance_chart(df), use_container_width=True)

    else:
        # Branch Overview
        branch_name = selected_overview.replace("📍 ", "")
        filtered_df = df[df['BranchName'] == branch_name]

        # Branch-level Metrics Summary
        total_sales = filtered_df['Revenue'].sum()
        total_expenses = filtered_df['Expense'].sum() + filtered_df['Salary'].sum()
        net_income = total_sales - total_expenses
        avg_customer_rating = 4.69  # Replace if you have per-branch rating
        total_branches = 1
        total_employees = filtered_df['EmployeeID'].nunique()

        performance_ratio = total_sales / total_expenses if total_expenses > 0 else float('inf')
        performance_status = "PW" if performance_ratio >= 3 else "NPW"
        perf_status_display = blinking_star() if performance_status == "PW" else "⭐"

        # Display metrics in columns (like company overview)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Sales", f"${total_sales:,.0f}")
        col2.metric("Total Expenses", f"${total_expenses:,.0f}")
        col3.metric("Net Income", f"${net_income:,.0f}")
        col4.metric("Avg. Customer Rating", f"{avg_customer_rating:.2f}")

        col5, col6, col7, col8 = st.columns(4)
        col5.metric("Total Branches", total_branches)
        col6.metric("Performance Ratio", f"{performance_ratio:.2f}x")
        col7.markdown(f"**Performance Status:** {perf_status_display}", unsafe_allow_html=True)
        col8.metric("Total Employees", total_employees)

        # Visualizations filtered for branch
        st.subheader(f"📈 Visualizations for {branch_name}")

        # Financials by branch chart filtered for this branch only
        def financials_by_single_branch_chart(df_branch):
            summary = df_branch.groupby("BranchName")[["Revenue", "Expense", "Salary"]].sum().reset_index()
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
                title=f"📊 Financials for {branch_name}"
            )

            return chart

        st.altair_chart(financials_by_single_branch_chart(filtered_df), use_container_width=True)

        # Monthly performance chart filtered to this branch
        def monthly_performance_for_branch_chart(df_branch):
            df_branch['Month_Year'] = df_branch['Date'].dt.to_period('M').astype(str)
            monthly = df_branch.groupby("Month_Year").agg({
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
                title=f"📅 12-Month Performance for {branch_name}"
            )

            return chart

        st.altair_chart(monthly_performance_for_branch_chart(filtered_df), use_container_width=True)

        # Employee performance summary table
        st.subheader(f"🧑‍💼 Employee Performance: {branch_name}")

        emp_summary = filtered_df.groupby(['EmployeeID', 'EmployeeName']).agg({
            'Revenue': 'sum',
            'Expense': 'sum',
            'Salary': 'sum',
            'Net Income': 'sum',
            'Date': 'count'  # Number of transactions
        }).reset_index()

        emp_summary['Performance Ratio'] = emp_summary.apply(
            lambda row: row['Revenue'] / (row['Expense'] + row['Salary']) if (row['Expense'] + row['Salary']) > 0 else float('inf'),
            axis=1
        )
        emp_summary['Performance Status'] = emp_summary['Performance Ratio'].apply(lambda r: "⭐✨" if r >= 3 else ("⭐" if r > 1 else ""))

        # Dummy Customer Rating per employee (replace if you have real data)
        emp_summary['Customer Rating'] = 4.69

        # Rename for display
        emp_summary = emp_summary.rename(columns={
            'EmployeeName': 'Employee',
            'Revenue': 'Sales',
            'Expense': 'Expenses',
            'Salary': 'Salary',
            'Net Income': 'Net Income',
            'Date': 'Transactions',
            'Performance Status': 'Status (Sales/Expense)'
        })

        st.dataframe(emp_summary[['Employee', 'Sales', 'Expenses', 'Salary', 'Net Income', 'Status (Sales/Expense)', 'Customer Rating', 'Transactions']])

else:
    st.warning("Please upload all three CSV files: Employees, Branches, and Transactions.")

