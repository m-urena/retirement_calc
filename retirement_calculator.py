import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date
from PIL import Image
import os
from supabase import create_client

# ----------------------------------------------------
# STREAMLIT PAGE CONFIG
# ----------------------------------------------------
st.set_page_config(
    page_title="Bison Wealth | 401(k) Growth Simulator",
    page_icon="🦬",
    layout="wide"
)

st.markdown(
    """
    <style>
    .block-container {
        max-width: 1400px;
        padding-left: 2rem;
        padding-right: 2rem;
        margin: auto;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ----------------------------------------------------
# LOAD LOGO
# ----------------------------------------------------
logo_path = "Bison Wealth Logo.png"
if os.path.exists(logo_path):
    st.image(logo_path, width=150)


# ----------------------------------------------------
# SUPABASE CONNECTION
# ----------------------------------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# ----------------------------------------------------
# PAGE TITLE
# ----------------------------------------------------
st.title("Bison Wealth 401(k) Growth Simulator")
st.write("Visualize how your 401(k) could grow **with and without Bison’s guidance.**")


# ====================================================
# INPUT SECTION LAYOUT
# ====================================================
left, right = st.columns([1, 2])

with left:
    st.subheader("Your Information")

    age = st.number_input("Your Age", min_value=18, max_value=120, value=42, step=1)
    salary_str = st.text_input("Current Annual Salary ($)", value="84,000")
    balance_str = st.text_input("Current 401(k) Balance ($)", value="76,500")

    # --- Company Input ---
    companies = ["Microsoft", "Amazon", "Google", "Apple", "Meta",
                 "Oracle", "JPMorgan", "Delta", "UPS", "Home Depot"]
    company_input = st.text_input("Company Name", "")

    # Autocomplete suggestion
    matches = [c for c in companies if company_input.lower() in c.lower()]

    if company_input and matches:
        st.write("Did you mean:")
        for m in matches:
            st.write(f"- {m}")

    company_final = company_input if company_input else "Unknown"

    # Parse inputs
    def parse_number(x):
        try:
            return float(x.replace(",", "").strip())
        except:
            return None

    salary = parse_number(salary_str)
    balance = parse_number(balance_str)

    # CALCULATE BUTTON
    calculate = st.button("Calculate", type="primary")


# ====================================================
# RIGHT SIDE: GRAPH AREA
# ====================================================
with right:
    st.subheader("Estimated 401(k) Growth")

    # Always compute the projection using current values
if salary and balance:

    target_age = 65
    years = max(0, target_age - age)

    salary_growth_rate = 0.03
    contrib_rate = 0.124  # 12.4%

    # Static returns
    non_help_rate = 0.0847
    help_rate = non_help_rate + 0.0332

    salaries = [salary * ((1 + salary_growth_rate) ** yr) for yr in range(years + 1)]
    annual_contribs = [s * contrib_rate for s in salaries]

    def projection(start_balance, annual_contribs, annual_rate):
        total = start_balance
        values = [start_balance]
        monthly_rate = (1 + annual_rate) ** (1/12) - 1
        for yearly in annual_contribs:
            m = yearly / 12
            for _ in range(12):
                total = total * (1 + monthly_rate) + m
            values.append(total)
        return values

    baseline = projection(balance, annual_contribs, non_help_rate)
    help_vals = projection(balance, annual_contribs, help_rate)

    ages = list(range(age, target_age + 1))

    final_baseline = baseline[-1]
    final_help = help_vals[-1]
    diff = final_help - final_baseline

    # GRAPH (always shown)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ages, y=baseline,
        mode="lines",
        name=f"On Your Lonesome ({non_help_rate*100:.1f}%)",
        line=dict(color="#7D7D7D", width=3)
    ))
    fig.add_trace(go.Scatter(
        x=ages, y=help_vals,
        mode="lines",
        name=f"With Bison by Your Side ({help_rate*100:.1f}%)",
        line=dict(color="#25385A", width=5)
    ))

    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        xaxis=dict(title="Age", gridcolor="#E0E0E0"),
        yaxis=dict(title="Portfolio Value ($)", gridcolor="#E0E0E0"),
        height=400,
        margin=dict(l=10, r=10, t=25, b=10)
    )

    st.plotly_chart(fig, use_container_width=True)

    # CTA area
    st.markdown(
        f"""
        <div style="text-align:center; margin-top:10px;">
            Is <span style="color:#25385A; font-weight:700;">
                ${diff:,.0f}
            </span> worth 30 minutes of your time?
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div style="text-align:center; margin-top:5px; margin-bottom:15px;">
            <a href="https://calendly.com/placeholder-link" target="_blank"
            style="
                background-color:#C17A49;
                color:white;
                padding:12px 24px;
                text-decoration:none;
                border-radius:8px;
                font-weight:600;
                font-size:16px;
            ">
                Schedule a Conversation
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Only insert into database when user clicks Calculate
    if calculate:
        supabase.table("submissions").insert({
            "age": age,
            "salary": salary,
            "balance": balance,
            "company": company_final,
            "ip_address": st.session_state.get("ip"),
            "user_agent": st.session_state.get("ua")
        }).execute()


# ====================================================
# DISCLOSURE (far down)
# ====================================================
st.markdown("<br><br><br>", unsafe_allow_html=True)
st.caption("""
For illustrative purposes only. Assumes 3% annual salary growth and 12.4% annual contribution (7.8% employee, 4.6% employer).  
Performance without help is the 5yr annualized return of the S&P Target Date 2035 Index (as of 12/04/2025).  
With help is increased by 3.32% based on the Hewitt Study.
""")
