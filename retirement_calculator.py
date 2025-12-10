import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from supabase import create_client
import os

st.set_page_config(
    page_title="Bison Wealth | 401(k) Growth Simulator",
    page_icon="🦬",
    layout="wide"
)

# --------------------------
# Load Supabase credentials
# --------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --------------------------
# Style
# --------------------------
st.markdown("""
<style>
.block-container {
    max-width: 1400px;
    padding-left: 2rem;
    padding-right: 2rem;
}
button.css-1emrehy, button.st-emotion-cache-7ym5gk {
    background-color: #C17A49 !important;
    color: white !important;
    border-radius: 8px !important;
}
</style>
""", unsafe_allow_html=True)

# --------------------------
# Logo
# --------------------------
logo_path = "Bison Wealth Logo.png"
if os.path.exists(logo_path):
    st.image(logo_path, width=140)

st.title("Bison Wealth 401(k) Growth Simulator")
st.write("Visualize how your 401(k) could grow **with and without Bison’s guidance.**")

# --------------------------
# Helpers
# --------------------------
def parse_number(x):
    try:
        return float(x.replace(",", "").strip())
    except:
        return None

# --------------------------
# Layout
# --------------------------
left, right = st.columns([1, 2])

with left:
    st.subheader("Your Information")

    age = st.number_input("Your Age", min_value=18, max_value=120, value=42, step=1)
    salary_str = st.text_input("Current Annual Salary ($)", value="84,000")
    balance_str = st.text_input("Current 401(k) Balance ($)", value="76,500")
    company = st.text_input("Company Name", placeholder="Start typing...")

    calculate_button = st.button("Calculate")

salary = parse_number(salary_str)
balance = parse_number(balance_str)

# --------------------------
# Projection Logic
# --------------------------
def growth_projection_monthly(start_balance, annual_contribs, annual_rate):
    total = start_balance
    values = [start_balance]
    monthly_rate = (1 + annual_rate)**(1/12) - 1

    for yearly in annual_contribs:
        monthly_contrib = yearly / 12
        for _ in range(12):
            total = total * (1 + monthly_rate) + monthly_contrib
        values.append(total)

    return values

def compute_projection(age, salary, balance):
    target_age = 65
    years = max(0, target_age - age)

    salary_growth = 0.03
    employee_contrib = 0.078
    employer_contrib = 0.046

    rate_no_help = 0.0847
    rate_help = rate_no_help + 0.0332  # 11.79%

    salaries = [salary * ((1 + salary_growth)**yr) for yr in range(years + 1)]
    contribs = [s * (employee_contrib + employer_contrib) for s in salaries]

    baseline = growth_projection_monthly(balance, contribs, rate_no_help)
    help_growth = growth_projection_monthly(balance, contribs, rate_help)

    # FIX: ages must match the array lengths
    ages = list(range(age, age + len(baseline)))

    df = pd.DataFrame({
        "Age": ages,
        "Baseline": baseline,
        "With Help": help_growth
    })
    return df

# Compute default or triggered values
df = compute_projection(age, salary or 0, balance or 0)

# --------------------------
# Save to Supabase on click
# --------------------------
if calculate_button:
    supabase.table("submissions").insert({
        "age": age,
        "salary": salary,
        "balance": balance,
        "company": company if company.strip() else "Unknown"
    }).execute()

# --------------------------
# Plotly Chart (Clean, No Zoom, No Toolbar)
# --------------------------
with right:
    st.subheader("Estimated 401(k) Growth")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["Age"], y=df["Baseline"],
        mode="lines",
        name=f"On Your Lonesome (8.5%)",
        line=dict(color="#7D7D7D", width=3)
    ))

    fig.add_trace(go.Scatter(
        x=df["Age"], y=df["With Help"],
        mode="lines",
        name=f"With Bison by Your Side (11.8%)",
        line=dict(color="#25385A", width=5)
    ))

    # End labels
    # Amount to offset labels so they never overlap the line
    offset_baseline = (df["Baseline"].iloc[-1] * 0.04)   # 4% above line
    offset_help     = (df["With Help"].iloc[-1] * 0.04)
    
    fig.add_annotation(
        x=df["Age"].iloc[-1] + 0.2,   # push slightly right
        y=df["Baseline"].iloc[-1] + offset_baseline,
        text=f"${df['Baseline'].iloc[-1]:,.0f}",
        showarrow=False,
        font=dict(color="#7D7D7D", size=13)
    )
    
    fig.add_annotation(
        x=df["Age"].iloc[-1] + 0.2,
        y=df["With Help"].iloc[-1] + offset_help,
        text=f"${df['With Help"].iloc[-1]:,.0f}",
        showarrow=False,
        font=dict(color="#25385A", size=16)
    )

    fig.update_layout(
        height=420,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=30, r=20, t=40, b=40),
        xaxis=dict(
            title="Age",
            gridcolor="#E0E0E0",
            fixedrange=True
        ),
        yaxis=dict(
            title="Portfolio Value ($)",
            gridcolor="#E0E0E0",
            fixedrange=True
        ),
        showlegend=True,
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True, config={
        "displayModeBar": False,
        "scrollZoom": False
    })

# --------------------------
# CTA
# --------------------------
final_baseline = df["Baseline"].iloc[-1]
final_help = df["With Help"].iloc[-1]
difference = final_help - final_baseline

st.markdown(
    f"""
    <div style="text-align:center; margin-top:15px;">
        <p style="font-size:18px; color:#414546;">
            Is <span style="color:#25385A; font-weight:700;">${difference:,.0f}</span>
            worth 30 minutes of your time?
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div style="text-align:center;">
        <a href="https://calendly.com/placeholder-link" target="_blank"
           style="background-color:#C17A49; color:white; padding:12px 28px;
                  text-decoration:none; border-radius:8px; font-weight:600;">
           Schedule a Conversation
        </a>
    </div>
    """,
    unsafe_allow_html=True
)

# --------------------------
# Disclosure
# --------------------------
st.markdown("<br><br>", unsafe_allow_html=True)
st.caption("""
For illustrative purposes only. Assumes 3% annual salary growth and 12.4% annual contribution
(7.8% employee, 4.6% employer). Compounded monthly.

Performance without help is the 5yr annualized return of the S&P Target Date 2035 Index.
With help is increased by 3.32% based on the Hewitt Study.
""")
