import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from supabase import create_client, Client
from pathlib import Path
import base64

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

    :root { color-scheme: light; }

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
# Brand fonts
# Headline: Rethink Sans
# Normal/UI: Urbanist
# Files expected:
#   Fonts/Urbanist-VariableFont_wght.ttf
#   Fonts/RethinkSans-VariableFont_wght.ttf
# --------------------------------------------------
def _b64_file(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("utf-8")

def inject_brand_fonts():
    font_dir = Path(__file__).resolve().parent / "Fonts"

    body_font_path = font_dir / "Urbanist-VariableFont_wght.ttf"
    headline_font_path = font_dir / "RethinkSans-VariableFont_wght.ttf"

    if not body_font_path.exists() or not headline_font_path.exists():
        st.warning("Font files not found in ./Fonts. Check folder name and filenames.")
        return

    body_b64 = _b64_file(body_font_path)
    headline_b64 = _b64_file(headline_font_path)

    st.markdown(
        f"""
        <style>
        @font-face {{
            font-family: "Urbanist";
            src: url(data:font/ttf;base64,{body_b64}) format("truetype");
            font-weight: 100 900;
            font-style: normal;
            font-display: swap;
        }}

        @font-face {{
            font-family: "Rethink Sans";
            src: url(data:font/ttf;base64,{headline_b64}) format("truetype");
            font-weight: 100 900;
            font-style: normal;
            font-display: swap;
        }}

        html, body, .stApp, [class*="css"], [class*="st-"] {{
            font-family: "Urbanist", sans-serif !important;
            font-weight: 400 !important;
        }}

        h1,
        .stTitle,
        [data-testid="stMarkdownContainer"] h1 {{
            font-family: "Rethink Sans", "Urbanist", sans-serif !important;
            font-weight: 800 !important;
        }}

        h2, h3, h4, h5, h6,
        .stHeader, .stSubheader,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3,
        [data-testid="stMarkdownContainer"] h4 {{
            font-family: "Urbanist", sans-serif !important;
            font-weight: 600 !important;
        }}

        div.stButton > button:first-child {{
            background-color: #C17A49;
            color: white;
            border-color: #C17A49;
            font-family: "Urbanist", sans-serif !important;
            font-weight: 700 !important;
        }}
        div.stButton > button:first-child:hover {{
            background-color: #A86B3D;
            border-color: #A86B3D;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

inject_brand_fonts()

# --------------------------------------------------
# Fixed (light-mode) colors
# --------------------------------------------------
plot_bg = "white"
paper_bg = "white"
grid_color = "#E0E0E0"
axis_color = "#000000"

baseline_color = "#9CA3AF"
help_color = "#F97113"
diff_color = help_color

plot_template = "plotly_white"

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
    r_no_help = 0.0819
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
st.session_state.setdefault("age_used", 41)
st.session_state.setdefault("salary_used", 84000)
st.session_state.setdefault("balance_used", 76500)

# --------------------------------------------------
# Inputs + Chart columns
# --------------------------------------------------
left, right = st.columns([1, 2])

with left:
    st.subheader("Your Information")

    age_input = st.number_input("Age", 18, 100, 41)
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
# CTA above the chart (top, centered over graph)
# --------------------------------------------------
final_diff = df["with_help"].iloc[-1] - df["baseline"].iloc[-1]

with right:
    st.markdown(
        f"""
        <div style="text-align:center; font-size:26px; margin-top:6px; margin-bottom:10px;
                    font-family:'Urbanist', sans-serif; font-weight:600;">
            Is <span style="font-weight:800; color:{diff_color};">
            ${final_diff:,.0f}</span> worth 30 minutes of your time?
        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------
    # Chart (no header/subheader/title)
    # --------------------------------------------------
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["age"],
        y=df["baseline"],
        mode="lines",
        name="Average earnings without Bison (8.2%)",
        line=dict(color=baseline_color, width=3),
        showlegend=False,
    ))

    fig.add_trace(go.Scatter(
        x=df["age"],
        y=df["with_help"],
        mode="lines",
        name="Average earnings with Bison Managed 401(k) (11.5%)",
        line=dict(color=help_color, width=4),
        showlegend=False,
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
        textfont=dict(size=14, color=axis_color, family="Urbanist"),
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
        textfont=dict(size=14, color=axis_color, family="Urbanist"),
        marker=dict(color=help_color, size=10),
        showlegend=False,
        cliponaxis=False,
    ))

    fig.update_layout(
        height=450,
        margin=dict(l=24, r=16, t=20, b=55),
        plot_bgcolor=plot_bg,
        paper_bgcolor=paper_bg,
        template=plot_template,
        font=dict(family="Urbanist", color=axis_color),
        xaxis=dict(
            title=dict(text="Age", font=dict(color=axis_color, size=13, family="Urbanist")),
            gridcolor=grid_color,
            zeroline=False,
            fixedrange=True,
            range=[x_min, x_max + x_padding],
            tickfont=dict(color=axis_color, family="Urbanist"),
        ),
        yaxis=dict(
            title=dict(text="Portfolio Value ($)", font=dict(color=axis_color, size=13, family="Urbanist")),
            gridcolor=grid_color,
            zeroline=False,
            fixedrange=True,
            tickfont=dict(color=axis_color, family="Urbanist"),
        ),
        hovermode="x unified",
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # --------------------------------------------------
    # Legend text updates
    # --------------------------------------------------
    st.markdown(
        f"""
        <style>
        .bw-legend {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 22px;
            flex-wrap: wrap;
            margin-top: 8px;
            font-family: "Urbanist", sans-serif;
            font-weight: 400;
        }}
        .bw-legend-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 14px;
            color: #000000;
            white-space: nowrap;
        }}
        .bw-swatch {{
            width: 34px;
            height: 4px;
            border-radius: 2px;
            display: inline-block;
        }}
        @media (max-width: 640px) {{
            .bw-legend {{
                flex-direction: column;
                gap: 10px;
            }}
            .bw-legend-item {{
                white-space: normal;
                justify-content: center;
                text-align: center;
            }}
        }}
        </style>

        <div class="bw-legend">
            <div class="bw-legend-item">
                <span class="bw-swatch" style="background:{baseline_color};"></span>
                Average earnings without Bison (8.2%)
            </div>
            <div class="bw-legend-item">
                <span class="bw-swatch" style="background:{help_color};"></span>
                Average earnings with Bison Managed 401(k) (11.5%)
            </div>
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
                  border-radius:8px; font-size:18px;
                  font-family:'Urbanist', sans-serif; font-weight:700;">
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
    "S&P Target Date 2035 Index as of Dec 31, 2025. With help is increased by 3.32% based on the Hewitt Study."
)
