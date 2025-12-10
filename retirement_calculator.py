import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from supabase import create_client
import datetime
from PIL import Image
import os

# ----------------------------------------------------------
# STREAMLIT PAGE CONFIG
# ----------------------------------------------------------
st.set_page_config(
    page_title="Bison Wealth | 401(k) Growth Simulator",
    page_icon="🦬",
    layout="wide"
)

# ----------------------------------------------------------
# PAGE WIDTH / THEME TWEAKS
# ----------------------------------------------------------
st.markdown("""
<style>
.block-container {
    max-width: 1400px;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------
# SUPABASE CONNECTION
# ----------------------------------------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_SERVICE_ROLE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def save_submission(age, salary, balance, company="Unknown"):
    try:
        supabase.table("submissions").insert({
            "age": age,
            "salary": salary,
            "balance": balance,
            "company": company,
            "created_at": datetime.datetime.utcnow().isoformat()
        }).execute()
    except Exception as e:
        print("Supabase insert failed:", e)

# ----------------------------------------------------------
# LOGO
# ----------------------------------------------------------
logo_path = "Bison Wealth Logo.png"
if os.path.exists(logo_path):
    st.image(logo_path, width=150)

# ----------------------------------------------------------
# TITLE + DESCRIPTION
# ----------------------------------------------------------
st.title("Bison Wealth 401(k) Growth Simulator")
st.write("Visualize how your 401(k) could grow **with and without Bison’s guidance.**")

# ----------------------------------------------------------
# INPUT SECTION — LEFT SIDE
# ----------------------------------------------------------
left, right = st.columns([1, 2])

with left:
    st.subheader("Your Information")

    age = st.number_input("Your Age", min_value=18, max_value=120, value=35, step=1)

    salary_str = st.text_input("Current Annual Salary ($)", value="100,000")

    balance_str = st.text_input("Current 401(k) Balance ($)", value="200,000")

    # Optional future feature (autocomplete list)
    company = "Unknown"

    # Convert values
    def parse_number(x):
        try:
            return float(x.replace(",", "").strip())
        except:
            return None

    salary = parse_number(salary_str)
    balance = parse_number(balance_str)

# ----------------------------------------------------------
# CALCULATIONS
# ----------------------------------------------------------
if balance and salary:

    target_age = 65
    years = max(0, target_age - age)

    salary_growth_rate = 0.03
    employee_contrib = 0.078
    employer_contrib = 0.046
    contribution_rate = employee_contrib + employer_contrib

    non_help_rate = 0.0847
    help_rate = non_help_rate + 0.0332

    salaries = [salary * ((1 + salary_growth_rate)**yr) for yr in range(years + 1)]
    annual_contribs = [s * contribution_rate for s in salaries]

    def growth_projection_monthly(start_balance, annual_contribs, annual_rate):
        total = start_balance
        values = [start_balance]
        monthly_rate = (1 + annual_rate)**(1/12) - 1

        for yearly_contrib in annual_contribs:
            monthly_contrib = yearly_contrib / 12
            for _ in range(12):
                total = total * (1 + monthly_rate) + monthly_contrib
            values.append(total)

        return values

    baseline = growth_projection_monthly(balance, annual_contribs, non_help_rate)
    with_help = growth_projection_monthly(balance, annual_contribs, help_rate)

    ages = list(range(age, target_age + 1))
    final_lonesome_val = baseline[-1]
    final_help_val = with_help[-1]

    # ----------------------------------------------------------
    # SAVE TO DATABASE
    # ----------------------------------------------------------
    save_submission(age, salary, balance, company)

    # ----------------------------------------------------------
    # GRAPH — RIGHT SIDE
    # ----------------------------------------------------------
    with right:
        st.subheader("Estimated 401(k) Growth")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=ages, y=baseline,
            mode="lines",
            name=f"On Your Lonesome (8.5%)",
            line=dict(color="#7D7D7D", width=3)
        ))

        fig.add_trace(go.Scatter(
            x=ages, y=with_help,
            mode="lines",
            name=f"With Bison by Your Side (11.8%)",
            line=dict(color="#25385A", width=6)
        ))

        fig.add_annotation(
            x=ages[-1], y=baseline[-1],
            text=f"${baseline[-1]:,.0f}",
            showarrow=False,
            font=dict(color="#7D7D7D", size=13),
            xanchor="left"
        )

        fig.add_annotation(
            x=ages[-1], y=with_help[-1],
            text=f"${with_help[-1]:,.0f}",
            showarrow=False,
            font=dict(color="#25385A", size=16),
            xanchor="left"
        )

        fig.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="white",
            xaxis=dict(title="Age", range=[age, 67], gridcolor="#E0E0E0"),
            yaxis=dict(title="Portfolio Value ($)", gridcolor="#E0E0E0"),
            margin=dict(l=20, r=20, t=10, b=20),
            height=450
        )

        st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------
# CTA SECTION — ALWAYS VISIBLE
# ----------------------------------------------------------
difference = final_help_val - final_lonesome_val if balance and salary else 0

st.markdown(
    f"""
    <div style="text-align:center; margin-top:20px;">
        <p style="font-size:18px; color:#414546;">
            Is <span style="color:#25385A; font-weight:700;">${difference:,.0f}</span>
            worth 30 minutes of your time?
        </p>
        <a href="https://calendly.com/placeholder-link" target="_blank"
           style="background-color:#25385A; color:white; padding:12px 24px;
                  text-decoration:none; border-radius:8px; font-weight:600;">
           Schedule a Conversation
        </a>
    </div>
    """,
    unsafe_allow_html=True
)

# ----------------------------------------------------------
# DISCLOSURE (moved far down)
# ----------------------------------------------------------
st.markdown("<br><br><br>", unsafe_allow_html=True)

st.caption("""
For illustrative purposes only. Assumes 3% annual salary growth and 12.4% of salary contributed annually
(7.8% employee, 4.6% employer). Compounded monthly.

Performance without help is the 5yr annualized return of the S&P Target Date 2035 Index as of 12/04/2025.
With help is increased by 3.32% based on the Hewitt Study.
""")
