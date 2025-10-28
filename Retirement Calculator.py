#!/usr/bin/env python
# coding: utf-8

# In[1]:


import math
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="Retirement Planner", page_icon="💼", layout="centered")

st.title("Retirement Planner")

colA, colB = st.columns(2)
acct_type = colA.selectbox("Account type", ["401(k)", "Traditional IRA", "Roth IRA", "Taxable", "403(b)", "SEP IRA", "Solo 401(k)"])
age = colA.number_input("Current age", min_value=18, max_value=80, value=28, step=1)
retire_age = colA.number_input("Planned retirement age", min_value=age+1, max_value=90, value=65, step=1)
income = colA.number_input("Current annual income", min_value=0.0, value=90000.0, step=1000.0, format="%.2f")
pct_income_needed = colA.slider("Percent of income needed in retirement", min_value=30, max_value=120, value=80, step=1)

current_savings = colB.number_input("Current savings", min_value=0.0, value=50000.0, step=1000.0, format="%.2f")
monthly_contrib = colB.number_input("Monthly contribution", min_value=0.0, value=1000.0, step=100.0, format="%.2f")
exp_return = colB.number_input("Expected annual return (%)", min_value=0.0, max_value=20.0, value=7.0, step=0.1, format="%.1f")
inflation = colB.number_input("Expected annual inflation (%)", min_value=0.0, max_value=10.0, value=2.5, step=0.1, format="%.1f")

years_to_retire = retire_age - age
r = exp_return / 100.0
i = inflation / 100.0
rm = r / 12.0
n_months = years_to_retire * 12

if rm == 0:
    fv_contribs = monthly_contrib * n_months
    fv_savings = current_savings
else:
    fv_contribs = monthly_contrib * (((1 + rm) ** n_months - 1) / rm)
    fv_savings = current_savings * (1 + rm) ** n_months

balance_at_retirement = fv_savings + fv_contribs

spend_at_retirement = income * (pct_income_needed / 100.0) * ((1 + i) ** years_to_retire)

horizon_max_age = 110
years_post = max(0, horizon_max_age - retire_age)
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
    b = b * (1 + r) - s
    s = s * (1 + i)

df_growth_years = list(range(age, retire_age + 1))
if rm == 0:
    growth_balances = [current_savings + monthly_contrib * (12 * (yr - age)) for yr in df_growth_years]
else:
    growth_balances = []
    for yr in df_growth_years:
        m = (yr - age) * 12
        fv_c = monthly_contrib * (((1 + rm) ** m - 1) / rm) if m > 0 else 0
        fv_s = current_savings * (1 + rm) ** m
        growth_balances.append(fv_c + fv_s)

df_pre = pd.DataFrame({"Age": df_growth_years, "Balance": growth_balances})
df_post = pd.DataFrame({"Age": ages, "Balance": balances, "Spending": spends})

runout_age = None
if len(df_post) > 0 and df_post["Balance"].iloc[-1] <= 0:
    runout_age = int(df_post["Age"].iloc[-1])

c1, c2, c3 = st.columns(3)
c1.metric("Balance at retirement", f"${balance_at_retirement:,.0f}")
c2.metric("Initial annual spending", f"${spend_at_retirement:,.0f}")
c3.metric("Money runs out", "Does not run out" if runout_age is None else f"Age {runout_age}")

fig = go.Figure()
fig.add_trace(go.Scatter(x=df_pre["Age"], y=df_pre["Balance"], mode="lines", name="Pre-retirement"))
if len(df_post) > 0:
    fig.add_trace(go.Scatter(x=df_post["Age"], y=df_post["Balance"], mode="lines", name="Post-retirement"))
fig.update_layout(title="Portfolio balance over time", xaxis_title="Age", yaxis_title="Balance", hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Details")
st.dataframe(pd.concat([df_pre.assign(Phase="Accumulation"), df_post.assign(Phase="Decumulation")], ignore_index=True))

