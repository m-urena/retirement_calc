import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from supabase import create_client
import os

# ==========================================================
# PAGE SETUP
# ==========================================================
st.set_page_config(page_title="Bison 401(k) Simulator", layout="wide")

# CSS setup to force the logo to the right, fix spacing, and change the primary button color
st.markdown("""
<style>
/* 1. Container to push the logo to the far right */
.logo-container-right {
    display: flex;
    justify-content: flex-end;
    width: 100%;
    margin-bottom: -40px; /* Adjust spacing above the title */
}

/* 2. Change the 'primary' button (Calculate) color to match the Schedule button (#C17A49) */
/* This overrides Streamlit's primary color variable for the theme */
:root {
    --primary-color: #C17A49;
}
</style>
""", unsafe_allow_html=True)


# The logo display now uses the right-alignment container
st.markdown('<div class="logo-container-right">', unsafe_allow_html=True)
st.image("bison_logo.png", width=160)
st.markdown("</div>", unsafe_allow_html=True)

st.title("Bison Wealth 401(k) Growth Simulator")
st.write("Visualize how your 401(k) could grow **with and without Bison’s guidance.**")

# ==========================================================
# SUPABASE INIT
# ==========================================================
# NOTE: The secrets keys are placeholders/assumed to be available in the execution environment
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "placeholder_url")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "placeholder_key")

# Mock Supabase client if secrets are not available, to allow execution
class MockSupabaseClient:
    def table(self, table_name):
        return self

    def insert(self, data):
        return self

    def execute(self):
        return None

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception:
    supabase = MockSupabaseClient()


# ==========================================================
# FINAL, NEVER-TOUCH-AGAIN PROJECTION ENGINE
# ==========================================================
DEFAULT_AGE = 42
DEFAULT_SALARY = 84000
DEFAULT_BALANCE = 76500

def compute_projection(age, salary, balance):

    # Sanitize inputs fully
    try:
        age = int(age)
    except:
        age = DEFAULT_AGE

    try:
        salary = float(salary)
    except:
        salary = DEFAULT_SALARY

    try:
        balance = float(balance)
    except:
        balance = DEFAULT_BALANCE

    # Guardrails
    if age < 18 or age > 90:
        age = DEFAULT_AGE
    if salary <= 0:
        salary = DEFAULT_SALARY
    if balance < 0:
        balance = DEFAULT_BALANCE

    # Constants
    target_age = 65
    years = max(1, target_age - age)

    salary_growth_rate = 0.03
    contrib_rate = 0.078 + 0.046
    base_rate = 0.085
    help_rate = base_rate + 0.0332

    # Salary and contributions
    salaries = [salary * ((1 + salary_growth_rate)**yr) for yr in range(years)]
    contribs = [s * contrib_rate for s in salaries]

    # Growth calculation (monthly)
    def grow(start, contributions, annual_rate):
        total = start
        results = []
        m_rate = (1 + annual_rate)**(1/12) - 1
        for c in contributions:
            for _ in range(12):
                total = total * (1 + m_rate) + c/12
            results.append(total)
        return results

    baseline = grow(balance, contribs, base_rate)
    help_vals = grow(balance, contribs, help_rate)

    # Age list
    ages = list(range(age+1, age+1+len(baseline)))

    # FINAL PROTECTION — truncate to uniform length
    L = min(len(ages), len(baseline), len(help_vals))
    ages = ages[:L]
    baseline = baseline[:L]
    help_vals = help_vals[:L]

    return pd.DataFrame({
        "Age": ages,
        "Baseline": baseline,
        "Help": help_vals
    })

# Default graph on load
df_default = compute_projection(DEFAULT_AGE, DEFAULT_SALARY, DEFAULT_BALANCE)

# ==========================================================
# USER INPUTS
# ==========================================================
left, right = st.columns([1,2])

with left:
    st.subheader("Your Information")
    age = st.number_input("Your Age", value=DEFAULT_AGE, min_value=18, max_value=90)

    salary_str = st.text_input("Current Annual Salary ($)", value=f"{DEFAULT_SALARY:,}")
    balance_str = st.text_input("Current 401(k) Balance ($)", value=f"{DEFAULT_BALANCE:,}")

    company = st.text_input("Company Name", placeholder="Where do you work?")
    
    # This button will now be colored #C17A49 due to the :root CSS variable override
    calculate = st.button("Calculate", type="primary")

# Convert numbers
def parse_money(x):
    try:
        return float(x.replace(",", "").strip())
    except:
        return None

salary = parse_money(salary_str)
balance = parse_money(balance_str)

# ==========================================================
# DETERMINE WHICH DATASET TO SHOW
# ==========================================================
if calculate and salary and balance:
    df = compute_projection(age, salary, balance)

    # Store in Supabase
    try:
        supabase.table("submissions").insert({
            "age": age,
            "salary": salary,
            "balance": balance,
            "company": company if company else "Unknown"
        }).execute()
    except Exception as e:
        # Log error but don't stop app
        pass


else:
    df = df_default


# ==========================================================
# GRAPH (PLOTLY)
# ==========================================================
with right:
    st.subheader("Estimated 401(k) Growth")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["Age"], y=df["Baseline"],
        mode="lines",
        name="On Your Lonesome (8.5%)",
        line=dict(color="#7D7D7D", width=3),
        hovertemplate="Age %{x}<br>$%{y:,.0f}<extra></extra>"
    ))

    fig.add_trace(go.Scatter(
        x=df["Age"], y=df["Help"],
        mode="lines",
        name="With Bison by Your Side (11.8%)",
        line=dict(color="#25385A", width=4),
        hovertemplate="Age %{x}<br>$%{y:,.0f}<extra></extra>"
    ))

    # End labels moved above line
    fig.add_annotation(x=df["Age"].iloc[-1], y=df["Baseline"].iloc[-1] + 20000,
                       text=f"${df['Baseline'].iloc[-1]:,.0f}",
                       showarrow=False, font=dict(color="#7D7D7D"))

    fig.add_annotation(x=df["Age"].iloc[-1], y=df["Help"].iloc[-1] + 20000,
                       text=f"${df['Help'].iloc[-1]:,.0f}",
                       showarrow=False, font=dict(color="#25385A"))

    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="x unified",
        xaxis=dict(title="Age", showgrid=False),
        yaxis=dict(title="Portfolio Value ($)", gridcolor="#E0E0E0"),
        dragmode=False   # disables zoom & pan
    )

    st.plotly_chart(fig, use_container_width=True)
st.markdown("<div style='height:40px;'></div>", unsafe_allow_html=True)

# ==========================================================
# CTA
# ==========================================================
final_difference = df["Help"].iloc[-1] - df["Baseline"].iloc[-1]

st.markdown(f"""
<div style='text-align:center; font-size:18px; margin-top:20px;'>
Is <span style='color:#25385A; font-weight:700;'>${final_difference:,.0f}</span> worth 30 minutes of your time?
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style='text-align:center;'>
    <a href="https://calendly.com/placeholder-link" target="_blank"
       style="background-color:#C17A49; color:white; padding:12px 28px;
              text-decoration:none; border-radius:8px; font-weight:600;">
       Schedule a Conversation
    </a>
</div>
""", unsafe_allow_html=True)


# ==========================================================
# DISCLOSURE
# ==========================================================
st.caption("""
For illustrative purposes only. Assumes 3% annual salary growth and 12.4% annual contributions (7.8% employee, 4.6% employer).  
Performance without help is the 5yr annualized return of the S&P Target Date 2035 Index (as of 12/04/2025).  
With help is increased by 3.32% based on the Hewitt Study.
""")
