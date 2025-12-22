import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from supabase import create_client, Client
from pathlib import Path

# --------------------------------------------------
# Streamlit Page Config (iframe-ready)
# --------------------------------------------------
st.set_page_config(
    page_title="Bison Wealth 401(k) Growth Simulator",
    page_icon="🦬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --------------------------------------------------
# Hide Streamlit chrome (iframe widget)
# --------------------------------------------------
st.markdown(
    """
    <style>
    header { visibility: hidden; height: 0px; }
    footer { visibility: hidden; height: 0px; }
    #MainMenu { visibility: hidden; }

    :root {
        color-scheme: light;
    }

    html, body, .stApp {
        overflow-x: hidden;
        background-color: white !important;
        color: #111827;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------
# Fixed (light-mode) colors
# --------------------------------------------------
plot_bg = "white"
paper_bg = "white"
grid_color = "#E0E0E0"
axis_color = "#000000"

baseline_color = "#9CA3AF"   # neutral gray
help_color = "#C17A49"       # Bison orange
diff_color = help_color

plot_template = "plotly_white"

# --------------------------------------------------
# Global CSS
# --------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Montserrat', sans-serif;
    }

    div.stButton > button:first-child {
        background-color: #C17A49;
        color: white;
        border-color: #C17A49;
    }
    div.stButton > button:first-child:hover {
        background-color: #A86B3D;
        border-color: #A86B3D;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------
# Supabase Setup (safe)
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
    data_path = Path(__file__).resolve().parent / "401k Data.csv"
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

# --------------------------------------------------
# Header
# --------------------------------------------------
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
        "with_help": project(balance, annual_contribs, r_help),
    })

# --------------------------------------------------
# Session Defaults
# --------------------------------------------------
st.session_state.setdefault("age_used", 42)
st.session_state.setdefault("salary_used", 84000)
st.session_state.setdefault("balance_used", 76500)

# --------------------------------------------------
# Inputs
# --------------------------------------------------
left, right = st.columns([1, 2])

with left:
    st.subheader("Your Information")

    age_input = st.number_input("Age", 18, 100, 42)
    salary_input = parse_number(st.text_input("Current Annual Salary ($)", "84,000"))
    balance_input = parse_number(st.text_input("Current 401(k) Balance ($)", "76,500"))

    company_list = load_company_names()

    company_input = st.selectbox(
        "Company Name",
        options=company_list,
        index=None,
        placeholder="Type your company's name",
        accept_new_options=True
    )

    company = None
    if company_input and len(company_input.strip()) >= 3:
        normalized = company_input.strip().title()
        company = normalized if normalized in company_list else "My Company Is Not Listed"

    calculate = st.button("Calculate", type="primary")

# --------------------------------------------------
# Handle Calculate
# --------------------------------------------------
if calculate:
    if salary_input is None or salary_input <= 0:
        st.error("Please enter a salary greater than $0 to run the projection.")
    elif balance_input is None:
        st.error("Please enter your current 401(k) balance.")
    elif age_input >= 65:
        st.error("Projection only supports ages under 65.")
    elif not company:
        st.error("Please select or enter a company name.")
    else:
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
        line=dict(color=baseline_color, width=3),
    ))

    fig.add_trace(go.Scatter(
        x=df["age"],
        y=df["with_help"],
        mode="lines",
        name="With Bison by Your Side (11.8%)",
        line=dict(color=help_color, width=4),
    ))

    x_max = df["age"].iloc[-1]
    x_min = df["age"].iloc[0]
    x_padding = 1 if len(df) > 1 else 0.5

    fig.add_trace(go.Scatter(
        x=[x_max],
        y=[df["baseline"].iloc[-1]],
        mode="markers+text",
        text=[f"${df['baseline'].iloc[-1]:,.0f}"],
        textposition="top left",
        textfont=dict(size=14),
        marker=dict(color=baseline_color, size=10),
        showlegend=False,
        cliponaxis=False,
    ))

    fig.add_trace(go.Scatter(
        x=[x_max],
        y=[df["with_help"].iloc[-1]],
        mode="markers+text",
        text=[f"${df['with_help'].iloc[-1]:,.0f}"],
        textposition="middle left",
        textfont=dict(size=14),
        marker=dict(color=help_color, size=10),
        showlegend=False,
        cliponaxis=False,
    ))

    fig.update_layout(
        height=450,
        margin=dict(l=20, r=8, t=20, b=80),
        plot_bgcolor=plot_bg,
        paper_bgcolor=paper_bg,
        template=plot_template,
        font=dict(family="Montserrat", color=axis_color),
        hovermode="x unified",
    )

    fig.update_xaxes(
        title_text="Age",
        title_font=dict(color="#111827", size=13),
        gridcolor=grid_color,
        zeroline=False,
        fixedrange=True,
        range=[x_min, x_max + x_padding],
        tickfont=dict(color="#1F2937"),
    )

    fig.update_yaxes(
        title_text="Portfolio Value ($)",
        title_font=dict(color="#111827", size=13),
        gridcolor=grid_color,
        zeroline=False,
        fixedrange=True,
        tickfont=dict(color="#1F2937"),
    )

    fig.update_layout(
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            orientation="h",
            yanchor="top",
            y=-0.25,
            xanchor="center",
            x=0.5,
            font=dict(color="#111827")
        )
    )

    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

# --------------------------------------------------
# CTA
# --------------------------------------------------
final_diff = df["with_help"].iloc[-1] - df["baseline"].iloc[-1]

st.markdown(
    f"""
    <div style="text-align:center; font-size:26px; margin-top:20px;">
        Is <span style="font-weight:700; color:{diff_color};">
        ${final_diff:,.0f}</span> worth 30 minutes of your time?
    </div>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------
# Calendly
# --------------------------------------------------
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
    unsafe_allow_html=True
)

# --------------------------------------------------
# Disclosure
# --------------------------------------------------
st.space("large")
st.space("large")
st.caption(
    "For illustrative purposes only. Assumes 3% annual salary growth and 12.4% annual contribution "
    "(7.8% employee, 4.6% employer). Performance without help is the 5-year annualized return of the "
    "S&P Target Date 2035 Index. With help is increased by 3.32% based on the Hewitt Study."
)
