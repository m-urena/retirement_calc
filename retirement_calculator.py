import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date

st.set_page_config(page_title="Bison Wealth | 401(k) Growth Simulator", page_icon="💼", layout="centered")

# --- Header ---
st.title("💼 Bison Wealth 401(k) Growth Simulator")
st.write("Visualize how your 401(k) could grow **with and without Bison’s guidance.**")

# --- Client info ---
st.subheader("Client Information")
col1, col2 = st.columns(2)
name = col1.text_input("Client Name")
dob = col2.date_input("Date of Birth", min_value=date(1900, 1, 1), max_value=date.today())

# --- Calculate current age ---
if dob:
    today = date.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
else:
    age = 0

# --- Inputs ---
st.subheader("401(k) Details")
colA, colB, colC = st.columns(3)
balance = colA.number_input("Current 401(k) Balance ($)", min_value=0.0, value=100000.0, step=1000.0, format="%.2f")
annual_contrib = colB.number_input("Your Annual Contribution ($)", min_value=0.0, value=10000.0, step=500.0, format="%.2f")
employer_contrib = colC.number_input("Employer Annual Contribution ($)", min_value=0.0, value=5000.0, step=500.0, format="%.2f")

# --- Constants ---
target_age = 65
years = max(0, target_age - age)
growth_rate_lonesome = 0.08
growth_rate_help = 0.1479

# --- Growth function ---
def future_value(balance, contrib, rate, years):
    total = balance
    values = [balance]
    for _ in range(years):
        total = total * (1 + rate) + contrib
        values.append(total)
    return values

total_contrib = annual_contrib + employer_contrib
baseline = future_value(balance, total_contrib, growth_rate_lonesome, years)
with_help = future_value(balance, total_contrib, growth_rate_help, years)
ages = list(range(age, target_age + 1))

# --- Plot ---
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=ages, y=baseline, mode="lines", name="On Your Lonesome (8%)",
    line=dict(color="#7D7D7D", width=3)
))
fig.add_trace(go.Scatter(
    x=ages, y=with_help, mode="lines", name="With Help (14.79%)",
    line=dict(color="#57A3C4", width=3)
))
fig.update_layout(
    title=f"Estimated 401(k) Growth for {name}" if name else "Estimated 401(k) Growth",
    title_font=dict(color="#414546", size=22),
    paper_bgcolor="white",
    plot_bgcolor="white",
    xaxis=dict(title="Age", color="#414546", gridcolor="#E0E0E0"),
    yaxis=dict(title="Portfolio Value ($)", color="#414546", gridcolor="#E0E0E0"),
    legend=dict(bgcolor="white", font=dict(color="#414546")),
    hovermode="x unified"
)
st.plotly_chart(fig, use_container_width=True)

# --- Summary metrics ---
st.markdown("---")
final_lonesome = baseline[-1]
final_help = with_help[-1]
c1, c2 = st.columns(2)
c1.metric("On Your Lonesome", f"${final_lonesome:,.0f}")
c2.metric("With Help", f"${final_help:,.0f}")

st.caption("For illustrative purposes only. Assumes annual compounding and consistent contributions.")
