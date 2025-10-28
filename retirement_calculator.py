import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date

# --- Streamlit Page Config ---
st.set_page_config(
    page_title="Bison Wealth | 401(k) Growth Simulator",
    page_icon="💼",
    layout="wide"  # enables wider overall layout
)
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
# --- App Header ---
st.title("💼 Bison Wealth 401(k) Growth Simulator")
st.write("Visualize how your 401(k) could grow **with and without Bison’s guidance.**")

# --- Client Info ---
st.subheader("Client Information")
col1, col2 = st.columns(2)
name = col1.text_input("Client Name")
dob = col2.date_input("Date of Birth", min_value=date(1900, 1, 1), max_value=date.today())

# --- Calculate Age ---
if dob:
    today = date.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
else:
    age = 0

# --- 401(k) Inputs ---
st.subheader("401(k) Details")
colA, colB = st.columns(2)
balance = colA.number_input("Current 401(k) Balance ($)", min_value=0.0, value=100000.0, step=1000.0, format="%.2f")
salary = colB.number_input("Current Annual Salary ($)", min_value=0.0, value=90000.0, step=1000.0, format="%.2f")

# --- Assumptions ---
target_age = 65
years = max(0, target_age - age)
salary_growth_rate = 0.03
employee_contrib = 0.078
employer_contrib = 0.046
contribution_rate = employee_contrib + employer_contrib

# --- Age-banded Return Estimates ---
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

# --- Salary Growth and Contributions ---
salaries = [salary * ((1 + salary_growth_rate) ** yr) for yr in range(years + 1)]
annual_contribs = [s * contribution_rate for s in salaries]

def growth_projection(start_balance, contribs, rate):
    total = start_balance
    values = [start_balance]
    for c in contribs:
        total = total * (1 + rate) + c
        values.append(total)
    return values

baseline = growth_projection(balance, annual_contribs, non_help_rate)
with_help = growth_projection(balance, annual_contribs, help_rate)
ages = list(range(age, target_age + 1))

# --- Plot ---
final_lonesome_val = baseline[-1]
final_help_val = with_help[-1]

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=ages, y=baseline, mode="lines",
    name=f"On Your Lonesome ({non_help_rate*100:.1f}%)",
    line=dict(color="#7D7D7D", width=3)
))

fig.add_trace(go.Scatter(
    x=ages, y=with_help, mode="lines",
    name=f"With Help ({help_rate*100:.1f}%)",
    line=dict(color="#57A3C4", width=4)
))

# --- End value labels (just past 65) ---
fig.add_annotation(
    x=65.3, y=final_lonesome_val,
    text=f"${final_lonesome_val:,.0f}",
    showarrow=False,
    font=dict(color="#7D7D7D", size=13, family="Segoe UI"),
    xanchor="left", yanchor="middle"
)
fig.add_annotation(
    x=65.3, y=final_help_val,
    text=f"${final_help_val:,.0f}",
    showarrow=False,
    font=dict(color="#57A3C4", size=16, family="Segoe UI"),
    xanchor="left", yanchor="middle"
)

fig.update_layout(
    title=f"Estimated 401(k) Growth for {name}" if name else "Estimated 401(k) Growth",
    title_font=dict(color="#414546", size=22),
    paper_bgcolor="white",
    plot_bgcolor="white",
    xaxis=dict(title="Age", color="#414546", gridcolor="#E0E0E0", range=[age, 67]),
    yaxis=dict(title="Portfolio Value ($)", color="#414546", gridcolor="#E0E0E0"),
    legend=dict(bgcolor="white", font=dict(color="#414546")),
    hovermode="x unified",
    margin=dict(l=40, r=200, t=60, b=60),
    height=450
)

# --- Display Plot in Wider Container ---
wide_col = st.container()
with wide_col:
    st.plotly_chart(fig, use_container_width=True)

# --- Summary ---
st.markdown("---")
final_lonesome = baseline[-1]
final_help = with_help[-1]
difference = final_help - final_lonesome

c1, c2 = st.columns(2)
c1.metric("On Your Lonesome", f"${final_lonesome:,.0f}")
with c2:
    st.markdown(
        f"""
        <div style="text-align:center; background-color:#E6F4F9;
                    border-radius:12px; padding:10px; border:1px solid #57A3C4;">
            <p style="color:#414546; font-weight:600; margin:0;">With Bison by Your Side</p>
            <p style="color:#57A3C4; font-size:24px; font-weight:700; margin:0;">
                ${final_help:,.0f}
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
            Is <span style="color:#57A3C4; font-weight:700;">${difference:,.0f}</span>
            worth 30 minutes of your time?
        </p>
        <a href="https://calendly.com/your-placeholder-link" target="_blank"
           style="background-color:#57A3C4; color:white; padding:12px 24px;
                  text-decoration:none; border-radius:8px; font-weight:600;">
           Schedule a Conversation
        </a>
    </div>
    """,
    unsafe_allow_html=True
)

st.caption("""
For illustrative purposes only. Assumes 3% annual salary growth and 12.4% of salary contributed annually
(7.8% employee, 4.6% employer). Annual return band chosen from current age.
""")
