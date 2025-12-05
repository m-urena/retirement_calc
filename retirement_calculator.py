import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date
from PIL import Image
import os

st.set_page_config(page_title="Bison Wealth | 401(k) Growth Simulator", page_icon="🦬", layout="wide")

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

# --- Logo ---
logo_path = "Bison Wealth Logo.png"
if os.path.exists(logo_path):
    st.image(logo_path, width=220)

st.title("Bison Wealth 401(k) Growth Simulator")
st.write("Visualize how your 401(k) could grow **with and without Bison’s guidance.**")

# --------------------------------------------------
# NEW: ASK FOR AGE DIRECTLY (DEFAULT = 35)
# --------------------------------------------------
st.subheader("Client Information")
col1, col2 = st.columns(2)
name = col1.text_input("Client Name")
age = col2.number_input("Your Age", min_value=18, max_value=120, value=35, step=1)
# --------------------------------------------------
# 401(k) Inputs With Defaults
# --------------------------------------------------
st.subheader("401(k) Details")
colA, colB = st.columns(2)

balance_str = colA.text_input(
    "Current 401(k) Balance ($)",
    value="200,000",
    placeholder="Enter your balance"
)

salary_str = colB.text_input(
    "Current Annual Salary ($)",
    value="100,000",
    placeholder="Enter your salary"
)

# Convert to numbers safely
def parse_number(x):
    try:
        return float(x.replace(",", "").strip())
    except:
        return None

balance = parse_number(balance_str)
salary = parse_number(salary_str)

# Proceed only if inputs provided
if balance and salary:

    target_age = 65
    years = max(0, target_age - age)

    salary_growth_rate = 0.03
    employee_contrib = 0.078
    employer_contrib = 0.046
    contribution_rate = employee_contrib + employer_contrib

    AGE_BANDS = [
        (25, 30, 0.078, 0.112),
        (30, 35, 0.082, 0.119),
        (35, 40, 0.080, 0.116),
        (40, 45, 0.078, 0.114),
        (45, 50, 0.076, 0.110),
        (50, 55, 0.066, 0.105),
        (55, 60, 0.059, 0.092),
        (61, 120, 0.046, 0.070),
    ]

    def rates_for_age(a: int):
        if a < 25:
            return AGE_BANDS[0][2], AGE_BANDS[0][3]
        for lo, hi, non_help, help_rate in AGE_BANDS:
            if lo <= a <= hi:
                return non_help, help_rate
        return AGE_BANDS[-1][2], AGE_BANDS[-1][3]

    non_help_rate, help_rate = rates_for_age(age)

    salaries = [salary * ((1 + salary_growth_rate) ** yr) for yr in range(years + 1)]
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

    baseline = growth_projection_monthly(balance, annual_contribs, non_help_rate)
    with_help = growth_projection_monthly(balance, annual_contribs, help_rate)

    ages = list(range(age, target_age + 1))
    final_lonesome_val = baseline[-1]
    final_help_val = with_help[-1]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ages, y=baseline, mode="lines",
        name=f"On Your Lonesome ({non_help_rate*100:.1f}%)",
        line=dict(color="#7D7D7D", width=3)))
    fig.add_trace(go.Scatter(x=ages, y=with_help, mode="lines",
        name=f"With Help ({help_rate*100:.1f}%)",
        line=dict(color="#25385A", width=6)))

    fig.add_annotation(
        x=ages[-1] - 0.6, y=baseline[-1],
        text=f"${baseline[-1]:,.0f}",
        showarrow=False,
        font=dict(color="#7D7D7D", size=13),
        xanchor="right", yanchor="middle"
    )
    fig.add_annotation(
        x=ages[-1] - 0.6, y=with_help[-1],
        text=f"${with_help[-1]:,.0f}",
        showarrow=False,
        font=dict(color="#25385A", size=16),
        xanchor="right", yanchor="middle"
    )

    fig.update_layout(
        title=f"Estimated 401(k) Growth for {name}" if name else "Estimated 401(k) Growth",
        title_font=dict(color="#414546", size=22),
        paper_bgcolor="white", plot_bgcolor="white",
        xaxis=dict(title="Age", color="#414546", gridcolor="#E0E0E0", range=[age, 67]),
        yaxis=dict(title="Portfolio Value ($)", color="#414546", gridcolor="#E0E0E0"),
        legend=dict(bgcolor="white", font=dict(color="#414546")),
        hovermode="x unified",
        margin=dict(l=40, r=200, t=60, b=60),
        height=450
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown("---")

    difference = final_help_val - final_lonesome_val
    c1, c2 = st.columns(2)
    c1.metric("On Your Lonesome", f"${final_lonesome_val:,.0f}")
    with c2:
        st.markdown(
            f"""
            <div style="text-align:center; background-color:#F3F4F6;
                        border-radius:12px; padding:10px; border:1px solid #25385A;">
                <p style="color:#414546; font-weight:600; margin:0;">With Bison by Your Side</p>
                <p style="color:#25385A; font-size:24px; font-weight:700; margin:0;">
                    ${final_help_val:,.0f}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.markdown(
        f"""
        <div style="text-align:center; margin-top:20px; margin-bottom:50px;">
            <p style="font-size:18px; color:#414546; font-weight:500;">
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

    st.caption("""
    For illustrative purposes only. Assumes 3% annual salary growth and 12.4% of salary contributed annually
    (7.8% employee, 4.6% employer). Compounded monthly with age-adjusted annual returns.
    """)
else:
    st.info("Please enter your current 401(k) balance and salary to generate your projection.")
