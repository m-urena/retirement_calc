import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from supabase import create_client, Client
import os
from pathlib import Path
import base64

# --------------------------------------------------
# Streamlit Page Config
# --------------------------------------------------
st.set_page_config(
    page_title="Bison Wealth 401(k) Growth Simulator",
    page_icon="🦬",
    layout="wide"
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Montserrat', sans-serif;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------
# Supabase Setup
# --------------------------------------------------
def get_secret(key):
    try:
        return st.secrets[key]
    except Exception:
        return None


def create_supabase_client():
    url = get_secret("SUPABASE_URL")
    key = get_secret("SUPABASE_KEY")

    if not url or not key:
        return None

    try:
        return create_client(url, key)
    except Exception:
        return None


supabase: Client | None = create_supabase_client()

# --------------------------------------------------
# Load Company Names
# --------------------------------------------------
@st.cache_data(show_spinner=False)
def load_company_names():
    data_path = Path(__file__).resolve().parent / "Data.csv"

    if not data_path.exists():
        return []

    df = pd.read_csv(data_path)
    df.columns = df.columns.str.strip()

    if "Company Name" not in df.columns:
        return []

    names = (
        df["Company Name"]
        .dropna()
        .astype(str)
        .str.strip()
        .loc[lambda s: s != ""]
        .str.title()
    )

    return sorted(set(names))

# --------------------------------------------------
# Logo
# --------------------------------------------------
logo_path = Path(__file__).resolve().parent / "bison_logo.png"
with open(logo_path, "rb") as f:
    logo_b64 = base64.b64encode(f.read()).decode()

st.markdown(
    f"""
    <div style="position:absolute; top:70px; right:40px; z-index:999;">
        <img src="data:image/png;base64,{logo_b64}" width="150">
    </div>
    """,
    unsafe_allow_html=True
)

st.title("Bison Wealth 401(k) Growth Simulator")
st.write("Visualize how your 401(k) could grow **with and without Bison’s guidance.**")

# --------------------------------------------------
# Helpers
# --------------------------------------------------
def parse_number(x):
    try:
        return float(x.replace(",", "").strip())
    except Exception:
        return None

# --------------------------------------------------
# Projection Logic
# --------------------------------------------------
@st.cache_data(show_spinner=False)
def compute_projection(age, salary, balance):
    target_age = 65

    if age >= target_age or salary <= 0:
        return pd.DataFrame({
            "age": [age],
            "baseline": [balance],
            "with_help": [balance]
        })

    years = target_age - age
    num_points = years + 1

    salary_growth_rate = 0.03
    contribution_rate = 0.078 + 0.046

    r_no_help = 0.0847
    r_help = r_no_help + 0.0332

    salaries = [salary * ((1 + salary_growth_rate) ** yr) for yr in range(num_points)]
    annual_contribs = [s * contribution_rate for s in salaries]

    def project(start, contribs, rate):
        total = start
        out = [start]
        monthly_rate = (1 + rate) ** (1 / 12)
        monthly_factor = monthly_rate ** 12
        contrib_multiplier = (monthly_factor - 1) / (monthly_rate - 1)

        for yearly in contribs:
            monthly_contrib = yearly / 12
            total = total * monthly_factor + monthly_contrib * contrib_multiplier
            out.append(total)

        return out[:num_points]

    return pd.DataFrame({
        "age": list(range(age, age + num_points)),
        "baseline": project(balance, annual_contribs, r_no_help),
        "with_help": project(balance, annual_contribs, r_help)
    })

# --------------------------------------------------
# Session Defaults
# --------------------------------------------------
if "age_used" not in st.session_state:
    st.session_state.age_used = 42
if "salary_used" not in st.session_state:
    st.session_state.salary_used = 84000
if "balance_used" not in st.session_state:
    st.session_state.balance_used = 76500

# --------------------------------------------------
# Inputs
# --------------------------------------------------
left, right = st.columns([1, 2])

with left:
    st.subheader("Your Information")

    age_input = st.number_input("Your Age", 18, 100, 42)
    salary_str = st.text_input("Current Annual Salary ($)", "84,000")
    balance_str = st.text_input("Current 401(k) Balance ($)", "76,500")

    salary_input = parse_number(salary_str)
    balance_input = parse_number(balance_str)

    company_list = load_company_names()

    company_input = st.selectbox(
        "Company Name",
        options=company_list,
        index=None,
        placeholder="Type your company's name",
        accept_new_options=True
    )

    company = None
    raw_company_input = company_input.strip() if company_input else ""

    if raw_company_input and len(raw_company_input) >= 3:
        normalized = raw_company_input.title()
        if normalized in company_list:
            company = normalized
        else:
            company = "My Company Is Not Listed"

    st.markdown(
        """
        <style>
        div.stButton > button:first-child {
            background-color: #C17A49 !important;
            color: white !important;
            border-radius: 6px !important;
            height: 40px !important;
            padding: 0 20px !important;
            border: none !important;
            font-family: 'Montserrat', sans-serif !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    calculate = st.button("Calculate", type="primary")

# --------------------------------------------------
# Handle Calculate
# --------------------------------------------------
if (
    calculate
    and salary_input
    and balance_input
    and age_input < 65
    and company
):
    st.session_state.age_used = age_input
    st.session_state.salary_used = salary_input
    st.session_state.balance_used = balance_input

    if supabase:
        try:
            supabase.table("submissions").insert({
                "age": age_input,
                "salary": salary_input,
                "balance": balance_input,
                "company": company,
                "raw_company_input": raw_company_input,
                "created_at": datetime.utcnow().isoformat()
            }).execute()
        except Exception:
            pass

# --------------------------------------------------
# Compute Projection
# --------------------------------------------------
df = compute_projection(
    st.session_state.age_used,
    st.session_state.salary_used,
    st.session_state.balance_used
)

# --------------------------------------------------
# Chart
# --------------------------------------------------
with right:
    st.subheader("Estimated 401(k) Growth")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["age"],
        y=df["baseline"],
        mode="lines",
        name="On Your Lonesome (8.5%)",
        line=dict(color="#7D7D7D", width=3)
    ))

    fig.add_trace(go.Scatter(
        x=df["age"],
        y=df["with_help"],
        mode="lines",
        name="With Bison by Your Side (11.8%)",
        line=dict(color="#25385A", width=4)
    ))

    final_age = df["age"].iloc[-1]
    baseline_final = df["baseline"].iloc[-1]
    with_help_final = df["with_help"].iloc[-1]

    fig.add_trace(go.Scatter(
        x=[final_age],
        y=[baseline_final],
        mode="markers+text",
        text=[f"${baseline_final:,.0f}"],
        textposition="bottom right",
        textfont=dict(color="#7D7D7D", size=12),
        marker=dict(color="#7D7D7D", size=10),
        showlegend=False,
        hoverinfo="text",
        name="On Your Lonesome Final"
    ))

    fig.add_trace(go.Scatter(
        x=[final_age],
        y=[with_help_final],
        mode="markers+text",
        text=[f"${with_help_final:,.0f}"],
        textposition="top left",
        textfont=dict(color="#25385A", size=12, family="Montserrat"),
        marker=dict(color="#25385A", size=10),
        showlegend=False,
        hoverinfo="text",
        name="With Bison by Your Side Final"
    ))

    fig.update_layout(
        height=450,
        margin=dict(l=20, r=20, t=20, b=40),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Montserrat"),
        xaxis=dict(title="Age", fixedrange=True),
        yaxis=dict(title="Portfolio Value ($)", fixedrange=True),
        hovermode="x unified",
        dragmode=False
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "scrollZoom": False,
            "doubleClick": False,
            "displayModeBar": False
        }
    )

# --------------------------------------------------
# CTA + Calendly Button
# --------------------------------------------------
final_diff = df["with_help"].iloc[-1] - df["baseline"].iloc[-1]

st.markdown(
    f"""
    <div style="text-align:center; font-size:26px; margin-top:20px;">
        Is <span style="font-weight:700; color:#25385A;">
        ${final_diff:,.0f}</span> worth 30 minutes of your time?
    </div>
    """,
    unsafe_allow_html=True
)

DEFAULT_CALENDLY = "https://calendly.com/placeholder"
ALT_CALENDLY = "https://calendly.com/placeholder-not-listed"

normalized_company = company.lower() if company else ""
calendly_link = (
    ALT_CALENDLY
    if normalized_company == "my company is not listed"
    else DEFAULT_CALENDLY
)

st.markdown(
    f"""
    <div style="text-align:center; margin-top:20px;">
        <a href="{calendly_link}" target="_blank"
           style="
               background-color:#C17A49;
               color:white;
               padding:14px 28px;
               text-decoration:none;
               border-radius:8px;
               font-size:18px;
               font-family:Montserrat, sans-serif;
           ">
           Schedule a Conversation
        </a>
    </div>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------
# Disclosure
# --------------------------------------------------
st.space("large")
st.caption(
    "For illustrative purposes only. Assumes 3% annual salary growth and 12.4% annual contribution "
    "(7.8% employee, 4.6% employer). Performance without help is the 5-year annualized return of the "
    "S&P Target Date 2035 Index. With help is increased by 3.32% based on the Hewitt Study."
)
