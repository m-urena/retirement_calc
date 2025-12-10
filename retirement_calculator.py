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
# Logo (safe load)
# -----------------------------
logo_path = "Bison_Wealth_Logo.png"
if os.path.exists(logo_path):
    st.image(logo_path, width=150)


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
# Projection Calculation
# -----------------------------
def compute_projection(age, salary, balance):

    if salary is None:
        salary = 0
    if balance is None:
        balance = 0

    target_age = 65
    years = target_age - age
    num_points = years + 1

    salary_growth_rate = 0.03
    employee = 0.078
    employer = 0.046
    contrib_rate = employee + employer

    without_help = 0.0847
    with_help_rate = without_help + 0.0332

    salaries = [salary * ((1 + salary_growth_rate)**yr) for yr in range(num_points)]
    annual_contribs = [s * contrib_rate for s in salaries]

    def project(start, contribs, rate):
        total = start
        vals = [start]
        monthly_rate = (1 + rate)**(1/12) - 1

        for yearly in contribs:
            monthly_contrib = yearly / 12
            for _ in range(12):
                total = total * (1 + monthly_rate) + monthly_contrib
            vals.append(total)

        return vals[:num_points]

    baseline = project(balance, annual_contribs, without_help)
    helpvals = project(balance, annual_contribs, with_help_rate)

    ages = list(range(age, age + num_points))

    df = pd.DataFrame({
        "age": ages,
        "baseline": baseline,
        "with_help": helpvals
    })

    return df


# -----------------------------
# Inputs Section
# -----------------------------
col_left, col_right = st.columns([1, 2])

with col_left:

    st.subheader("Your Information")

    age = st.number_input("Your Age", min_value=18, max_value=100, value=42, step=1)
    salary_str = st.text_input("Current Annual Salary ($)", value="84,000")
    balance_str = st.text_input("Current 401(k) Balance ($)", value="76,500")
    company = st.text_input("Company Name", placeholder="Where do you work?")

    salary = parse_number(salary_str)
    balance = parse_number(balance_str)

    calculate = st.button("Calculate", type="primary")


# -----------------------------
# Evaluate Projection (always show)
# -----------------------------
df = compute_projection(age, salary, balance)


# -----------------------------
# Save to Supabase on Calculate
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
# Plotly Chart
# -----------------------------
with col_right:
    st.subheader("Estimated 401(k) Growth")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["age"], y=df["baseline"],
        mode="lines",
        name="On Your Lonesome (8.5%)",
        line=dict(color="#7D7D7D", width=3),
        hovertemplate="Age %{x}<br>$%{y:,.0f}<extra></extra>"
    ))

    fig.add_trace(go.Scatter(
        x=df["age"], y=df["with_help"],
        mode="lines",
        name="With Bison by Your Side (11.8%)",
        line=dict(color="#25385A", width=4),
        hovertemplate="Age %{x}<br>$%{y:,.0f}<extra></extra>"
    ))

    # End label offsets
    offset_base = df["baseline"].iloc[-1] * 0.04
    offset_help = df["with_help"].iloc[-1] * 0.04

    fig.add_annotation(
        x=df["age"].iloc[-1] + 0.3,
        y=df["baseline"].iloc[-1] + offset_base,
        text=f"${df['baseline'].iloc[-1]:,.0f}",
        showarrow=False,
        font=dict(color="#7D7D7D", size=14)
    )

    fig.add_annotation(
        x=df["age"].iloc[-1] + 0.3,
        y=df["with_help"].iloc[-1] + offset_help,
        text=f"${df['with_help'].iloc[-1]:,.0f}",
        showarrow=False,
        font=dict(color="#25385A", size=17)
    )

    fig.update_layout(
        height=450,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=20, r=20, t=20, b=40),
        xaxis=dict(title="Age", fixedrange=True, gridcolor="#E0E0E0"),
        yaxis=dict(title="Portfolio Value ($)", fixedrange=True, gridcolor="#E0E0E0"),
        hovermode="x unified"
    )

    fig.update_layout(dragmode=False)
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)

    st.plotly_chart(fig, use_container_width=True)


# -----------------------------
# CTA Section
# -----------------------------
final_diff = df["with_help"].iloc[-1] - df["baseline"].iloc[-1]

st.markdown(
    f"""
    <div style="text-align:center; font-size:18px; margin-top:15px;">
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
# Disclosure
# -----------------------------
st.markdown("<br><br>", unsafe_allow_html=True)
st.caption("""
For illustrative purposes only. Assumes 3% annual salary growth and 12.4% annual contribution (7.8% employee, 4.6% employer).
Performance without help is the 5-year annualized return of the S&P Target Date 2035 Index (as of 12/04/2025).
With help is increased by 3.32% based on the Hewitt Study.
""")
