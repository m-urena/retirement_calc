import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from supabase import create_client, Client

# ---------------------------
# STREAMLIT PAGE SETUP
# ---------------------------
st.set_page_config(
    page_title="Bison Wealth | 401(k) Growth Simulator",
    page_icon="🦬",
    layout="wide"
)

# ---------------------------
# BISON BRANDING + STYLING
# ---------------------------
st.markdown(
    """
    <style>
    .block-container {
        max-width: 1300px;
        padding-left: 3rem;
        padding-right: 3rem;
        margin: auto;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------------------
# LOGO
# ---------------------------
st.image("Bison Wealth Logo.png", width=140)

st.title("Bison Wealth 401(k) Growth Simulator")
st.write("Visualize how your 401(k) could grow **with and without Bison’s guidance.**")

# ---------------------------
# SUPABASE SETUP
# ---------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

TABLE_NAME = "submissions_app"   # ← fixed table name


# ---------------------------
# DEFAULT PARAMETERS
# ---------------------------
DEFAULT_AGE = 42
DEFAULT_SALARY = 84000
DEFAULT_BALANCE = 76500

SALARY_GROWTH = 0.03
EMPLOYEE_CONTRIB = 0.078
EMPLOYER_CONTRIB = 0.046
TOTAL_CONTRIB_RATE = EMPLOYEE_CONTRIB + EMPLOYER_CONTRIB

NON_HELP_RETURN = 0.0847
HELP_RETURN = NON_HELP_RETURN + 0.0332


# ---------------------------
# CALCULATE PROJECTIONS
# ---------------------------
def projection_monthly(start_balance, salary, years):
    """Returns baseline and with-help projections."""
    salaries = [salary * ((1 + SALARY_GROWTH) ** yr) for yr in range(years + 1)]
    annual_contribs = [s * TOTAL_CONTRIB_RATE for s in salaries]

    def grow(rate):
        total = start_balance
        curve = [start_balance]
        monthly_rate = (1 + rate) ** (1/12) - 1

        for contrib in annual_contribs:
            monthly_contrib = contrib / 12
            for _ in range(12):
                total = total * (1 + monthly_rate) + monthly_contrib
            curve.append(total)
        return curve

    baseline = grow(NON_HELP_RETURN)
    with_help = grow(HELP_RETURN)
    return baseline, with_help


# ---------------------------
# LAYOUT (SIDEBAR STYLE LEFT)
# ---------------------------
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Your Information")

    age = st.number_input("Your Age", min_value=18, max_value=120,
                          value=DEFAULT_AGE, step=1)

    salary_str = st.text_input(
        "Current Annual Salary ($)",
        value=f"{DEFAULT_SALARY:,}"
    )

    balance_str = st.text_input(
        "Current 401(k) Balance ($)",
        value=f"{DEFAULT_BALANCE:,}"
    )

    company = st.text_input("Company Name", placeholder="Enter or type 'Unknown'")

    # Parse numbers safely
    def parse_number(x):
        try:
            return float(x.replace(",", "").strip())
        except:
            return None

    salary = parse_number(salary_str)
    balance = parse_number(balance_str)

    calculate_button = st.button("Calculate", type="primary")


# ---------------------------
# RIGHT SIDE: GRAPH & RESULT PANEL
# ---------------------------
with col2:
    st.subheader("Estimated 401(k) Growth")

    if salary is None or balance is None:
        st.info("Please enter valid numeric inputs.")
        st.stop()

    years_to_65 = max(0, 65 - age)

    # ALWAYS calculate baseline graph so default graph loads automatically
    baseline, with_help = projection_monthly(balance, salary, years_to_65)
    ages = list(range(age, 65 + 1))

    # ---------------------------
    # MATPLOTLIB GRAPH
    # ---------------------------
    fig, ax = plt.subplots(figsize=(8, 4), dpi=130)

    ax.plot(ages, baseline, label=f"On Your Lonesome ({NON_HELP_RETURN*100:.1f}%)",
            color="#7D7D7D", linewidth=2.5)

    ax.plot(ages, with_help, label=f"With Bison by Your Side ({HELP_RETURN*100:.1f}%)",
            color="#25385A", linewidth=3.3)

    # End labels on right
    ax.text(65.1, baseline[-1], f"${baseline[-1]:,.0f}", color="#7D7D7D", fontsize=9)
    ax.text(65.1, with_help[-1], f"${with_help[-1]:,.0f}", color="#25385A", fontsize=11)

    ax.set_xlabel("Age", fontsize=10)
    ax.set_ylabel("Portfolio Value ($)", fontsize=10)

    ax.grid(True, linestyle="--", color="#DDDDDD")
    ax.set_facecolor("white")

    ax.legend(frameon=False, fontsize=9, loc="upper left")

    st.pyplot(fig)

    # CTA
    difference = with_help[-1] - baseline[-1]
    st.markdown(
        f"""
        <div style="text-align:center; margin-top:10px;">
            <p style="font-size:18px; color:#414546;">
                Is <strong style="color:#25385A;">${difference:,.0f}</strong>
                worth 30 minutes of your time?
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div style="text-align:center;">
            <a href="https://calendly.com/placeholder-link" target="_blank"
               style="background-color:#C17A49; color:white; padding:12px 26px;
                      text-decoration:none; border-radius:8px; font-weight:600;">
               Schedule a Conversation
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )


# ---------------------------
# SAVE TO SUPABASE ONLY WHEN CALCULATE IS CLICKED
# ---------------------------
if calculate_button:
    entry = {
        "age": age,
        "salary": salary,
        "balance": balance,
        "company": company if company.strip() != "" else "Unknown",
        "created_at": datetime.utcnow().isoformat()
    }

    try:
        supabase.table(TABLE_NAME).insert(entry).execute()
        st.success("Saved to database.")
    except Exception as e:
        st.error(f"Database error: {e}")


# ---------------------------
# DISCLOSURE
# ---------------------------
st.markdown("---")
st.caption("""
For illustrative purposes only. Assumes 3% annual salary growth and 12.4% of salary contributed annually
(7.8% employee, 4.6% employer). Compounded monthly.

Performance without help is the 5yr annualized return of the S&P Target Date 2035 Index (as of 12/04/2025).  
With help is increased by 3.32% based on the Hewitt Study.
""")
