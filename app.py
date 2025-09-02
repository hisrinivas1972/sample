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

def performance_status_display(ratio):
    if ratio >= 3:
        return blinking_star()
    elif ratio > 1:
        return "⭐"
    else:
        return ""

# --- File Uploads ---
st.sidebar.header("📤 Upload CSV Files")
uploaded_employees = st.sidebar.file_uploader("Upload Employees CSV", type="csv")
uploaded_branches = st.sidebar.file_uploader("Upload Branches CSV", type="csv")
uploaded_transactions = st.sidebar.file_uploader("Upload Transactions CSV", type="csv")

# --- Load and Prepare Data ---
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

    # Pivot transactions by Type for revenue, expense, salary
    pivot_df = df.pivot_table(
        index=['EmployeeID', 'EmployeeName', 'Position', 'BranchName', 'Date'],
        columns='Type',
        values='Amount',
        aggfunc='sum',
        fill_value=0
    ).reset_index()

    pivot_df.columns.name = None
    for col in ['Revenue', 'Expense', 'Salary']:
        if col not in pivot_df.columns:
            pivot_df[col] = 0

    pivot_df['Net Income'] = pivot_df['Revenue'] - pivot_df['Expense'] - pivot_df['Salary']
    pivot_df['Month_Year'] = pivot_df['Date'].dt.to_period('M').astype(str)

    df['Month_Year'] = df['Date'].dt.to_period('M').astype(str)

    return df, pivot_df

# --- Charts ---
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

    color_scale = alt.Scale(domain=["Net Income (Good)", "Net Income (Review)", "Total Expenses", "Revenue"],
                            range=["#2ecc71", "#f1c40f", "#e74c3c", "#9b59b6"])

    chart = alt.Chart(bar_df).mark_bar().encode(
        x=alt.X("BranchName:N", title="Branch", axis=alt.Axis(labelAngle=-30)),
        y=alt.Y("Amount:Q", title="Amount ($)", stack=None),
        color=alt.Color("Display Label:N", scale=color_scale, title="Metric"),
        tooltip=["BranchName", "Metric", "Amount"],
        xOffset='Display Label:N'
    ).properties(
        width=600, height=400, title="📊 Financials by Branch"
    )
    return chart

def monthly_performance_chart(df, title="📅 12-Month Performance"):
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

    color_scale = alt.Scale(domain=["Gross Sales", "Total Expenses"], range=["#9b59b6", "#e74c3c"])

    bar_chart = alt.Chart(bar_df).mark_bar().encode(
        x=alt.X("Month_Year:N", title="Month", axis=alt.Axis(labelAngle=-45)),
        y=alt.Y("Amount:Q", title="Amount ($)", stack=None),
        color=alt.Color("Metric:N", scale=color_scale),
        xOffset="Metric:N",
        tooltip=["Month_Year", "Metric", "Amount"]
    )

    line_chart = alt.Chart(monthly).mark_line(point=alt.OverlayMarkDef(color="#2ecc71", filled=True)).encode(
        x=alt.X("Month_Year:N"),
        y=alt.Y("Net Sales:Q"),
        color=alt.value("#2ecc71"),
        tooltip=["Month_Year", "Net Sales"]
    )

    return alt.layer(bar_chart, line_chart).properties(width=700, height=400, title=title)

