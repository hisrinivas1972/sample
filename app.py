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

# --- Load and process data ---
def load_data(emp_file, branch_file, trans_file):
    employees = pd.read_csv(emp_file)
    branches = pd.read_csv(branch_file)
    transactions = pd.read_csv(trans_file)

    emp_branch = pd.merge(employees, branches, on='BranchID', how='left')
    df = pd.merge(transactions, emp_branch, on='EmployeeID', how='left')

    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
    df.dropna(subset=['Date'], inplace=True)

    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month

    pivot_df = df.pivot_table(
        index=['EmployeeID', 'EmployeeName', 'BranchName', 'Date'],
        columns='Type',
        values='Amount',
        aggfunc='sum',
        fill_value=0
    ).reset_index()

    pivot_df.columns = [col if not isinstance(col, tuple) else col[1] if col[1] else col[0] for col in pivot_df.columns]

    for col in ['Revenue', 'Expense', 'Salary']:
        if col not in pivot_df.columns:
            pivot_df[col] = 0
        else:
            pivot_df[col] = pd.to_numeric(pivot_df[col], errors='coerce').fillna(0)

    pivot_df['Net Income'] = pivot_df['Revenue'] - pivot_df['Expense'] - pivot_df['Salary']

    return df, pivot_df

# --- Financials by branch chart ---
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

# --- 12-Month Company Performance chart ---
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

# --- 12-Month Branch Performance chart ---
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

# --- Main App ---
if uploaded_employees and uploaded_branches and uploaded_transactions:
    raw_df, pivot_df = load_data(uploaded_employees, uploaded_branches, uploaded_transactions)

    branches = sorted(pivot_df['BranchName'].dropna().unique())
    overview_options = ["📊 Company Overview"] + [f"📍 {branch}" for branch in branches]

    st.sidebar.header("📋 Select Overview")
    selected_overview = st.sidebar.radio("Choose Overview", overview_options)

    if selected_overview == "📊 Company Overview":
        # Company-wide summary (branch level)
        summary = pivot_df.groupby("BranchName")[["Revenue", "Expense", "Salary", "Net Income"]].sum().reset_index()

        # Show blinking star for branches with positive Net Income
        summary["Star"] = summary["Net Income"].apply(lambda x: blinking_star() if x > 0 else "")

        # Branch Financials chart
        st.altair_chart(financials_by_branch_chart(pivot_df), use_container_width=True)

        # 12-month company performance
        st.altair_chart(monthly_company_performance_chart(raw_df), use_container_width=True)

        # Summary table (branch level only)
        st.subheader("Branch Summary")
        display_summary = summary[["BranchName", "Revenue", "Expense", "Salary", "Net Income", "Star"]]
        display_summary = display_summary.rename(columns={
            "BranchName": "Branch",
            "Revenue": "Revenue ($)",
            "Expense": "Expense ($)",
            "Salary": "Salary ($)",
            "Net Income": "Net Income ($)",
            "Star": "Status"
        })
        st.write(display_summary.style.format({
            "Revenue ($)": "${:,.2f}",
            "Expense ($)": "${:,.2f}",
            "Salary ($)": "${:,.2f}",
            "Net Income ($)": "${:,.2f}"
        }).hide(axis="index").set_properties(subset=["Status"], **{'text-align': 'center'}).set_table_styles([
            {'selector': 'th', 'props': [('text-align', 'center')]}
        ]), unsafe_allow_html=True)

    else:
        # Branch Overview: Show individual employee performance without "Status"
        branch_name = selected_overview.replace("📍 ", "")
        st.header(f"Branch Overview: {branch_name}")

        branch_data = pivot_df[pivot_df["BranchName"] == branch_name].copy()
        if branch_data.empty:
            st.warning(f"No data available for branch '{branch_name}'.")
        else:
            # Drop 'Status' column here if exists (you said not needed)
            # But you want individual rows here
            branch_data = branch_data[[
                "EmployeeID", "EmployeeName", "Date", "Revenue", "Expense", "Salary", "Net Income"
            ]]

            # Format Date nicely
            branch_data["Date"] = branch_data["Date"].dt.strftime('%Y-%m-%d')

            st.dataframe(branch_data.style.format({
                "Revenue": "${:,.2f}",
                "Expense": "${:,.2f}",
                "Salary": "${:,.2f}",
                "Net Income": "${:,.2f}"
            }))

            # Show 12-month branch performance chart
            st.altair_chart(monthly_performance_for_branch_chart(raw_df[raw_df["BranchName"] == branch_name], branch_name), use_container_width=True)

else:
    st.info("Please upload Employees, Branches, and Transactions CSV files to proceed.")
