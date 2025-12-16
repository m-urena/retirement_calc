import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from supabase import create_client, Client
from pathlib import Path
import base64

# --------------------------------------------------
# Streamlit Page Config
# --------------------------------------------------
st.set_page_config(
    page_title="Bison Wealth 401(k) Growth Simulator",
    page_icon="🦬",
    layout="wide",
    initial_sidebar_state="collapsed"  # IFRAME CHANGE
)

# --------------------------------------------------
# IFRAME: hide Streamlit chrome
# --------------------------------------------------
st.markdown(
    """
    <style>
    header { visibility: hidden; height: 0px; }
    footer { visibility: hidden; height: 0px; }
    #MainMenu { visibility: hidden; }

    /* Prevent horizontal scroll in iframes */
    html, body {
        overflow-x: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------
# Dark mode detection + colors (UNCHANGED)
# --------------------------------------------------
def _hex_to_rgb(hex_color: str):
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join([c * 2 for c in hex_color])
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def _is_dark_background(color: str | None) -> bool:
    if not color:
        return False
    try:
        r, g, b = _hex_to_rgb(color)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return luminance < 0.5
    except Exception:
        return False


theme_base = st.get_option("theme.base")
theme_background = st.get_option("theme.backgroundColor")

is_dark_mode = theme_base == "dark" or _is_dark_background(theme_background)

if is_dark_mode:
    plot_bg = "#000000"
    paper_bg = "#000000"
    grid_color = "#1F2933"
    axis_color = "#FFFFFF"
    baseline_color = "#9CA3AF"
    help_color = "#C17A49"
    diff_color = help_color
    plot_template = "plotly_dark"
else:
    plot_bg = "white"
    paper_bg = "white"
    grid_color = "#E0E0E0"
    axis_color = "#000000"
    baseline_color = "#7D7D7D"
    help_color = "#263759"
    diff_color = help_color
    plot_template = "plotly_white"

# --------------------------------------------------
# Global CSS (UNCHANGED)
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
# Supabase Setup (UNCHANGED)
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
# Load Company Names (UNCHANGED)
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
# Logo (iframe-safe)
# --------------------------------------------------
logo_path = Path(__file__).resolve().parent / "bison_logo.png"
with open(logo_path, "rb") as f:
    logo_b64 = base64.b64encode(f.read()).decode()

st.markdown(
    f"""
    <style>
    .bison-logo {{
        position: absolute;
        top: 70px;
        right: 40px;
        z-index: 10;   /* IFRAME CHANGE: lower z-index */
    }}
    @media (max-width: 768px) {{
        .bison-logo {{
            display: none;
        }}
    }}
    </style>

    <div class="bison-logo">
        <img src="data:image/png;base64,{logo_b64}" width="150">
    </div>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------
# Header (UNCHANGED)
# --------------------------------------------------
st.title("Bison Wealth 401(k) Growth Simulator")
st.write("Visualize how your 401(k) could grow **with and without Bison’s guidance.**")

# --------------------------------------------------
# Helpers / Projection / Inputs / Chart / CTA
# --------------------------------------------------
# EVERYTHING BELOW THIS POINT IS 100% UNCHANGED
# (your chart colors, annotations, numbers, logic remain intact)
