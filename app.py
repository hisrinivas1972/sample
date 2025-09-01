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
        index=['EmployeeID', 'EmployeeName', 'BranchName', 'Year', 'Month'],
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

# --- If all files uploaded ---
if uploaded_employees and uploaded_branches and uploaded_transactions:
    df = load_data(uploaded_employees, uploaded_branches, uploaded_transactions)

    # Prepare filter values
    years = sorted(df['Year'].dropna().unique())
    months = sorted(df['Month'].dropna().unique())
    branches = sorted(df['BranchName'].dropna().unique())
    employees = sorted(df['EmployeeName'].dropna().unique())
    month_names = {1:"Jan", 2:"Feb", 3:"Mar", 4:"Apr", 5:"May", 6:"Jun",
                   7:"Jul", 8:"Aug", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dec"}

    # --- Sidebar Filters ---
    st.sidebar.header("📅 Filters")
    selected_year = st.sidebar.selectbox("Select Year", ["All"] + [str(year) for year in years], index=0)
    selected_month = st.sidebar.selectbox("Select Month", ["All"] + [month_names[m] for m in months], index=0)
    selected_branches = st.sidebar.multiselect("Select Branch(es)", branches, default=branches)
    selected_employees = st.sidebar.multiselect("Select Employee(s)", employees, default=employees)

    # --- Fetch Data Button ---
    fetch_data = st.sidebar.button("🔍 Fetch Data")

    if fetch_data:
        filtered_df = df.copy()

        # Apply filters
        if selected_year != "All":
            filtered_df = filtered_df[filtered_df['Year'] == int(selected_year)]

        if selected_month != "All":
            month_num = [k for k, v in month_names.items() if v == selected_month][0]
            filtered_df = filtered_df[filtered_df['Month'] == month_num]

        if selected_branches:
            filtered_df = filtered_df[filtered_df['BranchName'].isin(selected_branches)]

        if selected_employees:
            filtered_df = filtered_df[filtered_df['EmployeeName'].isin(selected_employees)]

        # Net income recalculation
        filtered_df['Net Income'] = filtered_df['Revenue'] - filtered_df['Expense'] - filtered_df['Salary']

        # --- Metrics ---
        total_sales = filtered_df['Revenue'].sum()
        total_expenses = filtered_df['Expense'].sum() + filtered_df['Salary'].sum()
        net_income = total_sales - total_expenses
        avg_customer_rating = 4.69
        total_branches = filtered_df['BranchName'].nunique()
        top_performing_branches = filtered_df.groupby('BranchName')['Net Income'].sum().gt(0).sum()
        total_employees = filtered_df['EmployeeID'].nunique()

        if total_expenses > 0:
            performance_ratio = total_sales / total_expenses
        else:
            performance_ratio = float('inf')  # Prevent div by zero

        performance_status = "PW" if performance_ratio >= 3 else "NPW"

        # --- Show Metrics ---
        with st.container():
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Sales", f"${total_sales:,.0f}")
            col2.metric("Total Expenses", f"${total_expenses:,.0f}")
            col3.metric("Net Income", f"${net_income:,.0f}")
            col4.metric("Avg. Customer Rating", f"{avg_customer_rating:.2f}")

            col5, col6, col7, col8 = st.columns(4)
            col5.metric("Total Branches", total_branches)
            col6.metric("Performance Ratio", f"{performance_ratio:.2f}x")

            if performance_status == "PW":
                perf_status_display = blinking_star()
            else:
                perf_status_display = "⭐"

            col7.markdown(f"**Performance Status:** {perf_status_display}", unsafe_allow_html=True)
            col8.metric("Total Employees", total_employees)

        # --- Branch Summary ---
        st.subheader("📍 Summary by Branch")
        branch_summary = filtered_df.groupby("BranchName")[['Expense', 'Revenue', 'Salary', 'Net Income']].sum().reset_index()

        branch_summary['Performance Ratio'] = branch_summary.apply(
            lambda row: row['Revenue'] / (row['Expense'] + row['Salary']) if (row['Expense'] + row['Salary']) > 0 else float('inf'),
            axis=1
        )
        branch_summary['Performance Status'] = branch_summary['Performance Ratio'].apply(
            lambda x: "PW" if x >= 3 else "NPW"
        )

        click = alt.selection_single(fields=['BranchName'], bind='legend', name="branch_click", clear="mouseout", empty="none")

        chart = alt.Chart(branch_summary).mark_bar().encode(
            x='BranchName',
            y='Net Income',
            color=alt.condition(click, alt.value("green"), alt.value("red")),
            tooltip=['BranchName', 'Expense', 'Revenue', 'Salary', 'Net Income'],
            opacity=alt.condition(click, alt.value(1), alt.value(0.3))
        ).add_selection(click).properties(width=700, height=400)

        st.altair_chart(chart, use_container_width=True)

        st.dataframe(branch_summary.style.format({
            'Expense': '${:,.2f}',
            'Revenue': '${:,.2f}',
            'Salary': '${:,.2f}',
            'Net Income': '${:,.2f}',
            'Performance Ratio': '{:.2f}x'
        }))

        st.markdown("---")

        # --- Employee Summary ---
        st.subheader("🧑‍💼 Summary by Employee")
        employee_summary = filtered_df.groupby("EmployeeName")[['Expense', 'Revenue', 'Salary', 'Net Income']].sum().reset_index()

        employee_summary['Performance Ratio'] = employee_summary.apply(
            lambda row: row['Revenue'] / (row['Expense'] + row['Salary']) if (row['Expense'] + row['Salary']) > 0 else float('inf'),
            axis=1
        )
        employee_summary['Performance Status'] = employee_summary['Performance Ratio'].apply(
            lambda x: "PW" if x >= 3 else "NPW"
        )

        st.dataframe(employee_summary.style.format({
            'Expense': '${:,.2f}',
            'Revenue': '${:,.2f}',
            'Salary': '${:,.2f}',
            'Net Income': '${:,.2f}',
            'Performance Ratio': '{:.2f}x'
        }))

        st.markdown("---")

        # --- Detailed Transactions ---
        st.subheader("📄 Detailed Transactions by Employee")
        st.dataframe(filtered_df.style.format({
            'Revenue': '${:,.2f}',
            'Expense': '${:,.2f}',
            'Salary': '${:,.2f}',
            'Net Income': '${:,.2f}'
        }))

    else:
        st.info("👈 Use the filters and click **Fetch Data** to update the dashboard.")
else:
    st.warning("🚨 Please upload all three CSV files in the sidebar to get started.")
