import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
from supabase import create_client, Client
import os

# -----------------------------
# Streamlit Page Configuration
# -----------------------------
st.set_page_config(page_title="Bison Wealth 401(k) Growth Simulator",
                   page_icon="🦬",
                   layout="wide")

# -----------------------------
# Supabase Setup
# -----------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------
# Header + Branding
# -----------------------------
logo_path = "Bison_Wealth_Logo.png"
st.image(logo_path, width=180)

st.title("Bison Wealth 401(k) Growth Simulator")
st.write("Visualize how your 401(k) could grow **with and without Bison’s guidance.**")

# -----------------------------
# Helper: clean numeric input
# -----------------------------
def parse_number(x):
    try:
        return float(x.replace(",", "").strip())
    except:
        return None

# -----------------------------
# Calculation
# -----------------------------
def compute_projection(age, salary, balance):

    target_age = 65
    years = max(0, target_age - age)

    salary_growth_rate = 0.03
    contrib_rate = 0.078 + 0.046  # employee + employer

    non_help_rate = 0.0847
    help_rate = non_help_rate + 0.0332

    salaries = [salary * ((1 + salary_growth_rate) ** yr) for yr in range(years + 1)]
    annual_contribs = [s * contrib_rate for s in salaries]

    def monthly_growth(start, annual_contribs, annual_rate):
        total = start
        values = [start]
        monthly_rate = (1 + annual_rate) ** (1/12) - 1
        for yearly_contrib in annual_contribs:
            monthly_contrib = yearly_contrib / 12
            for _ in range(12):
                total = total * (1 + monthly_rate) + monthly_contrib
            values.append(total)
        return values

    baseline = monthly_growth(balance, annual_contribs, non_help_rate)
    help_vals = monthly_growth(balance, annual_contribs, help_rate)

    ages = list(range(age, target_age + 1))

    df = pd.DataFrame({
        "Age": ages,
        "Baseline": baseline,
        "With Help": help_vals
    })

    return df


# -----------------------------
# Input Section
# -----------------------------
col_left, col_right = st.columns([1, 2])

with col_left:

    st.subheader("Your Information")

    age = st.number_input("Your Age", min_value=18, max_value=100, value=42, step=1)
    salary_str = st.text_input("Current Annual Salary ($)", value="84000")
    balance_str = st.text_input("Current 401(k) Balance ($)", value="76500")
    company = st.text_input("Company Name", value="")

    salary = parse_number(salary_str)
    balance = parse_number(balance_str)

    calculate = st.button("Calculate", type="primary")


# -----------------------------
# Compute or Load Default
# -----------------------------
if salary and balance:
    df = compute_projection(age, salary, balance)
else:
    df = compute_projection(42, 84000, 76500)


# -----------------------------
# Plotly Chart
# -----------------------------
with col_right:

    st.subheader("Estimated 401(k) Growth")

    fig = go.Figure()

    # Baseline line
    fig.add_trace(go.Scatter(
        x=df["Age"], y=df["Baseline"],
        mode="lines",
        name="On Your Lonesome (8.5%)",
        line=dict(color="#7D7D7D", width=3),
        hovertemplate="Age %{x}<br>$%{y:,.0f}<extra></extra>"
    ))

    # Help line
    fig.add_trace(go.Scatter(
        x=df["Age"], y=df["With Help"],
        mode="lines",
        name="With Bison by Your Side (11.8%)",
        line=dict(color="#25385A", width=4),
        hovertemplate="Age %{x}<br>$%{y:,.0f}<extra></extra>"
    ))

    # Offset labels so they don't overlap
    offset_base = df["Baseline"].iloc[-1] * 0.04
    offset_help = df["With Help"].iloc[-1] * 0.04

    # End label: Baseline
    fig.add_annotation(
        x=df["Age"].iloc[-1] + 0.3,
        y=df["Baseline"].iloc[-1] + offset_base,
        text=f"${df['Baseline'].iloc[-1]:,.0f}",
        showarrow=False,
        font=dict(color="#7D7D7D", size=13)
    )

    # End label: With Help
    fig.add_annotation(
        x=df["Age"].iloc[-1] + 0.3,
        y=df["With Help"].iloc[-1] + offset_help,
        text=f"${df['With Help'].iloc[-1]:,.0f}",
        showarrow=False,
        font=dict(color="#25385A", size=16)
    )

    fig.update_layout(
        height=450,
        margin=dict(l=20, r=20, t=20, b=40),
        xaxis_title="Age",
        yaxis_title="Portfolio Value ($)",
        hovermode="x",
    )

    # Disable zoom + pan
    fig.update_layout(
        dragmode=False,
    )
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)

    st.plotly_chart(fig, use_container_width=True)


# -----------------------------
# CTA + Difference
# -----------------------------
final_diff = df["With Help"].iloc[-1] - df["Baseline"].iloc[-1]

st.markdown(
    f"""
    <div style="text-align:center; font-size:18px;">
        Is <b style="color:#25385A;">${final_diff:,.0f}</b> worth 30 minutes of your time?
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div style="text-align:center; margin-top:20px;">
        <a href="https://calendly.com/placeholder" target="_blank"
           style="background-color:#C17A49; color:white; padding:14px 28px;
                  text-decoration:none; border-radius:8px; font-size:18px;">
           Schedule a Conversation
        </a>
    </div>
    """,
    unsafe_allow_html=True
)


# -----------------------------
# Save to Supabase if Calculate Pressed
# -----------------------------
if calculate and salary and balance:

    supabase.table("submissions").insert({
        "age": age,
        "salary": salary,
        "balance": balance,
        "company": company if company.strip() else "Unknown",
        "created_at": datetime.utcnow().isoformat()
    }).execute()

    st.success("Saved to database!")


# -----------------------------
# Disclosure
# -----------------------------
st.caption("""
For illustrative purposes only. Assumes 3% annual salary growth and 12.4% annual contribution (7.8% employee, 4.6% employer).  
Performance without help is the 5yr annualized return of the S&P Target Date 2035 Index (as of 12/04/2025).  
With help is increased by 3.32% based on the Hewitt Study.
""")
