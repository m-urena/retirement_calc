import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from supabase import create_client, Client
from pathlib import Path
import base64

# ==================================================
# Page config (iframe-friendly)
# ==================================================
st.set_page_config(
    page_title="401(k) Growth Simulator",
    page_icon="🦬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ==================================================
# Hide Streamlit chrome (iframe widget mode)
# ==================================================
st.markdown(
    """
    <style>
    header { visibility: hidden; height: 0px; }
    footer { visibility: hidden; height: 0px; }
    #MainMenu { visibility: hidden; }

    /* Prevent iframe scroll jitter */
    html, body {
        overflow-x: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==================================================
# Dark mode detection
# ==================================================
is_dark_mode = st.get_option("theme.base") == "dark"

if is_dark_mode:
    plot_bg = "#0B0F14"
    paper_bg = "#0B0F14"
    grid_color = "rgba(255,255,255,0.08)"
    axis_color = "#E5E7EB"
    baseline_color = "#FFFFFF"
    help_color = "#C17A49"
else:
    plot_bg = "white"
    paper_bg = "white"
    grid_color = "#E0E0E0"
    axis_color = "#000000"
    baseline_color = "#7D7D7D"
    help_color = "#25385A"

# ==================================================
# Global font
# ==================================================
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

# ==================================================
# Supabase (safe / optional)
# ==================================================
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

# ==================================================
# Load companies
# ==================================================
@st.cache_data(show_spinner=False)
def load_company_names():
    data_path = Path(__file__).resolve().parent / "Data.csv"
    if not data_path.exists():
        return []

    df = pd.read_csv(data_path)
    df.columns = df.columns.str.strip()

    if "Company Name" not in df.columns:
        return []

    return sorted(
        set(
            df["Company Name"]
            .dropna()
            .astype(str)
            .str.strip()
            .loc[lambda s: s != ""]
            .str.title()
        )
    )

# ==================================================
# Helpers
# ==================================================
def parse_number(x):
    try:
        return float(x.replace(",", "").strip())
    except Exception:
        return None

# ==================================================
# Projection logic
# ==================================================
@st.cache_data(show_spinner=False)
def compute_projection(age, salary, balance):
    target_age = 65

    if age >= target_age or salary <= 0:
        return pd.DataFrame({
            "age": [age],
            "baseline": [balance],
            "with_help": [balance],
        })

    years = target_age - age
    salary_growth = 0.03
    contrib_rate = 0.078 + 0.046
    r_base = 0.0847
    r_help = r_base + 0.0332

    salaries = [salary * ((1 + salary_growth) ** i) for i in range(years + 1)]
    contribs = [s * contrib_rate for s in salaries]

    def project(start, contribs, r):
        total = start
        out = [start]
        monthly_r = (1 + r) ** (1 / 12)
        annual_factor = monthly_r ** 12
        contrib_mult = (annual_factor - 1) / (monthly_r - 1)

        for c in contribs:
            total = total * annual_factor + (c / 12) * contrib_mult
            out.append(total)

        return out[: years + 1]

    return pd.DataFrame({
        "age": list(range(age, age + years + 1)),
        "baseline": project(balance, contribs, r_base),
        "with_help": project(balance, contribs, r_help),
    })

# ==================================================
# Session defaults
# ==================================================
st.session_state.setdefault("age_used", 42)
st.session_state.setdefault("salary_used", 84000)
st.session_state.setdefault("balance_used", 76500)

# ==================================================
# Layout
# ==================================================
left, right = st.columns([1, 2], gap="large")

# ==================================================
# Inputs
# ==================================================
with left:
    st.subheader("Your Information")

    age_input = st.number_input("Your Age", 18, 100, st.session_state.age_used)
    salary_input = parse_number(st.text_input("Current Annual Salary ($)", "84,000"))
    balance_input = parse_number(st.text_input("Current 401(k) Balance ($)", "76,500"))

    company_list = load_company_names()

    company_input = st.selectbox(
        "Company Name",
        options=company_list,
        index=None,
        placeholder="Type your company's name",
        accept_new_options=True,
    )

    company = None
    if company_input and len(company_input.strip()) >= 3:
        normalized = company_input.strip().title()
        company = normalized if normalized in company_list else "My Company Is Not Listed"

    calculate = st.button("Calculate", type="primary")

# ==================================================
# Handle calculate
# ==================================================
if calculate and salary_input and balance_input and age_input < 65 and company:
    st.session_state.age_used = age_input
    st.session_state.salary_used = salary_input
    st.session_state.balance_used = balance_input

    try:
        if supabase:
            supabase.table("submissions").insert({
                "age": age_input,
                "salary": salary_input,
                "balance": balance_input,
                "company": company,
                "created_at": datetime.utcnow().isoformat(),
            }).execute()
    except Exception:
        pass

# ==================================================
# Compute projection
# ==================================================
df = compute_projection(
    st.session_state.age_used,
    st.session_state.salary_used,
    st.session_state.balance_used,
)

# ==================================================
# Chart
# ==================================================
with right:
    st.subheader("Estimated 401(k) Growth")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["age"],
        y=df["baseline"],
        mode="lines",
        name="On Your Lonesome (8.5%)",
        line=dict(color=baseline_color, width=3),
    ))

    fig.add_trace(go.Scatter(
        x=df["age"],
        y=df["with_help"],
        mode="lines",
        name="With Bison by Your Side (11.8%)",
        line=dict(color=help_color, width=4),
    ))

    fig.update_layout(
        template="plotly_dark" if is_dark_mode else "plotly",
        height=450,
        margin=dict(l=20, r=20, t=20, b=40),
        plot_bgcolor=plot_bg,
        paper_bgcolor=paper_bg,
        font=dict(color=axis_color),
        xaxis=dict(
            title=dict(text="Age"),
            gridcolor=grid_color,
            zeroline=False,
            fixedrange=True,
        ),
        yaxis=dict(
            title=dict(text="Portfolio Value ($)"),
            gridcolor=grid_color,
            zeroline=False,
            fixedrange=True,
        ),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        hovermode="x unified",
        dragmode=False,
    )

    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

# ==================================================
# CTA
# ==================================================
final_diff = df["with_help"].iloc[-1] - df["baseline"].iloc[-1]

st.markdown(
    f"""
    <div style="text-align:center; font-size:24px; margin-top:24px;">
        Is <span style="font-weight:700; color:{help_color};">
        ${final_diff:,.0f}</span> worth 30 minutes of your time?
    </div>
    """,
    unsafe_allow_html=True,
)

# ==================================================
# Calendly
# ==================================================
DEFAULT_CALENDLY = "https://calendly.com/placeholder"
ALT_CALENDLY = "https://calendly.com/placeholder-not-listed"

calendly_link = ALT_CALENDLY if company == "My Company Is Not Listed" else DEFAULT_CALENDLY

st.markdown(
    f"""
    <div style="text-align:center; margin-top:20px;">
        <a href="{calendly_link}" target="_blank"
           style="background-color:#C17A49; color:white;
                  padding:14px 28px; text-decoration:none;
                  border-radius:8px; font-size:18px;">
           Schedule a Conversation
        </a>
    </div>
    """,
    unsafe_allow_html=True,
)

# ==================================================
# Disclosure
# ==================================================
st.space("large")
st.space("large")
st.caption(
    "For illustrative purposes only. Assumes 3% annual salary growth and 12.4% annual contribution "
    "(7.8% employee, 4.6% employer). Performance without help is the 5-year annualized return of the "
    "S&P Target Date 2035 Index. With help is increased by 3.32% based on the Hewitt Study."
)