# --- Main App Logic ---
if uploaded_employees and uploaded_branches and uploaded_transactions:
    raw_df, pivot_df = load_data(uploaded_employees, uploaded_branches, uploaded_transactions)

    branches = sorted(pivot_df['BranchName'].dropna().unique())
    overview_options = ["📊 Company Overview"] + [f"📍 {b}" for b in branches]
    selected = st.sidebar.radio("📋 Select Overview", overview_options)

    if selected == "📊 Company Overview":
        total_sales = pivot_df['Revenue'].sum()
        total_expenses = pivot_df['Expense'].sum() + pivot_df['Salary'].sum()
        net_income = total_sales - total_expenses
        avg_rating = 4.69
        total_branches = pivot_df['BranchName'].nunique()
        total_employees = pivot_df['EmployeeID'].nunique()
        ratio = total_sales / total_expenses if total_expenses > 0 else float('inf')
        status_display = blinking_star() if ratio >= 3 else ("⭐" if ratio > 1 else "")

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Sales", f"${total_sales:,.0f}")
        col2.metric("Total Expenses", f"${total_expenses:,.0f}")
        col3.metric("Net Income", f"${net_income:,.0f}")

        col4, col5, col6 = st.columns(3)
        col4.metric("Avg. Customer Rating", f"{avg_rating}")
        col5.metric("Total Branches", total_branches)
        col6.metric("Performance Ratio", f"{ratio:.2f}x")

        st.markdown(f"**Performance Status:** {status_display}", unsafe_allow_html=True)
        st.metric("Total Employees", total_employees)

        st.markdown("### 📈 Visualizations")
        st.altair_chart(financials_by_branch_chart(pivot_df), use_container_width=True)
        st.altair_chart(monthly_performance_chart(pivot_df, "📅 12-Month Company Performance"), use_container_width=True)

    else:
        branch = selected.replace("📍 ", "")
        branch_df = pivot_df[pivot_df['BranchName'] == branch]
        raw_branch_df = raw_df[raw_df['BranchName'] == branch]

        total_sales = branch_df['Revenue'].sum()
        total_expenses = branch_df['Expense'].sum() + branch_df['Salary'].sum()
        net_income = total_sales - total_expenses
        total_employees = branch_df['EmployeeID'].nunique()
        ratio = total_sales / total_expenses if total_expenses > 0 else float('inf')
        status_display = blinking_star() if ratio >= 3 else ("⭐" if ratio > 1 else "")

        avg_rating = 4.69  # Placeholder, update if you have branch rating data

        st.header(f"📍 Branch Overview: {branch}")

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Sales", f"${total_sales:,.0f}")
        col2.metric("Total Expenses", f"${total_expenses:,.0f}")
        col3.metric("Net Income", f"${net_income:,.0f}")

        col4, col5 = st.columns(2)
        col4.metric("Avg. Customer Rating", f"{avg_rating}")
        col5.metric("Performance Ratio", f"{ratio:.2f}x")

        st.markdown(f"**Performance Status:** {status_display}", unsafe_allow_html=True)
        st.metric("Total Employees", total_employees)

        st.markdown("### 🧑‍💼 Individual Performance")

        # Prepare employee-level summary for the branch (no Status column)
        emp_summary = branch_df.groupby(['EmployeeID', 'EmployeeName', 'Position']).agg({
            'Revenue': 'sum',
            'Expense': 'sum',
            'Salary': 'sum',
            'Net Income': 'sum'
        }).reset_index()

        # Transactions count & average rating (if available) from raw data
        trans_count = raw_branch_df.groupby('EmployeeID').size().reset_index(name='Transactions')
        # Assuming customer rating is available in raw_branch_df with a 'CustomerRating' column
        if 'CustomerRating' in raw_branch_df.columns:
            cust_rating = raw_branch_df.groupby('EmployeeID')['CustomerRating'].mean().reset_index(name='Avg Customer Rating')
            emp_summary = emp_summary.merge(cust_rating, on='EmployeeID', how='left')
        else:
            emp_summary['Avg Customer Rating'] = None

        emp_summary = emp_summary.merge(trans_count, on='EmployeeID', how='left')

        # Calculate Total Expenses per employee
        emp_summary['Total Expenses'] = emp_summary['Expense'] + emp_summary['Salary']

        # Select and order columns as requested (without Status)
        display_cols = ['EmployeeName', 'Position', 'Revenue', 'Total Expenses', 'Net Income', 'Avg Customer Rating', 'Transactions']
        emp_summary_display = emp_summary.rename(columns={
            'Revenue': 'Sales',
            'Avg Customer Rating': 'Customer Rating',
            'Transactions': 'Transactions'
        })[display_cols]

        st.dataframe(emp_summary_display.style.format({
            'Sales': '${:,.0f}',
            'Total Expenses': '${:,.0f}',
            'Net Income': '${:,.0f}',
            'Customer Rating': '{:.2f}',
            'Transactions': '{:.0f}'
        }), height=400)

        st.markdown("### 📈 Visualizations")
        st.altair_chart(financials_by_branch_chart(branch_df), use_container_width=True)
        st.altair_chart(monthly_performance_chart(branch_df, f"📅 12-Month Performance: {branch}"), use_container_width=True)

else:
    st.info("Please upload all three CSV files (Employees, Branches, Transactions) to proceed.")
