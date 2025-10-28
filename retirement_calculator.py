import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date

st.set_page_config(page_title="Bison Wealth | 401(k) Growth Simulator", page_icon="💼", layout="centered")

st.title("💼 Bison Wealth 401(k) Growth Simulator")
st.write("Visualize how your 401(k) could grow **with and without Bison’s guidance.**")

# --- Client info ---
st.subheader("Client Information")
col1, col2 = st.columns(2)
name = col1.text_input("Client Name")
dob = col2.date_input("Date of Birth", min_value=date(1900, 1, 1), max_value=date.today())

# Current age
if dob:
    today = date.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
else:
    age = 0

# --- Inputs ---
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
contribution_rate = employee_contrib + employer_contrib  # 12.4%

# Age-banded returns (tight estimates from your chart)
# tuples: (min_age, max_age_inclusive, non_help_rate, help_rate)
AGE_BANDS = [
    (25, 30, 0.078, 0.112),
    (30, 35, 0.082, 0.119),
    (35, 40, 0.080, 0.116),
    (40, 45, 0.078, 0.114),
    (45, 50, 0.076, 0.110),
    (50, 55, 0.066, 0.105),
    (55, 60, 0.059, 0.092),
    (61, 120, 0.046, 0.070),  # >60 bucket; start at 61 so 60 falls in prior band
]

def rates_for_age(a: int):
    # If under 25, clamp to first band; if 60 exactly, it uses 55–60
    if a < 25:
        return AGE_BANDS[0][2], AGE_BANDS[0][3]
    for lo, hi, non_help, help_rate in AGE_BANDS:
        if lo <= a <= hi:
            return non_help, help_rate
    # Fallback to last band
    lo, hi, non_help, help_rate = AGE_BANDS[-1]
    return non_help, help_rate

non_help_rate, help_rate = rates_for_age(age)

# --- Salary projection and contributions ---
salaries = [salary * ((1 + salary_growth_rate) ** yr) for yr in range(years + 1)]
annual_contribs = [s * contribution_rate for s in salaries]

def growth_projection(start_balance, contribs, rate):
    total = start_balance
    values = [start_balance]
    # End-of-year contribution convention
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

# On Your Lonesome line
fig.add_trace(go.Scatter(
    x=ages, y=baseline, mode="lines",
    name=f"On Your Lonesome ({non_help_rate*100:.1f}% | ${final_lonesome_val/1_000_000:.2f}M)",
    line=dict(color="#7D7D7D", width=3)
))

# With Help line
fig.add_trace(go.Scatter(
    x=ages, y=with_help, mode="lines",
    name=f"With Help ({help_rate*100:.1f}% | ${final_help_val/1_000_000:.2f}M)",
    line=dict(color="#57A3C4", width=4)
))

# --- Layout ---
fig.update_layout(
    title=f"Estimated 401(k) Growth for {name}" if name else "Estimated 401(k) Growth",
    title_font=dict(color="#414546", size=22),
    paper_bgcolor="white",
    plot_bgcolor="white",
    xaxis=dict(
        title="Age", color="#414546", gridcolor="#E0E0E0",
        range=[age, 65]  # stop exactly at 65
    ),
    yaxis=dict(title="Portfolio Value ($)", color="#414546", gridcolor="#E0E0E0"),
    legend=dict(bgcolor="white", font=dict(color="#414546")),
    hovermode="x unified",
    margin=dict(r=80, t=60, l=60, b=60)
)

st.plotly_chart(fig, use_container_width=True)



# --- Metrics + CTA ---
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
        <a href="https://calendly.com/placeholder-link" target="_blank"
           style="background-color:#57A3C4; color:white; padding:12px 24px;
                  text-decoration:none; border-radius:8px; font-weight:600;">
           Schedule a Conversation
        </a>
    </div>
    """,
    unsafe_allow_html=True
)

st.caption("For illustrative purposes only. Assumes 7.8% employee contribution, 4.6% employer contribution, 3% annual salary growth, and compound growth at 6.5% vs 9.8%.")
