import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Retirement Planner", page_icon="💼", layout="centered")
st.title("💼 Tax-Aware Retirement Planner")

colA, colB = st.columns(2)

# === Inputs ===
acct_type = colA.selectbox("Account Type", ["401(k)", "Traditional IRA", "Roth IRA", "Taxable", "403(b)", "SEP IRA", "Solo 401(k)"])
age = colA.number_input("Current Age", 18, 80, 28)
retire_age = colA.number_input("Planned Retirement Age", age + 1, 90, 65)
income = colA.number_input("Current Annual Income ($)", 0.0, 1e7, 90000.0, step=1000.0, format="%.2f")
pct_income_needed = colA.slider("Percent of Income Needed in Retirement", 30, 120, 80)

current_savings = colB.number_input("Current Savings ($)", 0.0, 1e8, 50000.0, step=1000.0, format="%.2f")
monthly_contrib = colB.number_input("Monthly Contribution ($)", 0.0, 1e5, 1000.0, step=100.0, format="%.2f")
exp_return_pre = colB.number_input("Expected Annual Return Before Retirement (%)", 0.0, 20.0, 7.0, step=0.1)
exp_return_post = colB.number_input("Expected Annual Return After Retirement (%)", 0.0, 20.0, 4.0, step=0.1)
inflation = colB.number_input("Expected Annual Inflation (%)", 0.0, 10.0, 2.5, step=0.1)

adjust_for_inflation = st.checkbox("Adjust retirement spending for inflation?", value=True)

tax_rate_income = st.slider("Ordinary Income Tax Rate (%)", 0, 50, 25)
tax_rate_capgains = st.slider("Capital Gains Tax Rate (%)", 0, 30, 15)

# === Setup ===
years_to_retire = retire_age - age
r_pre = exp_return_pre / 100
r_post = exp_return_post / 100
i = inflation / 100
tax_rate_income /= 100
tax_rate_capgains /= 100

# === Adjust accumulation by account type ===
if acct_type in ["401(k)", "Traditional IRA", "SEP IRA", "403(b)"]:
    eff_contrib = monthly_contrib
    eff_r_pre = r_pre
elif acct_type == "Roth IRA":
    eff_contrib = monthly_contrib * (1 - tax_rate_income)
    eff_r_pre = r_pre
else:  # Taxable
    eff_contrib = monthly_contrib * (1 - tax_rate_income)
    eff_r_pre = r_pre * (1 - tax_rate_capgains)

rm_eff = eff_r_pre / 12
n_months = years_to_retire * 12

fv_contribs = eff_contrib * (((1 + rm_eff) ** n_months - 1) / rm_eff)
fv_savings = current_savings * (1 + rm_eff) ** n_months
balance_at_retirement = fv_contribs + fv_savings

# === Convert to after-tax equivalent ===
if acct_type in ["401(k)", "Traditional IRA", "SEP IRA", "403(b)"]:
    after_tax_balance = balance_at_retirement * (1 - tax_rate_income)
elif acct_type == "Taxable":
    taxable_fraction = 0.8
    after_tax_balance = balance_at_retirement * (1 - taxable_fraction * tax_rate_capgains)
else:
    after_tax_balance = balance_at_retirement

# === Spending target ===
if adjust_for_inflation:
    spend_at_retirement = income * (pct_income_needed / 100) * ((1 + i) ** years_to_retire)
else:
    spend_at_retirement = income * (pct_income_needed / 100)

# === Post-retirement drawdown ===
horizon_max_age = 110
years_post = horizon_max_age - retire_age
ages, balances, spends = [], [], []
b = balance_at_retirement
s = spend_at_retirement

for y in range(years_post + 1):
    ages.append(retire_age + y)
    balances.append(max(b, 0))
    spends.append(s)

    if acct_type in ["401(k)", "Traditional IRA", "SEP IRA", "403(b)"]:
        withdrawal = s / (1 - tax_rate_income)
    elif acct_type == "Roth IRA":
        withdrawal = s
    else:
        withdrawal = s / (1 - tax_rate_capgains)

    if b <= 0:
        break
    b = b * (1 + r_post) - withdrawal
    s = s * (1 + i)

df_growth_years = list(range(age, retire_age + 1))
growth_balances = []
for yr in df_growth_years:
    m = (yr - age) * 12
    fv_c = eff_contrib * (((1 + rm_eff) ** m - 1) / rm_eff) if m > 0 else 0
    fv_s = current_savings * (1 + rm_eff) ** m
    growth_balances.append(fv_c + fv_s)

df_pre = pd.DataFrame({"Age": df_growth_years, "Balance": growth_balances})
df_post = pd.DataFrame({"Age": ages, "Balance": balances})
runout_age = int(df_post["Age"].iloc[-1]) if df_post["Balance"].iloc[-1] <= 0 else None

# === Output ===
st.subheader("Results")
c1, c2, c3 = st.columns(3)
c1.metric("Balance at Retirement (Pre-Tax)", f"${balance_at_retirement:,.0f}")
c2.metric("After-Tax Equivalent", f"${after_tax_balance:,.0f}")
c3.metric("Money Runs Out", "Does not run out" if runout_age is None else f"Age {runout_age}")

st.caption(f"Pre-ret return: {exp_return_pre:.1f}% | Post-ret: {exp_return_post:.1f}% | Inflation: {inflation:.1f}%")

fig = go.Figure()
fig.add_trace(go.Scatter(x=df_pre["Age"], y=df_pre["Balance"], mode="lines", name="Pre-retirement"))
fig.add_trace(go.Scatter(x=df_post["Age"], y=df_post["Balance"], mode="lines", name="Post-retirement"))
fig.update_layout(title=f"Portfolio Balance Over Time — {acct_type}",
                  xaxis_title="Age", yaxis_title="Balance ($)", hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)
