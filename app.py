import pandas as pd
import streamlit as st
import altair as alt

st.set_page_config(page_title="Employee Dashboard", layout="wide")
st.title("📊 Company Employee Dashboard with Transactions")

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
    pivot_df['Revenue'] = pd.to_numeric(pivot_df.get('Revenue', 0), errors='coerce').fillna(0)
    pivot_df['Expense'] = pd.to_numeric(pivot_df.get('Expense', 0), errors='coerce').fillna(0)
    pivot_df['Salary'] = pd.to_numeric(pivot_df.get('Salary', 0), errors='coerce').fillna(0)
    pivot_df['Net Income'] = pivot_df['Revenue'] - pivot_df['Expense'] - pivot_df['Salary']

    return pivot_df

# --- Helper function for performance label ---
def performance_label(net_income, total_expenses):
    # If total_expenses is zero, avoid division by zero
    if total_expenses == 0:
        return "NPW"
    return "PW" if net_income >= 3 * total_expenses else "NPW"

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
    selected_branches = st.sidebar.multiselect("Select Branch(es)", ["All"] + branches, default=["All"])
    selected_employees = st.sidebar.multiselect("Select Employee(s)", ["All"] + employees, default=["All"])

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

        if selected_branches != ["All"]:
            filtered_df = filtered_df[filtered_df['BranchName'].isin(selected_branches)]

        if selected_employees != ["All"]:
            filtered_df = filtered_df[filtered_df['EmployeeName'].isin(selected_employees)]

        # Handle branch click via session state
        if 'clicked_branch' in st.session_state:
            clicked_branch = st.session_state.clicked_branch
            filtered_df = filtered_df[filtered_df['BranchName'] == clicked_branch]

        # Net income recalc
        filtered_df['Net Income'] = filtered_df.get('Revenue', 0) - filtered_df.get('Expense', 0) - filtered_df.get('Salary', 0)

        # --- Metrics ---
        total_sales = filtered_df['Revenue'].sum()
        total_expenses = filtered_df['Expense'].sum() + filtered_df['Salary'].sum()
        net_income = total_sales - total_expenses
        avg_customer_rating = 4.69
        total_branches = filtered_df['BranchName'].nunique()
        top_performing_branches = filtered_df.groupby('BranchName').apply(
            lambda x: performance_label(x['Net Income'].sum(), x['Expense'].sum() + x['Salary'].sum())
        ).value_counts().get("PW", 0)
        total_employees = filtered_df['EmployeeID'].nunique()

        # --- Show Metrics ---
        with st.container():
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Sales", f"${total_sales:,.0f}")
            col2.metric("Total Expenses", f"${total_expenses:,.0f}")
            col3.metric("Net Income", f"${net_income:,.0f}")
            col4.metric("Avg. Customer Rating", f"{avg_customer_rating:.2f}")

            col5, col6, col7 = st.columns(3)
            col5.metric("Total Branches", total_branches)
            col6.metric("Top Performing Branches", f"{top_performing_branches} / {total_branches}")
            col7.metric("Total Employees", total_employees)

        # --- Branch Summary ---
        st.subheader("📍 Summary by Branch")
        branch_summary = filtered_df.groupby("BranchName")[['Expense', 'Revenue', 'Salary', 'Net Income']].sum().reset_index()

        # Add performance label column
        branch_summary['Performance'] = branch_summary.apply(
            lambda row: performance_label(row['Net Income'], row['Expense'] + row['Salary']),
            axis=1
        )

        # Altair bar chart for branch summary with clickable bars
        click = alt.selection_single(fields=['BranchName'], bind='legend', name="branch_click", clear="mouseout", empty="none")

        chart = alt.Chart(branch_summary).mark_bar().encode(
            x=alt.X('BranchName:N', sort='-y'),
            y='Net Income:Q',
            color=alt.condition(click, alt.value("green"), alt.value("red")),
            tooltip=['BranchName', 'Expense', 'Revenue', 'Salary', 'Net Income', 'Performance'],
            opacity=alt.condition(click, alt.value(1), alt.value(0.3))
        ).add_selection(click).properties(width=700, height=400)

        st.altair_chart(chart, use_container_width=True)

        # Save branch selection in session state
        if click.selected:
            st.session_state.clicked_branch = click.selected['BranchName']

        # Branch summary table with performance shortcut
        display_branch_summary = branch_summary.copy()
        display_branch_summary['Performance'] = display_branch_summary['Performance'].replace({'PW': 'Performing Well (PW)', 'NPW': 'Not Performing Well (NPW)'})

        st.dataframe(display_branch_summary.style.format({
            'Expense': '${:,.2f}',
            'Revenue': '${:,.2f}',
            'Salary': '${:,.2f}',
            'Net Income': '${:,.2f}'
        }).set_table_styles([{'selector': 'th.row_heading, td.row_heading, th.blank', 'props': [('display', 'none')]}]))

        st.markdown("---")

        # --- Employee Summary ---
        st.subheader("🧑‍💼 Summary by Employee")
        employee_summary = filtered_df.groupby("EmployeeName")[['Expense', 'Revenue', 'Salary', 'Net Income']].sum().reset_index()

        # Add performance label column for employees
        employee_summary['Performance'] = employee_summary.apply(
            lambda row: performance_label(row['Net Income'], row['Expense'] + row['Salary']),
            axis=1
        )

        display_employee_summary = employee_summary.copy()
        display_employee_summary['Performance'] = display_employee_summary['Performance'].replace({'PW': 'Performing Well (PW)', 'NPW': 'Not Performing Well (NPW)'})

        st.dataframe(display_employee_summary.style.format({
            'Expense': '${:,.2f}',
            'Revenue': '${:,.2f}',
            'Salary': '${:,.2f}',
            'Net Income': '${:,.2f}'
        }).set_table_styles([{'selector': 'th.row_heading, td.row_heading, th.blank', 'props': [('display', 'none')]}]))

        st.markdown("---")

        # --- Detailed Transactions ---
        st.subheader("📄 Detailed Transactions by Employee")
        st.dataframe(filtered_df.style.format({
            'Revenue': '${:,.2f}',
            'Expense': '${:,.2f}',
            'Salary': '${:,.2f}',
            'Net Income': '${:,.2f}'
        }))

        st.markdown("---")

        # --- Financials by Branch (Bar Chart side by side) ---
        st.subheader("🏢 Financials by Branch")

        # Calculate Good and Review Net Income
        branch_summary['Net Income Status'] = branch_summary['Performance'].apply(lambda x: 'Net Income (Good)' if x == 'PW' else 'Net Income (Review)')
        financials_melted = branch_summary.melt(id_vars=['BranchName'], value_vars=['Expense', 'Revenue'], var_name='Metric', value_name='Amount')

        # Add net income metrics with status
        net_income_good = branch_summary[branch_summary['Performance'] == 'PW'][['BranchName', 'Net Income']]
        net_income_good['Metric'] = 'Net Income (Good)'

        net_income_review = branch_summary[branch_summary['Performance'] == 'NPW'][['BranchName', 'Net Income']]
        net_income_review['Metric'] = 'Net Income (Review)'

        # Combine all metrics
        combined_metrics = pd.concat([financials_melted, net_income_good.rename(columns={'Net Income': 'Amount'}),
                                      net_income_review.rename(columns={'Net Income': 'Amount'})], ignore_index=True)

        # Filter out rows with NaN amounts (some branches might not appear in net income good/review)
        combined_metrics = combined_metrics.dropna(subset=['Amount'])

        bar_chart = alt.Chart(combined_metrics).mark_bar().encode(
            x=alt.X('BranchName:N', title="Branch"),
            y=alt.Y('Amount:Q', title="Amount ($)"),
            color='Metric:N',
            tooltip=['BranchName', 'Metric', 'Amount']
        ).properties(width=800, height=400)

        st.altair_chart(bar_chart, use_container_width=True)

        st.markdown("---")

        # --- 12-Month Company Performance (Net Income Trend) ---
        st.subheader("📅 12-Month Company Net Income Trend")

        monthly_perf = filtered_df.groupby(['Year', 'Month']).agg({
            'Revenue': 'sum',
            'Expense': 'sum',
            'Salary': 'sum',
            'Net Income': 'sum'
        }).reset_index()

        monthly_perf['MonthStr'] = monthly_perf.apply(lambda row: f"{row['Year']}-{int(row['Month']):02d}", axis=1)

        line_chart = alt.Chart(monthly_perf).transform_fold(
            ['Revenue', 'Expense', 'Salary', 'Net Income'],
            as_=['Metric', 'Amount']
        ).mark_line(point=True).encode(
            x='MonthStr:T',
            y='Amount:Q',
            color='Metric:N',
            tooltip=['MonthStr', 'Metric', 'Amount']
        ).properties(width=900, height=400)

        st.altair_chart(line_chart, use_container_width=True)

    else:
        st.info("👈 Use the filters and click **Fetch Data** to update the dashboard.")
else:
    st.warning("🚨 Please upload all three CSV files in the sidebar to get started.")
