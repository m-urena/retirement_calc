import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from PIL import Image
import os

# ==========================================================
# PAGE CONFIG
# ==========================================================
st.set_page_config(
    page_title="Bison Wealth | 401(k) Growth Simulator",
    page_icon="🦬",
    layout="wide"
)

# ==========================================================
# GLOBAL CSS — PROFESSIONAL COMPACT LOOK
# ==========================================================
st.markdown("""
<style>

    /* Reduce padding to eliminate vertical scrolling */
    .block-container {
        padding-top: 1rem !important;
        max-width: 1500px !important;
    }

    /* Card container */
    .card {
        background-color: #F7F8FA;
        border-radius: 12px;
        padding: 20px 25px;
        border: 1px solid #E0E0E0;
        margin-bottom: 18px;
    }

    /* Tight spacing between Streamlit elements */
    .element-container {
        margin-bottom: 0.4rem !important;
    }

    /* Clean section title */
    .section-title {
        font-size: 20px;
        font-weight: 700;
        margin-bottom: 0.3rem;
        color: #25385A;
    }

    /* Inputs look cleaner */
    input[type="text"], input[type="number"] {
        height: 42px !important;
        border-radius: 8px !important;
    }

</style>
""", unsafe_allow_html=True)


# ==========================================================
# LOGO + HEADER
# ==========================================================
logo_path = "Bison Wealth Logo.png"
if os.path.exists(logo_path):
    st.image(logo_path, width=200)

st.markdown("<h1 style='margin-bottom:0px;'>Bison Wealth 401(k) Growth Simulator</h1>", unsafe_allow_html=True)
st.write("Visualize how your 401(k) could grow **with and without Bison’s guidance.**")


# ==========================================================
# INPUT CARD — AGE, SALARY, BALANCE (Horizontal 3 columns)
# ==========================================================
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>Your Information</div>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

age = col1.number_input("Your Age", min_value=18, max_value=120, value=35, step=1)
salary_str = col2.text_input("Current Annual Salary ($)", value="100,000")
balance_str = col3.text_input("Current 401(k) Balance ($)", value="200,000")

st.markdown("</div>", unsafe_allow_html=True)


# --------------------------------------------------
# PARSE NUMERIC INPUTS
# --------------------------------------------------
def parse_number(x):
    try:
        return float(x.replace(",", "").strip())
    except:
        return None

balance = parse_number(balance_str)
salary = parse_number(salary_str)


# ==========================================================
# RUN CALCULATIONS IF INPUTS PRESENT
# ==========================================================
if balance and salary:

    target_age = 65
    years = max(0, target_age - age)

    salary_growth_rate = 0.03
    employee_contrib = 0.078
    employer_contrib = 0.046
    contribution_rate = employee_contrib + employer_contrib

    # STATIC RETURNS
    non_help_rate = 0.0847
    help_rate = non_help_rate + 0.0332

    salaries = [salary * ((1 + salary_growth_rate) ** yr) for yr in range(years + 1)]
    annual_contribs = [s * contribution_rate for s in salaries]

    # MONTHLY COMPOUNDING MODEL
    def growth_projection_monthly(start_balance, annual_contribs, annual_rate):
        total = start_balance
        values = [start_balance]
        monthly_rate = (1 + annual_rate) ** (1 / 12) - 1
        for yearly_contrib in annual_contribs:
            monthly_contrib = yearly_contrib / 12
            for _ in range(12):
                total = total * (1 + monthly_rate) + monthly_contrib
            values.append(total)
        return values

    baseline = growth_projection_monthly(balance, annual_contribs, non_help_rate)
    with_help = growth_projection_monthly(balance, annual_contribs, help_rate)

    ages = list(range(age, target_age + 1))
    final_lonesome_val = baseline[-1]
    final_help_val = with_help[-1]
    difference = final_help_val - final_lonesome_val


    # ==========================================================
    # CHART DESIGN
    # ==========================================================
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ages, y=baseline,
        mode="lines",
        name=f"On Your Lonesome ({non_help_rate*100:.1f}%)",
        line=dict(color="#7D7D7D", width=3)
    ))

    fig.add_trace(go.Scatter(
        x=ages, y=with_help,
        mode="lines",
        name=f"With Bison by Your Side ({help_rate*100:.1f}%)",
        line=dict(color="#25385A", width=6)
    ))

    # END LABELS
    fig.add_annotation(
        x=ages[-1] - 0.6, y=baseline[-1],
        text=f"${baseline[-1]:,.0f}",
        showarrow=False,
        font=dict(color="#7D7D7D", size=13),
        xanchor="right", yanchor="middle"
    )

    fig.add_annotation(
        x=ages[-1] - 0.6, y=with_help[-1],
        text=f"${with_help[-1]:,.0f}",
        showarrow=False,
        font=dict(color="#25385A", size=16),
        xanchor="right", yanchor="middle"
    )

    fig.update_layout(
        title="Estimated 401(k) Growth",
        title_font=dict(color="#414546", size=20),
        paper_bgcolor="white",
        plot_bgcolor="white",
        xaxis=dict(title="Age", color="#414546", gridcolor="#E0E0E0", range=[age, 67]),
        yaxis=dict(title="Portfolio Value ($)", color="#414546", gridcolor="#E0E0E0"),
        legend=dict(bgcolor="white", font=dict(color="#414546")),
        hovermode="x unified",
        margin=dict(l=20, r=20, t=40, b=20),
        height=430,
    )


    # ==========================================================
    # CHART + METRICS IN ONE CARD (Horizontal Layout)
    # ==========================================================
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Estimated 401(k) Growth</div>", unsafe_allow_html=True)

    left, right = st.columns([4, 1])

    with left:
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.markdown(f"""
            <div style="background-color:#FFFFFF; border:1px solid #D7D7D7;
                        padding:18px; border-radius:10px; text-align:center;">
                <p style="color:#414546; margin:0; font-weight:600;">On Your Lonesome</p>
                <p style="font-size:26px; color:#7D7D7D; margin-top:0;">${final_lonesome_val:,.0f}</p>

                <p style="color:#414546; margin:0; font-weight:600;">With Bison by Your Side</p>
                <p style="font-size:26px; color:#25385A; font-weight:700; margin-top:0;">
                    ${final_help_val:,.0f}
                </p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


    # ==========================================================
    # CTA SECTION
    # ==========================================================
    st.markdown(f"""
    <div style="text-align:center; margin-top:10px; margin-bottom:20px;">
        <p style="font-size:18px; color:#414546;">
            Is <span style="color:#25385A; font-weight:700;">${difference:,.0f}</span>
            worth 30 minutes of your time?
        </p>
        <a href="https://calendly.com/placeholder-link" target="_blank"
           style="background-color:#25385A; color:white; padding:12px 28px;
                  text-decoration:none; border-radius:8px; font-weight:600;">
           Schedule a Conversation
        </a>
    </div>
    """, unsafe_allow_html=True)


    # ==========================================================
    # DISCLOSURE
    # ==========================================================
    st.caption("""
For illustrative purposes only. Assumes 3% annual salary growth and 12.4% of salary contributed annually
(7.8% employee, 4.6% employer). Compounded monthly.

Performance without help is the 5yr annualized return of the S&P Target Date 2035 Index as of 12/04/2025.
With help is bumped up by 3.32% because of the Hewitt Study.
""")

else:
    st.info("Please enter your age, salary, and 401(k) balance to generate your projection.")

