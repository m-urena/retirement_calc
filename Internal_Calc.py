import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Optional, Dict, Any

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

plot_bg = "white"
paper_bg = "white"
grid_color = "#E0E0E0"
axis_color = "#000000"

without_color = "#9CA3AF"
with_color = "#C17A49"

plot_template = "plotly_white"

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif; }

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
    unsafe_allow_html=True,
)


def parse_number(x: str) -> Optional[float]:
    try:
        return float(str(x).replace(",", "").strip())
    except Exception:
        return None


def pct_from_decimal(x: float) -> str:
    return f"{x*100:.2f}%"


MODEL_OPTIONS = {
    "Core": 0.1071,
    "Balanced Growth": 0.1133,
    "Growth": 0.1291,
    "Aggressive": 0.1356,
}

CONTRIB_FREQ_OPTIONS = {
    "Semi-monthly (24x/year)": 24,
    "Bi-weekly (26x/year)": 26,
}

WITHOUT_HELP_RETURN = 0.0819


def build_pay_period_schedule(annual_amount: float, periods_per_year: int) -> list[float]:
    if periods_per_year <= 0:
        return []
    amt = annual_amount / float(periods_per_year)
    return [amt] * periods_per_year


@st.cache_data(show_spinner=False)
def compute_projection_two_lines(age: int, salary: float, balance: float, cfg: Dict[str, Any]) -> pd.DataFrame:
    target_age = int(cfg["target_age"])
    if age >= target_age or salary <= 0:
        return pd.DataFrame({"age": [age], "without_help": [balance], "with_model": [balance]})

    years = target_age - age

    salary_growth = float(cfg["salary_growth_rate_pct"]) / 100.0
    employee_rate = float(cfg["employee_contrib_rate_pct"]) / 100.0
    employer_rate = float(cfg["employer_contrib_rate_pct"]) / 100.0
    annual_contrib_rate = employee_rate + employer_rate

    model_return = float(cfg["model_return"])
    periods_per_year = int(cfg["contributions_per_year"])

    r_period_without = (1.0 + WITHOUT_HELP_RETURN) ** (1.0 / periods_per_year) - 1.0
    r_period_with = (1.0 + model_return) ** (1.0 / periods_per_year) - 1.0

    total_wo = float(balance)
    total_w = float(balance)

    ages = [age]
    wo = [total_wo]
    w = [total_w]

    for yr in range(1, years + 1):
        current_salary = salary * ((1.0 + salary_growth) ** (yr - 1))
        annual_contrib_amount = current_salary * annual_contrib_rate
        contrib_schedule = build_pay_period_schedule(annual_contrib_amount, periods_per_year)

        for c in contrib_schedule:
            total_wo *= (1.0 + r_period_without)
            total_wo += c

            total_w *= (1.0 + r_period_with)
            total_w += c

        ages.append(age + yr)
        wo.append(total_wo)
        w.append(total_w)

    return pd.DataFrame({"age": ages, "without_help": wo, "with_model": w})


st.session_state.setdefault("age_used", 42)
st.session_state.setdefault("salary_used", 84000.0)
st.session_state.setdefault("balance_used", 76500.0)
st.session_state.setdefault("cfg", {})
cfg = st.session_state.cfg

cfg.setdefault("target_age", 65)
cfg.setdefault("salary_growth_rate_pct", 3.0)
cfg.setdefault("employee_contrib_rate_pct", 7.8)
cfg.setdefault("employer_contrib_rate_pct", 4.6)

cfg.setdefault("contrib_frequency_label", "Bi-weekly (26x/year)")
cfg.setdefault("contributions_per_year", CONTRIB_FREQ_OPTIONS.get(cfg["contrib_frequency_label"], 26))

if cfg.get("model_name") not in MODEL_OPTIONS:
    cfg["model_name"] = list(MODEL_OPTIONS.keys())[0]
cfg["model_return"] = float(MODEL_OPTIONS[cfg["model_name"]])

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
            step=0.25,
        )

        cfg["employer_contrib_rate_pct"] = st.number_input(
            "Employer contribution rate (%)",
            0.0,
            50.0,
            float(cfg["employer_contrib_rate_pct"]),
            step=0.25,
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

        st.caption(f'Comparison line "Without Help" is fixed at {pct_from_decimal(WITHOUT_HELP_RETURN)} annual return.')

    model_choice = st.selectbox(
        "Model selection",
        list(MODEL_OPTIONS.keys()),
        index=list(MODEL_OPTIONS.keys()).index(cfg["model_name"]) if cfg["model_name"] in MODEL_OPTIONS else 0,
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
        cfg["model_name"] = model_choice
        cfg["model_return"] = float(MODEL_OPTIONS[model_choice])

df = compute_projection_two_lines(
    int(st.session_state.age_used),
    float(st.session_state.salary_used),
    float(st.session_state.balance_used),
    cfg,
)

with right:
    st.subheader("Projected 401(k) Balance")

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["age"],
            y=df["without_help"],
            mode="lines",
            name=f"Without Help ({pct_from_decimal(WITHOUT_HELP_RETURN)})",
            line=dict(color=without_color, width=3),
            showlegend=False,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["age"],
            y=df["with_model"],
            mode="lines",
            name=f"{cfg['model_name']} ({pct_from_decimal(float(cfg['model_return']))})",
            line=dict(color=with_color, width=4),
            showlegend=False,
        )
    )

    x_max = df["age"].iloc[-1]
    x_min = df["age"].iloc[0]
    x_padding = 1 if len(df) > 1 else 0.5

    fig.add_trace(
        go.Scatter(
            x=[x_max],
            y=[df["without_help"].iloc[-1]],
            mode="markers+text",
            text=[f"${df['without_help'].iloc[-1]:,.0f}"],
            textposition="top left",
            textfont=dict(size=14, color=axis_color),
            marker=dict(color=without_color, size=10),
            showlegend=False,
            cliponaxis=False,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[x_max],
            y=[df["with_model"].iloc[-1]],
            mode="markers+text",
            text=[f"${df['with_model'].iloc[-1]:,.0f}"],
            textposition="middle left",
            textfont=dict(size=14, color=axis_color),
            marker=dict(color=with_color, size=10),
            showlegend=False,
            cliponaxis=False,
        )
    )

    fig.update_layout(
        height=450,
        margin=dict(l=24, r=16, t=20, b=55),
        plot_bgcolor=plot_bg,
        paper_bgcolor=paper_bg,
        template=plot_template,
        font=dict(family="Montserrat", color=axis_color),
        xaxis=dict(
            title=dict(text="Age", font=dict(color=axis_color, size=13)),
            gridcolor=grid_color,
            zeroline=False,
            fixedrange=True,
            range=[x_min, x_max + x_padding],
            tickfont=dict(color=axis_color),
        ),
        yaxis=dict(
            title=dict(text="Portfolio Value ($)", font=dict(color=axis_color, size=13)),
            gridcolor=grid_color,
            zeroline=False,
            fixedrange=True,
            tickfont=dict(color=axis_color),
        ),
        hovermode="x unified",
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

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
                <span class="bw-swatch" style="background:{without_color};"></span>
                Without Help ({pct_from_decimal(WITHOUT_HELP_RETURN)})
            </div>
            <div class="bw-legend-item">
                <span class="bw-swatch" style="background:{with_color};"></span>
                {cfg["model_name"]} ({pct_from_decimal(float(cfg["model_return"]))})
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
    f'Baseline "Without Help" return: {pct_from_decimal(WITHOUT_HELP_RETURN)}.'
)
