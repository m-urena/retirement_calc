import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Optional, Dict, Any
from pathlib import Path
import base64

st.set_page_config(
    page_title="Internal Retire Calc",
    page_icon="🦬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

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
    unsafe_allow_html=True,
)
#keep input text black
st.markdown(
    """
    <style>
    /* Keep labels + helper text readable even if browser forces dark-mode styles */
    [data-testid="stWidgetLabel"] p,
    [data-testid="stWidgetLabel"] label,
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] span,
    [data-testid="stMarkdownContainer"] label,
    [data-testid="stForm"] label,
    .stCaption,
    .stMarkdown,
    .stTextInput label,
    .stNumberInput label,
    .stSelectbox label,
    .stMultiSelect label,
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] summary *,
    [data-testid="stExpander"] div,
    [data-testid="stExpander"] div * {
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
    }

    /* Also keep input text dark (some phones flip it) */
    input, textarea, select {
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
        caret-color: #111827 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
#text inside the input blocks
st.markdown(
    """
    <style>
    @media (prefers-color-scheme: dark) {
        /* Text typed into inputs */
        input, textarea {
            color: #FFFFFF !important;
            -webkit-text-fill-color: #FFFFFF !important;
            caret-color: #FFFFFF !important;
        }

        /* Placeholder text */
        input::placeholder, textarea::placeholder {
            color: rgba(255, 255, 255, 0.65) !important;
            -webkit-text-fill-color: rgba(255, 255, 255, 0.65) !important;
            opacity: 1 !important;
        }

        /* Streamlit BaseWeb selectbox text */
        [data-baseweb="select"] * {
            color: #FFFFFF !important;
            -webkit-text-fill-color: #FFFFFF !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


plot_bg = "white"
paper_bg = "white"
grid_color = "#E0E0E0"
axis_color = "#000000"

ACCENT = "#F97113"
ACCENT_HOVER = "#E5620F"
ACCENT_SOFT = "rgba(249, 113, 19, 0.10)"

with_color = ACCENT
plot_template = "plotly_white"

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

        html, body, .stApp {{
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

        .material-icons,
        .material-symbols-outlined,
        .material-symbols-rounded,
        i.material-icons,
        span.material-icons {{
            font-family: "Material Icons" !important;
            font-weight: normal !important;
            font-style: normal !important;
            letter-spacing: normal !important;
            text-transform: none !important;
            display: inline-block !important;
            white-space: nowrap !important;
            word-wrap: normal !important;
            direction: ltr !important;
            -webkit-font-feature-settings: "liga" !important;
            -webkit-font-smoothing: antialiased !important;
        }}

        div.stButton > button:first-child {{
            background-color: {ACCENT};
            color: white;
            border-color: {ACCENT};
            font-family: "Urbanist", sans-serif !important;
            font-weight: 700 !important;
        }}
        div.stButton > button:first-child:hover {{
            background-color: {ACCENT_HOVER};
            border-color: {ACCENT_HOVER};
        }}
        div.stButton > button:first-child:focus {{
            outline: none !important;
            box-shadow: 0 0 0 0.2rem {ACCENT_SOFT} !important;
        }}

        input, textarea {{
            border-radius: 10px !important;
        }}
        input:focus, textarea:focus {{
            border-color: {ACCENT} !important;
            box-shadow: 0 0 0 0.2rem {ACCENT_SOFT} !important;
        }}

        [data-baseweb="select"] > div {{
            border-radius: 10px !important;
        }}
        [data-baseweb="select"] > div:focus-within {{
            border-color: {ACCENT} !important;
            box-shadow: 0 0 0 0.2rem {ACCENT_SOFT} !important;
        }}

        [data-testid="stNumberInput"] div:focus-within {{
            border-color: {ACCENT} !important;
            box-shadow: 0 0 0 0.2rem {ACCENT_SOFT} !important;
            border-radius: 10px !important;
        }}

        [data-testid="stExpander"] details {{
            border: 1px solid rgba(17, 24, 39, 0.12) !important;
            border-radius: 12px !important;
            overflow: hidden !important;
        }}
        [data-testid="stExpander"] summary {{
            background: {ACCENT_SOFT} !important;
            border-bottom: 1px solid rgba(17, 24, 39, 0.08) !important;
            padding: 10px 12px !important;
        }}
        [data-testid="stExpander"] summary:hover {{
            background: rgba(249, 113, 19, 0.14) !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

inject_brand_fonts()

def parse_number(x: str) -> Optional[float]:
    try:
        return float(str(x).replace(",", "").strip())
    except Exception:
        return None

def pct_from_decimal(x: float) -> str:
    return f"{x*100:.2f}%"
#model returns are the 5 year annualized total return of the howard SDBA models as of 01/01/2026
MODEL_OPTIONS = {
    "Core": 0.0878,
    "Balanced Growth": 0.0988,
    "Growth": 0.1068,
    "Aggressive": 0.1176,
}

MODEL_DROPDOWN_OPTIONS = list(MODEL_OPTIONS.keys()) + ["All Models"]

CONTRIB_FREQ_OPTIONS = {
    "Semi-monthly (24x/year)": 24,
    "Bi-weekly (26x/year)": 26,
}

def build_pay_period_schedule(annual_amount: float, periods_per_year: int) -> list[float]:
    if periods_per_year <= 0:
        return []
    amt = annual_amount / float(periods_per_year)
    return [amt] * periods_per_year

@st.cache_data(show_spinner=False)
def compute_projection_one_line(age: int, salary: float, balance: float, cfg: Dict[str, Any], model_return: float) -> pd.DataFrame:
    target_age = int(cfg["target_age"])
    if age >= target_age or salary <= 0:
        return pd.DataFrame({"age": [age], "value": [balance]})

    years = target_age - age

    salary_growth = float(cfg["salary_growth_rate_pct"]) / 100.0
    employee_rate = float(cfg["employee_contrib_rate_pct"]) / 100.0
    employer_rate = float(cfg["employer_contrib_rate_pct"]) / 100.0
    annual_contrib_rate = employee_rate + employer_rate

    periods_per_year = int(cfg["contributions_per_year"])
    r_period = (1.0 + float(model_return)) ** (1.0 / periods_per_year) - 1.0

    total = float(balance)
    ages = [age]
    vals = [total]

    for yr in range(1, years + 1):
        current_salary = salary * ((1.0 + salary_growth) ** (yr - 1))
        annual_contrib_amount = current_salary * annual_contrib_rate
        contrib_schedule = build_pay_period_schedule(annual_contrib_amount, periods_per_year)

        for c in contrib_schedule:
            total *= (1.0 + r_period)
            total += c

        ages.append(age + yr)
        vals.append(total)

    return pd.DataFrame({"age": ages, "value": vals})

st.session_state.setdefault("age_used", 42)
st.session_state.setdefault("salary_used", 84000.0)
st.session_state.setdefault("balance_used", 76500.0)
st.session_state.setdefault("cfg", {})
cfg = st.session_state.cfg

cfg.setdefault("target_age", 65)
cfg.setdefault("salary_growth_rate_pct", 3.0)
cfg.setdefault("employee_contrib_rate_pct", 7.8)
cfg.setdefault("employer_contrib_rate_pct", 4.6)
cfg.setdefault("model_selection", "Core")

cfg.setdefault("contrib_frequency_label", "Bi-weekly (26x/year)")
cfg.setdefault("contributions_per_year", CONTRIB_FREQ_OPTIONS.get(cfg["contrib_frequency_label"], 26))

if cfg.get("model_selection") not in MODEL_DROPDOWN_OPTIONS:
    cfg["model_selection"] = "Core"

st.title("Internal Retire Calc")

left, right = st.columns([1, 2])

with left:
    st.subheader("Inputs")

    age_input = st.number_input("Current age", 18, 100, int(st.session_state.age_used))

    target_age_input = st.number_input(
        "Retirement age",
        min_value=max(40, int(age_input) + 1),
        max_value=90,
        value=int(cfg["target_age"]),
        step=1,
    )

    salary_input = parse_number(st.text_input("Current annual salary ($)", f"{st.session_state.salary_used:,.0f}"))
    balance_input = parse_number(st.text_input("Current 401(k) balance ($)", f"{st.session_state.balance_used:,.0f}"))

    with st.expander("Assumptions", expanded=False):
        cfg["salary_growth_rate_pct"] = st.number_input(
            "Annual salary growth (%)",
            0.0,
            20.0,
            float(cfg["salary_growth_rate_pct"]),
            step=0.25,
        )

        cfg["employee_contrib_rate_pct"] = st.number_input(
            "Employee contribution rate (%)",
            0.0,
            50.0,
            float(cfg["employee_contrib_rate_pct"]),
            step=0.01,
        )

        cfg["employer_contrib_rate_pct"] = st.number_input(
            "Employer contribution rate (%)",
            0.0,
            50.0,
            float(cfg["employer_contrib_rate_pct"]),
            step=0.01,
        )

        cfg["contrib_frequency_label"] = st.selectbox(
            "Contribution frequency",
            list(CONTRIB_FREQ_OPTIONS.keys()),
            index=list(CONTRIB_FREQ_OPTIONS.keys()).index(cfg["contrib_frequency_label"])
            if cfg["contrib_frequency_label"] in CONTRIB_FREQ_OPTIONS
            else 0,
            help="Annual contribution rate stays the same. Contributions are deposited at the end of each pay period.",
        )
        cfg["contributions_per_year"] = int(CONTRIB_FREQ_OPTIONS[cfg["contrib_frequency_label"]])

    model_choice = st.selectbox(
        "Model selection",
        MODEL_DROPDOWN_OPTIONS,
        index=MODEL_DROPDOWN_OPTIONS.index(cfg["model_selection"]) if cfg["model_selection"] in MODEL_DROPDOWN_OPTIONS else 0,
    )

    calculate = st.button("Calculate", type="primary")

if calculate:
    if salary_input is None or salary_input <= 0:
        st.error("Enter a salary greater than $0.")
    elif balance_input is None:
        st.error("Enter a current 401(k) balance.")
    elif int(age_input) >= int(target_age_input):
        st.error("Retirement age must be greater than current age.")
    else:
        st.session_state.age_used = int(age_input)
        st.session_state.salary_used = float(salary_input)
        st.session_state.balance_used = float(balance_input)

        cfg["target_age"] = int(target_age_input)
        cfg["model_selection"] = model_choice

with right:
    st.subheader("Projected 401(k) Balance")

    fig = go.Figure()
    selected = cfg.get("model_selection", "All Models")

    if selected == "All Models":
        dfs = {}
        for name, r in MODEL_OPTIONS.items():
            dfs[name] = compute_projection_one_line(
                int(st.session_state.age_used),
                float(st.session_state.salary_used),
                float(st.session_state.balance_used),
                cfg,
                r,
            )

        base_age = next(iter(dfs.values()))["age"]
        x_max = base_age.iloc[-1]
        x_min = base_age.iloc[0]
        x_padding = 1 if len(base_age) > 1 else 0.5

        final_lines = []

        for name, dfi in dfs.items():
            fig.add_trace(
                go.Scatter(
                    x=dfi["age"],
                    y=dfi["value"],
                    mode="lines",
                    name=f"{name} ({pct_from_decimal(float(MODEL_OPTIONS[name]))})",
                    line=dict(width=4),
                    showlegend=False,
                )
            )
            final_lines.append((name, float(dfi["value"].iloc[-1])))

        final_lines.sort(key=lambda t: t[1], reverse=True)

        annotation_html = "<br>".join(
            [f"<b>{name}:</b> ${val:,.0f}" for name, val in final_lines]
        )

        fig.add_annotation(
            xref="paper", yref="paper",
            x=0.02, y=0.98,
            xanchor="left", yanchor="top",
            text=annotation_html,
            showarrow=False,
            align="left",
            font=dict(family="Urbanist", size=13, color=axis_color),
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="rgba(0,0,0,0.08)",
            borderwidth=1,
            borderpad=8,
        )

    else:
        model_return = float(MODEL_OPTIONS[selected])
        df = compute_projection_one_line(
            int(st.session_state.age_used),
            float(st.session_state.salary_used),
            float(st.session_state.balance_used),
            cfg,
            model_return,
        )

        fig.add_trace(
            go.Scatter(
                x=df["age"],
                y=df["value"],
                mode="lines",
                name=f"{selected} ({pct_from_decimal(model_return)})",
                line=dict(color=with_color, width=4),
                showlegend=False,
            )
        )

        x_max = df["age"].iloc[-1]
        x_min = df["age"].iloc[0]
        x_padding = 1 if len(df) > 1 else 0.5

        final_val = float(df["value"].iloc[-1])

        fig.add_annotation(
            xref="paper", yref="paper",
            x=0.02, y=0.98,
            xanchor="left", yanchor="top",
            text=f"<b>{selected}:</b> ${final_val:,.0f}",
            showarrow=False,
            align="left",
            font=dict(family="Urbanist", size=13, color=axis_color),
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="rgba(0,0,0,0.08)",
            borderwidth=1,
            borderpad=8,
        )

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

salary_growth_dec = float(cfg["salary_growth_rate_pct"]) / 100.0
employee_dec = float(cfg["employee_contrib_rate_pct"]) / 100.0
employer_dec = float(cfg["employer_contrib_rate_pct"]) / 100.0
total_contrib_dec = employee_dec + employer_dec

st.space("large")
st.caption(
    "Internal tool. "
    f"Salary growth: {pct_from_decimal(salary_growth_dec)}. "
    f"Annual contributions: {pct_from_decimal(total_contrib_dec)} "
    f"({pct_from_decimal(employee_dec)} employee, {pct_from_decimal(employer_dec)} employer). "
    f"Contribution frequency: {cfg['contrib_frequency_label']} (deposited at end of each pay period). "
    f"Retirement age: {int(cfg['target_age'])}. "
    f"Model selection: {cfg.get('model_selection', 'All Models')}."
)
