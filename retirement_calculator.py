import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import base64
from supabase import create_client

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(page_title="Bison Wealth | 401(k) Growth Simulator", layout="wide")

# -------------------------------
# LOAD LOGO SAFELY (base64 so Streamlit Cloud never breaks)
# -------------------------------
def load_image_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

logo_b64 = load_image_base64("bison_logo.png")

# -------------------------------
# STYLE
# -------------------------------
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; }
    </style>
""", unsafe_allow_html=True)

# -------------------------------
# TOP RIGHT LOGO
# -------------------------------
st.markdown(
    f"""
    <div style="display:flex; justify-content:flex-end; margin-bottom:5px;">
        <img src="data:image/png;base64,{logo_b64}" style="width:160px;">
    </div>
    """,
    unsafe_allow_html=True
)

# -------------------------------
# TITLE
# -------------------------------
st.title("Bison Wealth 401(k) Growth Simulator")
st.write("Visualize how your 401(k) could grow **with and without Bison’s guidance.**")

# -------------------------------
# SUPABASE CLIENT
# -------------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------------
# COMPUTATION LOGIC
# -------------------------------
def compute_projection(age, salary, balance):
    target_age = 65
    years = max(0, target_age - age)

    salary_growth_rate = 0.03
    employee_contrib = 0.078
    employer_contrib = 0.046
    contribution_rate = employee_contrib + employer_contrib

    non_help_rate = 0.085
    help_rate = non_help_rate + 0.0332  # 11.82%

    salaries = [salary * ((1 + salary_growth_rate) ** yr) for yr in range(years + 1)]
    annual_contribs = [s * contribution_rate for s in salaries]

    def grow(start_balance, annual_contribs, annual_rate):
        total = start_balance
        values = []
        monthly_rate = (1 + annual_rate) ** (1 / 12) - 1
        for c in annual_contribs:
            for _ in range(12):
                total = total * (1 + monthly_rate) + (c / 12)
            values.append(total)
        return values

    baseline = grow(balance, annual_contribs, non_help_rate)
    with_help = grow(balance, annual_contribs, help_rate)

    ages = list(range(age + 1, target_age + 1))

    df = pd.DataFrame({
        "Age": ages,
        "Baseline": baseline,
        "Help": with_help
    })
    return df

# -------------------------------
# DEFAULT VALUES & INPUTS
# -------------------------------
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Your Information")

    age = st.number_input("Your Age", min_value=18, max_value=90, value=42)
    salary_str = st.text_input("Current Annual Salary ($)", value="84,000")
    balance_str = st.text_input("Current 401(k) Balance ($)", value="76,500")
    company = st.text_input("Company Name", placeholder="Where do you work?")

    def parse_num(x):
        try:
            return float(x.replace(",", "").strip())
        except:
            return 0

    salary = parse_num(salary_str)
    balance = parse_num(balance_str)

    calculate = st.button("Calculate", type="primary")

# -------------------------------
# RIGHT SIDE — GRAPH
# -------------------------------
with col2:
    st.subheader("Estimated 401(k) Growth")

    # Default graph before clicking calculate
    df_default = compute_projection(42, 84000, 76500)

    graph_df = df_default  # default unless calculate clicked

    if calculate:
        if age and salary and balance:
            graph_df = compute_projection(age, salary, balance)

            # Insert into database quietly
            supabase.table("submissions").insert({
                "age": age,
                "salary": salary,
                "balance": balance,
                "company": company if company else "Unknown"
            }).execute()

    # Build Plotly chart
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=graph_df["Age"],
        y=graph_df["Baseline"],
        mode="lines",
        name="On Your Lonesome (8.5%)",
        line=dict(color="#7D7D7D", width=3)
    ))

    fig.add_trace(go.Scatter(
        x=graph_df["Age"],
        y=graph_df["Help"],
        mode="lines",
        name="With Bison by Your Side (11.8%)",
        line=dict(color="#25385A", width=4)
    ))

    # Move end labels so they don't overlap
    fig.add_annotation(
        x=graph_df["Age"].iloc[-1] + 0.2,
        y=graph_df["Baseline"].iloc[-1],
        text=f"${graph_df['Baseline'].iloc[-1]:,.0f}",
        showarrow=False,
        font=dict(color="#7D7D7D", size=13)
    )

    fig.add_annotation(
        x=graph_df["Age"].iloc[-1] + 0.2,
        y=graph_df["Help"].iloc[-1],
        text=f"${graph_df['Help'].iloc[-1]:,.0f}",
        showarrow=False,
        font=dict(color="#25385A", size=15)
    )

    fig.update_layout(
        height=420,
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis_title="Age",
        yaxis_title="Portfolio Value ($)",
        hovermode="x",
    )

    # Disable zoom + pan
    fig.update_layout(
        xaxis=dict(fixedrange=True),
        yaxis=dict(fixedrange=True)
    )

    st.plotly_chart(fig, use_container_width=True)

# -------------------------------
# CTA SECTION
# -------------------------------
final_diff = graph_df["Help"].iloc[-1] - graph_df["Baseline"].iloc[-1]

st.markdown(
    f"""
    <div style="text-align:center; margin-top:20px; font-size:18px;">
        Is <b>${final_diff:,.0f}</b> worth 30 minutes of your time?
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div style="text-align:center; margin-top:10px;">
        <a href="https://calendly.com/placeholder-link" target="_blank"
           style="background-color:#C17A49; color:white; padding:12px 26px;
                  text-decoration:none; border-radius:8px; font-weight:600;">
           Schedule a Conversation
        </a>
    </div>
    """,
    unsafe_allow_html=True
)

# -------------------------------
# DISCLOSURE (small + faint)
# -------------------------------
st.caption("""
For illustrative purposes only. Assumes 3% annual salary growth and 12.4% annual contributions (7.8% employee, 4.6% employer).
Performance without help is the 5yr annualized return of the S&P Target Date 2035 Index (as of 12/04/2025). 
With help is increased by 3.32% based on the Hewitt Study.
""")
