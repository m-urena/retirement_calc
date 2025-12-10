import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from PIL import Image
import os
from supabase import create_client

# --------------------------------------------------
# PAGE SETUP
# --------------------------------------------------
st.set_page_config(page_title="Bison Wealth | 401(k) Growth Simulator",
                   page_icon="🦬",
                   layout="wide")

st.markdown("""
<style>
.block-container {
    max-width: 1300px;
    padding-left: 3rem;
    padding-right: 3rem;
    margin: auto;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# LOAD LOGO
# --------------------------------------------------
logo_path = "Bison Wealth Logo.png"
if os.path.exists(logo_path):
    st.image(logo_path, width=150)

# --------------------------------------------------
# SUPABASE CLIENT
# --------------------------------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --------------------------------------------------
# DEFAULT VALUES
# --------------------------------------------------
DEFAULT_AGE = 42
DEFAULT_SALARY = 84000
DEFAULT_BALANCE = 76500

# --------------------------------------------------
# PAGE TITLE
# --------------------------------------------------
st.title("Bison Wealth 401(k) Growth Simulator")
st.write("Visualize how your 401(k) could grow **with and without Bison’s guidance.**")

# ==================================================
# LEFT COLUMN — INPUTS
# RIGHT COLUMN — GRAPH
# ==================================================
left, right = st.columns([1, 2])

with left:
    st.subheader("Your Information")

    age = st.number_input("Your Age", min_value=18, max_value=120, value=DEFAULT_AGE, step=1)
    salary_str = st.text_input("Current Annual Salary ($)", value=f"{DEFAULT_SALARY:,}")
    balance_str = st.text_input("Current 401(k) Balance ($)", value=f"{DEFAULT_BALANCE:,}")

    # Company selection (autocomplete style)
    company_input = st.text_input("Your Company (type name)")
    company_list = []  # Later you will fill this with real companies

    final_company = company_input if company_input else "My company is not listed"

    calculate = st.button("Calculate")

# Utility to parse comma numbers
def parse_number(x):
    try:
        return float(x.replace(",", "").strip())
    except:
        return None

balance = parse_number(balance_str)
salary = parse_number(salary_str)

# ==================================================
# CHART CALCULATION LOGIC
# ==================================================

# Defaults for initial chart before clicking Calculate
plot_age = DEFAULT_AGE
plot_salary = DEFAULT_SALARY
plot_balance = DEFAULT_BALANCE

run_projection = False

if calculate and balance and salary:
    # User clicked calculate and inputs are valid
    plot_age = age
    plot_salary = salary
    plot_balance = balance
    run_projection = True

# --------------------------------------------------
# RUN PROJECTION USING plot_* VARIABLES
# --------------------------------------------------

target_age = 65
years = max(0, target_age - plot_age)

salary_growth_rate = 0.03
employee_contrib = 0.078
employer_contrib = 0.046
contribution_rate = employee_contrib + employer_contrib

non_help_rate = 0.0847
help_rate = non_help_rate + 0.0332

salaries = [plot_salary * ((1 + salary_growth_rate) ** yr) for yr in range(years + 1)]
annual_contribs = [s * contribution_rate for s in salaries]

def growth_projection_monthly(start_balance, annual_contribs, annual_rate):
    total = start_balance
    values = [start_balance]
    monthly_rate = (1 + annual_rate) ** (1 / 12) - 1
    for yearly_contrib in annual_contribs:
        monthly_contrib = yearly_contrib / 12
        for _ in range(12):
            total = total * (1 + monthly_rate) + monthly_contrib
        values.append(total)
    return values

baseline = growth_projection_monthly(plot_balance, annual_contribs, non_help_rate)
with_help = growth_projection_monthly(plot_balance, annual_contribs, help_rate)

ages = list(range(plot_age, target_age + 1))

final_lonesome_val = baseline[-1]
final_help_val = with_help[-1]
difference = final_help_val - final_lonesome_val

# ==================================================
# RIGHT COLUMN — GRAPH
# ==================================================

with right:
    st.subheader("Estimated 401(k) Growth")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ages, y=baseline,
        mode="lines",
        name=f"On Your Lonesome ({non_help_rate*100:.1f}%)",
        line=dict(color="#7D7D7D", width=3)
    ))

    fig.add_trace(go.Scatter(
        x=ages, y=with_help,
        mode="lines",
        name=f"With Bison by Your Side ({help_rate*100:.1f}%)",
        line=dict(color="#25385A", width=6)
    ))

    fig.add_annotation(
        x=ages[-1], y=baseline[-1],
        text=f"${baseline[-1]:,.0f}",
        showarrow=False,
        font=dict(color="#7D7D7D", size=13)
    )

    fig.add_annotation(
        x=ages[-1], y=with_help[-1],
        text=f"${with_help[-1]:,.0f}",
        showarrow=False,
        font=dict(color="#25385A", size=16)
    )

    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        xaxis=dict(title="Age", color="#414546", gridcolor="#E0E0E0"),
        yaxis=dict(title="Portfolio Value ($)", color="#414546", gridcolor="#E0E0E0"),
        legend=dict(bgcolor="white", font=dict(color="#414546")),
        height=450
    )

    st.plotly_chart(fig, use_container_width=True)

# ==================================================
# CTA + DIFFERENCE TEXT
# ==================================================

st.markdown(
    f"""
    <div style="text-align:center; margin-top:10px; margin-bottom:20px;">
        <p style="font-size:18px; color:#414546;">
            Is <span style="color:#25385A; font-weight:700;">${difference:,.0f}</span>
            worth 30 minutes of your time?
        </p>
        <a href="https://calendly.com/placeholder-link" target="_blank"
           style="background-color:#C17A49; color:white; padding:12px 24px;
                  text-decoration:none; border-radius:8px; font-weight:600;">
           Schedule a Conversation
        </a>
    </div>
    """,
    unsafe_allow_html=True
)

# ==================================================
# STORE DATA ONLY AFTER CLICK
# ==================================================

if run_projection:
    supabase.table("user_inputs").insert({
        "age": plot_age,
        "salary": plot_salary,
        "balance": plot_balance,
        "company": final_company
    }).execute()

# ==================================================
# DISCLOSURE SECTION
# --------------------------------------------------
st.markdown("<br><br><br>", unsafe_allow_html=True)

st.caption("""
For illustrative purposes only. Assumes 3% annual salary growth and 12.4% annual 401(k) contributions
(7.8% employee + 4.6% employer). Compounded monthly.

Performance without help is the 5yr annualized return of the S&P Target Date 2035 Index (as of 12/04/2025).
Performance with help is increased by 3.32% based on the Hewitt Study.
""")
