import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from supabase import create_client
import datetime

# -----------------------------
# CONFIGURE PAGE
# -----------------------------
st.set_page_config(
    page_title="Bison Wealth 401(k) Growth Simulator",
    layout="wide"
)

# -----------------------------
# LOAD LOGO WITH POLISHED STYLING
# -----------------------------
st.markdown("""
    <style>
        .logo-box {
            padding-top: 25px;
            padding-bottom: 15px;
        }
    </style>
""", unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="logo-box">', unsafe_allow_html=True)
    st.image("bison_logo.png", width=165)
    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# SUPABASE SETUP
# -----------------------------
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

TABLE_NAME = "submissions"

# -----------------------------
# COMPUTATION FUNCTION
# -----------------------------
def compute_projection(age, salary, balance):
    years = list(range(age, 66))
    baseline_growth = []
    advisor_growth = []

    bal_base = balance
    bal_adv = balance

    for year in years:
        bal_base = bal_base * 1.085 + salary * 0.12
        bal_adv = bal_adv * 1.118 + salary * 0.12
        baseline_growth.append(bal_base)
        advisor_growth.append(bal_adv)

    return pd.DataFrame({
        "Age": years,
        "Baseline": baseline_growth,
        "Advisor": advisor_growth
    })

# -----------------------------
# DEFAULT VALUES
# -----------------------------
default_age = 42
default_salary = 84000
default_balance = 76500

df_default = compute_projection(default_age, default_salary, default_balance)

# -----------------------------
# PAGE TITLE
# -----------------------------
st.title("Bison Wealth 401(k) Growth Simulator")
st.write("Visualize how your 401(k) could grow with and without Bison’s guidance.")

# -----------------------------
# LAYOUT: INPUTS | GRAPH
# -----------------------------
col_left, col_right = st.columns([1, 2])

with col_left:
    st.subheader("Your Information")

    age = st.number_input("Your Age", min_value=18, max_value=65, value=default_age)
    salary = st.number_input("Current Annual Salary ($)", min_value=0, value=default_salary, step=1000, format="%d")
    balance = st.number_input("Current 401(k) Balance ($)", min_value=0, value=default_balance, step=1000, format="%d")

    company = st.text_input("Company Name", placeholder="Where do you work?")

    calculate = st.button("Calculate")

with col_right:
    st.subheader("Estimated 401(k) Growth")

    # The graph uses default values until Calculate is pressed
    df = df_default.copy()

    if calculate:
        df = compute_projection(age, salary, balance)

        # Store submission (clean — no IP, no UA)
        supabase.table(TABLE_NAME).insert({
            "age": age,
            "salary": salary,
            "balance": balance,
            "company": company if company else "Unknown",
            "created_at": datetime.datetime.utcnow().isoformat()
        }).execute()

    # -----------------------------
    # PLOTLY GRAPH (no zoom/pan)
    # -----------------------------
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["Age"], y=df["Baseline"],
        mode="lines+text",
        text=[f"${v:,.0f}" if i == len(df)-1 else "" for i, v in enumerate(df["Baseline"])],
        textposition="middle right",
        line=dict(color="#7f7f7f", width=3),
        name="On Your Lonesome (8.5%)"
    ))

    fig.add_trace(go.Scatter(
        x=df["Age"], y=df["Advisor"],
        mode="lines+text",
        text=[f"${v:,.0f}" if i == len(df)-1 else "" for i, v in enumerate(df["Advisor"])],
        textposition="middle right",
        line=dict(color="#25385a", width=4),
        name="With Bison by Your Side (11.8%)"
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
# SPACING BEFORE CTA
# -----------------------------
st.markdown("<div style='height:40px;'></div>", unsafe_allow_html=True)

# -----------------------------
# CTA SECTION
# -----------------------------
difference = df["Advisor"].iloc[-1] - df["Baseline"].iloc[-1]

st.markdown(
    f"<h4 style='text-align:center;'>Is <b>${difference:,.0f}</b> worth 30 minutes of your time?</h4>",
    unsafe_allow_html=True
)

st.markdown("""
<div style="text-align:center; padding-top:10px; padding-bottom:35px;">
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

# -----------------------------
# FOOTER SPACING
# -----------------------------
st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)
