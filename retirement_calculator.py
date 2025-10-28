import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Retirement Planner", page_icon="💼", layout="centered")
st.title("💼 Retirement Planner")

colA, colB = st.columns(2)

# Inputs
acct_type = colA.selectbox("Account Type", ["401(k)", "Traditional IRA", "Roth IRA", "Taxable", "403(b)", "SEP IRA", "Solo 401(k)"])
age = colA.number_input("Current Age", min_value=18, max_value=80, value=28, step=1)
retire_age = colA.number_input("Planned Retirement Age", min_value=age + 1, max_value=90, value=65, step=1)
income = colA.number_input("Current Annual Income ($)", min_value=0.0, value=90000.0, step=1000.0, format="%.2f")
pct_income_needed = colA.slider("Percent of Income Needed in Retirement", min_value=30, max_value=120, value=80, step=1)

current_savings = colB.number_input("Current Savings ($)", min_value=0.0, value=50000.0, step=1000.0, format="%.2f")
monthly_contrib = colB.number_input("Monthly Contribution ($)", min_value=0.0, value=1000.0, step=100.0, format="%.2f")
exp_return_pre = colB.number_input("Expected Annual Return Before Retirement (%)", min_value=0.0, max_value=20.0, value=7.0, step=0.1, format="%.1f")
exp_return_post = colB.number_input("Expected Annual Return After Retirement (%)", min_value=0.0, max_value=20.0, value=4.0, step=0.1, format="%.1f")
inflation = colB.number_input("Expected Annual Inflation (%)", min_value=0.0, max_value=10.0, value=2.5, step=0.1, format="%.1f")

adjust_for_inflation = st.checkbox("Adjust retirement spending for inflation?", value=True)

# --- Core Calculations ---
years_to_retire = retire_age - age
r_pre = exp_return_pre / 100
r_post = exp_return_post / 100
i = inflation / 100
rm = r_pre / 12
n_months = years_to_retire * 12

fv_contribs = monthly_contrib * (((1 + rm) ** n_months - 1) / rm)
fv_savings = current_savings * (1 + rm) ** n_months
balance_at_retirement = fv_savings + fv_contribs

if adjust_for_inflation:
    spend_at_retirement = income * (pct_income_needed / 100) * ((1 + i) ** years_to_retire)
else:
    spend_at_retirement = income * (pct_income_needed / 100)

# --- Post-Retirement Drawdown ---
horizon_max_age = 110
years_post = horizon_max_age - retire_age
ages = []
balances = []
spends = []
b = balance_at_retirement
s = spend_at_retirement

for y in range(years_post + 1):
    ages.append(retire_age + y)
    balances.append(max(b, 0))
    spends.append(s)
    if b <= 0:
        break
    b = b * (1 + r_post) - s
    s = s * (1 + i)

# --- Pre-Retirement Growth ---
df_growth_years = list(range(age, retire_age + 1))
growth_balances = []
for yr in df_growth_years:
    m = (yr - age) * 12
    fv_c = monthly_contrib * (((1 + rm) ** m - 1) / rm) if m > 0 else 0
    fv_s = current_savings * (1 + rm) ** m
    growth_balances.append(fv_c + fv_s)

df_pre = pd.DataFrame({"Age": df_growth_years, "Balance": growth_balances})
df_post = pd.DataFrame({"Age": ages, "Balance": balances, "Spending": spends})

runout_age = int(df_post["Age"].iloc[-1]) if df_post["Balance"].iloc[-1] <= 0 else None

# --- Results ---
st.subheader("Results")
col1, col2, col3 = st.columns(3)
col1.metric("Balance at Retirement", f"${balance_at_retirement:,.0f}")
col2.metric("Initial Annual Spending", f"${spend_at_retirement:,.0f}")
col3.metric("Money Runs Out", "Does not run out" if runout_age is None else f"Age {runout_age}")

st.caption(f"Pre-retirement return: {exp_return_pre:.1f}% | Post-retirement return: {exp_return_post:.1f}% | Inflation: {inflation:.1f}%")

# --- Plot ---
fig = go.Figure()
fig.add_trace(go.Scatter(x=df_pre["Age"], y=df_pre["Balance"], mode="lines", name="Pre-retirement"))
fig.add_trace(go.Scatter(x=df_post["Age"], y=df_post["Balance"], mode="lines", name="Post-retirement"))
fig.update_layout(title="Portfolio Balance Over Time", xaxis_title="Age", yaxis_title="Balance ($)", hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

# --- Optional Details ---
with st.expander("Show Calculation Table"):
    st.dataframe(pd.concat([df_pre.assign(Phase="Accumulation"), df_post.assign(Phase="Decumulation")], ignore_index=True))
