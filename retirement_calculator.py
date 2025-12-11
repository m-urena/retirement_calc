import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from supabase import create_client
import datetime

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="Bison Wealth 401(k) Growth Simulator",
    layout="wide"
)

# Make the main content area nicely centered and not ultra-wide
st.markdown(
    """
    <style>
    .block-container {
        max-width: 1300px;
        padding-left: 3rem;
        padding-right: 3rem;
        margin: auto;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# CONSTANTS FOR RETURNS
# -----------------------------
NON_HELP_RATE = 0.0847           # 8.47% annualized
HELP_RATE = NON_HELP_RATE + 0.0332   # +3.32%

# -----------------------------
# SUPABASE CLIENT
# -----------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
TABLE_NAME = "submissions"

# -----------------------------
# LOGO + TOP SPACING
# -----------------------------
st.markdown(
    """
    <style>
    .logo-box {
        padding-top: 25px;
        padding-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

with st.container():
    st.markdown('<div class="logo-box">', unsafe_allow_html=True)
    st.image("bison_logo.png", width=165)
    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# CORE PROJECTION FUNCTION
# -----------------------------
def compute_projection(age: int, salary: float, balance: float) -> pd.DataFrame:
    target_age = 65
    years = max(0, target_age - age)

    salary_growth_rate = 0.03
    employee_contrib = 0.078
    employer_contrib = 0.046
    contribution_rate = employee_contrib + employer_contrib

    # Salary path
    salaries = [salary * ((1 + salary_growth_rate) ** yr) for yr in range(years + 1)]
    annual_contribs = [s * contribution_rate for s in salaries]

    def growth_projection_monthly(start_balance, annual_contribs, annual_rate):
        total = start_balance
        values = [start_balance]
        monthly_rate = (1 + annual_rate) ** (1 / 12) - 1
        for yearly_contrib in annual_contribs:
            monthly_contrib = yearly_contrib / 12
            for _ in range(12):
                total = total * (1 + monthly_rate) + monthly_contrib
            values.append(total)
        return values

    baseline = growth_projection_monthly(balance, annual_contribs, NON_HELP_RATE)
    advisor = growth_projection_monthly(balance, annual_contribs, HELP_RATE)

    ages = list(range(age, target_age + 1))
    df = pd.DataFrame({
        "Age": ages,
        "Baseline": baseline,
        "Advisor": advisor
    })
    return df

# -----------------------------
# DEFAULT INPUTS & DEFAULT CURVE
# -----------------------------
default_age = 42
default_salary = 84_000
default_balance = 76_500

df_default = compute_projection(default_age, default_salary, default_balance)

# -----------------------------
# TITLE & INTRO
# -----------------------------
st.title("Bison Wealth 401(k) Growth Simulator")
st.write("Visualize how your 401(k) could grow with and without Bison’s guidance.")

# -----------------------------
# LAYOUT: LEFT (INPUTS) | RIGHT (CHART)
# -----------------------------
col_left, col_right = st.columns([1, 2])

with col_left:
    st.subheader("Your Information")

    age = st.number_input("Your Age", min_value=18, max_value=65, value=default_age)
    salary = st.number_input(
        "Current Annual Salary ($)", min_value=0, value=default_salary,
        step=1000, format="%d"
    )
    balance = st.number_input(
        "Current 401(k) Balance ($)", min_value=0, value=default_balance,
        step=1000, format="%d"
    )

    company = st.text_input("Company Name", placeholder="Where do you work?")

    calculate = st.button("Calculate")

with col_right:
    st.subheader("Estimated 401(k) Growth")

    # Use default curve until the user clicks Calculate
    df = df_default.copy()

    if calculate:
        df = compute_projection(age, salary, balance)

        # Quietly store the inputs to Supabase (no extra user messaging)
        supabase.table(TABLE_NAME).insert({
            "age": age,
            "salary": salary,
            "balance": balance,
            "company": company if company else "Unknown",
            "created_at": datetime.datetime.utcnow().isoformat()
        }).execute()

    # -----------------------------
    # PLOTLY CHART (hover only, no zoom/pan)
    # -----------------------------
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["Age"],
        y=df["Baseline"],
        mode="lines+text",
        line=dict(color="#7D7D7D", width=3),
        name=f"On Your Lonesome ({NON_HELP_RATE*100:.1f}%)",
        text=[f"${v:,.0f}" if i == len(df) - 1 else "" for i, v in enumerate(df["Baseline"])],
        textposition="middle right"
    ))

    fig.add_trace(go.Scatter(
        x=df["Age"],
        y=df["Advisor"],
        mode="lines+text",
        line=dict(color="#25385A", width=4),
        name=f"With Bison by Your Side ({HELP_RATE*100:.1f}%)",
        text=[f"${v:,.0f}" if i == len(df) - 1 else "" for i, v in enumerate(df["Advisor"])],
        textposition="middle right"
    ))

    fig.update_layout(
        height=450,
        margin=dict(l=40, r=40, t=10, b=40),
        hovermode="x unified",
        xaxis=dict(title="Age", fixedrange=True),
        yaxis=dict(title="Portfolio Value ($)", fixedrange=True),
        showlegend=True
    )

    st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# CTA (DIFFERENCE + BUTTON)
# -----------------------------
difference = df["Advisor"].iloc[-1] - df["Baseline"].iloc[-1]

# Some space between chart and text
st.markdown("<div style='height:25px;'></div>", unsafe_allow_html=True)

st.markdown(
    f"<h4 style='text-align:center;'>Is <b>${difference:,.0f}</b> worth 30 minutes of your time?</h4>",
    unsafe_allow_html=True
)

st.markdown("""
<div style="text-align:center; padding-top:10px; padding-bottom:25px;">
    <a href="https://calendly.com/bisonwealth" target="_blank">
        <button style="
            background-color:#C17A49;
            color:white;
            padding:14px 32px;
            border:none;
            border-radius:8px;
            font-size:17px;
            cursor:pointer;">
            Schedule a Conversation
        </button>
    </a>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# -----------------------------
# DISCLOSURE (BACK WHERE IT WAS)
# -----------------------------
st.caption("""
For illustrative purposes only. Assumes 3% annual salary growth and 12.4% of salary contributed annually
(7.8% employee, 4.6% employer). Compounded monthly.

Performance without help is the 5yr annualized return of the S&P Target Date 2035 Index as of 12/04/2025.  
With help is increased by 3.32% based on the Hewitt Study.
""")
