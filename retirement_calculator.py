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

    html, body, [class*="css"]  {
        font-family: 'Montserrat', sans-serif;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# Supabase Setup
# --------------------------------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# --------------------------------------------------
# Company data setup
# --------------------------------------------------
DATA_DIR = Path(__file__).resolve().parent / "Data"
COMPANY_FILE_PREFIX = "AL - ID Skip GA"


@st.cache_data(show_spinner=False)
def load_company_names():
    fallback = ["My Company Is Not Listed"]
    matches = sorted(DATA_DIR.glob(f"{COMPANY_FILE_PREFIX}*"))
    if not matches:
        return fallback

    data_path = matches[0]

    try:
        if data_path.suffix.lower() == ".csv":
            df = pd.read_csv(data_path)
        else:
            df = pd.read_excel(data_path)
    except Exception:
        return fallback

    col_name = "Plan sponsor's name"
    if col_name not in df.columns:
        return fallback

    names = (
        df[col_name]
        .dropna()
        .astype(str)
        .map(lambda x: x.strip())
        .loc[lambda s: s != ""]
        .map(lambda x: x.title())
    )

    unique_sorted = sorted(set(names))
    return fallback + unique_sorted


# --------------------------------------------------
# Logo
# --------------------------------------------------
logo_path = os.path.join(os.path.dirname(__file__), "bison_logo.png")
with open(logo_path, "rb") as logo_file:
    logo_b64 = base64.b64encode(logo_file.read()).decode()

st.markdown(
    f"""
    <div style="
        position: absolute;
        top: 70px;
        right: 40px;
        z-index: 999;
    ">
        <img src="data:image/png;base64,{logo_b64}" width="150">
    </div>
    """,
    unsafe_allow_html=True
)

st.title("Bison Wealth 401(k) Growth Simulator")
st.write("Visualize how your 401(k) could grow **with and without Bison’s guidance.**")


# --------------------------------------------------
# Helper: parse numbers with commas
# --------------------------------------------------
def parse_number(x):
    try:
        return float(x.replace(",", "").strip())
    except (TypeError, ValueError):
        return None


# --------------------------------------------------
# Projection Calculation Function
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

    baseline = project(balance, annual_contribs, r_no_help)
    helpvals = project(balance, annual_contribs, r_help)
    ages = list(range(age, age + num_points))

    return pd.DataFrame({
        "age": ages,
        "baseline": baseline,
        "with_help": helpvals
    })


# --------------------------------------------------
# Initialize session_state
# --------------------------------------------------
if "age_used" not in st.session_state:
    st.session_state.age_used = 42
if "salary_used" not in st.session_state:
    st.session_state.salary_used = 84000
if "balance_used" not in st.session_state:
    st.session_state.balance_used = 76500


# --------------------------------------------------
# Inputs Section
# --------------------------------------------------
left, right = st.columns([1, 2])

with left:
    st.subheader("Your Information")

    company_options = load_company_names()

    age_input = st.number_input("Your Age", min_value=18, max_value=100, value=42)
    salary_str = st.text_input("Current Annual Salary ($)", value="84,000")
    balance_str = st.text_input("Current 401(k) Balance ($)", value="76,500")

    company = st.selectbox(
        "Company Name",
        company_options,
        index=0,
        placeholder="Start typing to search your company",
    )

    salary_input = parse_number(salary_str)
    balance_input = parse_number(balance_str)

    st.markdown(
        """
        <style>
        div.stButton > button:first-child {
            background-color: #C17A49 !important;
            color: white !important;
            border-radius: 6px !important;
            height: 40px !important;
            padding-left: 20px !important;
            padding-right: 20px !important;
            border: none !important;
            font-family: 'Montserrat', sans-serif !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    calculate = st.button("Calculate", type="primary")


# --------------------------------------------------
# When user clicks Calculate
# --------------------------------------------------
if calculate and salary_input and balance_input and age_input < 65:
    st.session_state.age_used = age_input
    st.session_state.salary_used = salary_input
    st.session_state.balance_used = balance_input

    supabase.table("submissions").insert({
        "age": age_input,
        "salary": salary_input,
        "balance": balance_input,
        "company": company.strip() if company.strip() else "Unknown",
        "created_at": datetime.utcnow().isoformat()
    }).execute()


# --------------------------------------------------
# Compute Projection
# --------------------------------------------------
df = compute_projection(
    st.session_state.age_used,
    st.session_state.salary_used,
    st.session_state.balance_used
)


# --------------------------------------------------
# Graph Section
# --------------------------------------------------
with right:
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
        margin=dict(l=20, r=20, t=20, b=40),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Montserrat, sans-serif"),
        xaxis=dict(title="Age", fixedrange=True, gridcolor="#E0E0E0"),
        yaxis=dict(title="Portfolio Value ($)", fixedrange=True, gridcolor="#E0E0E0"),
        hovermode="x unified",
        dragmode=False
    )

    st.plotly_chart(fig, use_container_width=True)


# --------------------------------------------------
# CTA Section
# --------------------------------------------------
final_diff = df["with_help"].iloc[-1] - df["baseline"].iloc[-1]

st.markdown(
    f"""
    <div style="text-align:center; font-size:26px; margin-top:20px;">
        Is <span style="font-weight:700; color:#25385A;">${final_diff:,.0f}</span> worth 30 minutes of your time?
    </div>
    """,
    unsafe_allow_html=True
)

DEFAULT_CALENDLY = "https://calendly.com/placeholder"
ALT_CALENDLY = "https://calendly.com/placeholder-not-listed"

normalized_company = company.strip().lower()
calendly_link = ALT_CALENDLY if normalized_company == "my company is not listed" else DEFAULT_CALENDLY

st.markdown(
    f"""
    <div style="text-align:center; margin-top:20px;">
        <a href="{calendly_link}" target="_blank"
           style="background-color:#C17A49; color:white; padding:14px 28px;
                  text-decoration:none; border-radius:8px; font-size:18px;">
           Schedule a Conversation
        </a>
    </div>
    """,
    unsafe_allow_html=True
)


# --------------------------------------------------
# Disclosure
# --------------------------------------------------
st.markdown("<br><br>", unsafe_allow_html=True)
st.caption("""
For illustrative purposes only. Assumes 3% annual salary growth and 12.4% annual contribution (7.8% employee, 4.6% employer).
Performance without help is the 5-year annualized return of the S&P Target Date 2035 Index.
With help is increased by 3.32% based on the Hewitt Study.
""")
