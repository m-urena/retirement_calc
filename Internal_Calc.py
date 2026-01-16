import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
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

line_color = "#C17A49"
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


def _pct(x: float) -> str:
    return f"{x*100:.1f}%"


@st.cache_data(show_spinner=False)
def compute_projection(age: int, salary: float, balance: float, cfg: Dict[str, Any]) -> pd.DataFrame:
    target_age = int(cfg["target_age"])
    if age >= target_age or salary <= 0:
        return pd.DataFrame({"age": [age], "balance": [balance]})

    years = target_age - age
    num_points = years + 1

    salary_growth_rate = float(cfg["salary_growth_rate"])

    employee_contrib_rate = float(cfg["employee_contrib_rate"])
    employer_contrib_rate = float(cfg["employer_contrib_rate"])
    contribution_rate = employee_contrib_rate + employer_contrib_rate

    annual_return = float(cfg["model_return"])

    comp_per_year = int(cfg["compounding_per_year"])
    contrib_per_year = int(cfg["contributions_per_year"])
    timing = cfg["contribution_timing"]

    salaries = [salary * ((1 + salary_growth_rate) ** yr) for yr in range(num_points)]
    annual_contribs = [s * contribution_rate for s in salaries]

    def project(start: float, yearly_contribs: list[float], rate: float) -> list[float]:
        total = start
        out = [start]

        per_period_rate = (1 + rate) ** (1 / comp_per_year)
        growth_factor = per_period_rate ** comp_per_year

        periods_per_contrib = max(1, comp_per_year // max(1, contrib_per_year))
        contrib_growth_factor = per_period_rate ** periods_per_contrib

        if abs(contrib_growth_factor - 1.0) < 1e-12:
            contrib_annuity_factor = float(periods_per_contrib)
        else:
            contrib_annuity_factor = (contrib_growth_factor - 1.0) / (per_period_rate - 1.0)

        for yearly in yearly_contribs:
            total = total * growth_factor

            per_contrib = yearly / contrib_per_year
            if timing == "beginning":
                total += per_contrib * (contrib_annuity_factor * contrib_per_year) * per_period_rate
            else:
                total += per_contrib * (contrib_annuity_factor * contrib_per_year)

            out.append(total)

        return out[:num_points]

    return pd.DataFrame(
        {
            "age": list(range(age, age + num_points)),
            "balance": project(balance, annual_contribs, annual_return),
        }
    )


st.session_state.setdefault("age_used", 42)
st.session_state.setdefault("salary_used", 84000.0)
st.session_state.setdefault("balance_used", 76500.0)
st.session_state.setdefault("cfg", {})
cfg = st.session_state.cfg

cfg.setdefault("target_age", 65)
cfg.setdefault("salary_growth_rate", 0.03)

cfg.setdefault("employee_contrib_rate", 0.078)
cfg.setdefault("employer_contrib_rate", 0.046)

cfg.setdefault("compounding_per_year", 12)
cfg.setdefault("contribution_timing", "end")

cfg.setdefault("model_name", "Model 1 (10.0%)")
cfg.setdefault("model_return", 0.10)

MODEL_OPTIONS = {
    "Model 1 (10.0%)": 0.10,
    "Model 2 (11.0%)": 0.11,
    "Model 3 (12.0%)": 0.12,
    "Model 4 (13.0%)": 0.13,
}

CONTRIB_FREQ_OPTIONS = {
    "Monthly (12x/year)": 12,
    "Quarterly (4x/year)": 4,
    "Yearly (1x/year)": 1,
}

cfg.setdefault("contrib_frequency_label", "Monthly (12x/year)")
cfg.setdefault("contributions_per_year", CONTRIB_FREQ_OPTIONS[cfg["contrib_frequency_label"]])

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
        cfg["salary_growth_rate"] = st.number_input(
            "Annual salary growth rate",
            0.0,
            0.20,
            float(cfg["salary_growth_rate"]),
            step=0.005,
            format="%.3f",
        )

        cfg["employee_contrib_rate"] = st.number_input(
            "Employee contribution rate",
            0.0,
            0.50,
            float(cfg["employee_contrib_rate"]),
            step=0.001,
            format="%.3f",
        )

        cfg["employer_contrib_rate"] = st.number_input(
            "Employer contribution rate",
            0.0,
            0.50,
            float(cfg["employer_contrib_rate"]),
            step=0.001,
            format="%.3f",
        )

        cfg["compounding_per_year"] = st.number_input("Compounding periods per year", 1, 365, int(cfg["compounding_per_year"]))

        cfg["contribution_timing"] = st.selectbox(
            "Contribution timing",
            ["end", "beginning"],
            index=0 if cfg["contribution_timing"] == "end" else 1,
        )

        cfg["contrib_frequency_label"] = st.selectbox(
            "Contribution frequency",
            list(CONTRIB_FREQ_OPTIONS.keys()),
            index=list(CONTRIB_FREQ_OPTIONS.keys()).index(cfg["contrib_frequency_label"]),
            help="Controls how often contributions are deposited (monthly, quarterly, yearly).",
        )

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

        cfg["contributions_per_year"] = int(CONTRIB_FREQ_OPTIONS[cfg["contrib_frequency_label"]])

df = compute_projection(
    int(st.session_state.age_used),
    float(st.session_state.salary_used),
    float(st.session_state.balance_used),
    cfg,
)

annual_return = float(cfg["model_return"])
title_model = cfg["model_name"]
subtitle = f"{title_model} • Assumed return: {_pct(annual_return)}"

with right:
    st.subheader("Projected 401(k) Balance")
    st.caption(subtitle)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["age"],
            y=df["balance"],
            mode="lines",
            line=dict(color=line_color, width=4),
            showlegend=False,
        )
    )

    x_max = df["age"].iloc[-1]
    x_min = df["age"].iloc[0]
    x_padding = 1 if len(df) > 1 else 0.5

    fig.add_trace(
        go.Scatter(
            x=[x_max],
            y=[df["balance"].iloc[-1]],
            mode="markers+text",
            text=[f"${df['balance'].iloc[-1]:,.0f}"],
            textposition="middle left",
            textfont=dict(size=14, color=axis_color),
            marker=dict(color=line_color, size=10),
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

st.space("large")
employee = float(cfg["employee_contrib_rate"])
employer = float(cfg["employer_contrib_rate"])
total_contrib = employee + employer
st.caption(
    "Internal tool. "
    f"Assumes {_pct(float(cfg['salary_growth_rate']))} annual salary growth and {_pct(total_contrib)} annual contribution "
    f"({_pct(employee)} employee, {_pct(employer)} employer). "
    f"Contribution frequency: {cfg['contrib_frequency_label']}. "
    f"Compounding: {int(cfg['compounding_per_year'])}x/year. Contributions deposited at {cfg['contribution_timing']} of period. "
    f"Retirement age: {int(cfg['target_age'])}."
)
