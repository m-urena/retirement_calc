import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from supabase import create_client, Client
import os
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
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]   # MUST be the secret key

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# --------------------------------------------------
# Company data setup
# --------------------------------------------------
@st.cache_data(show_spinner=False)
def load_company_names():
    """Load normalized plan sponsor names from the data file.

    Falls back to an empty list if the file is missing or unreadable so the UI
    can still operate and present the "My Company Is Not Listed" option.
    """

    base_dir = os.path.dirname(__file__)
    data_dir = os.path.join(base_dir, "Data")
    filename = "AL - ID Skip GA"

    potential_paths = [
        os.path.join(data_dir, f"{filename}{ext}") for ext in (".csv", ".xlsx", ".xls")
    ]

    data_path = next((path for path in potential_paths if os.path.exists(path)), None)
    if not data_path:
        return []

    try:
        if data_path.endswith(".csv"):
            df = pd.read_csv(data_path)
        else:
            df = pd.read_excel(data_path)
    except Exception:
        return []

    target_col = next(
        (col for col in df.columns if col.strip().lower() == "plan sponsor's name".lower()),
        None,
    )
    if not target_col:
        return []

    names = (
        df[target_col]
        .dropna()
        .astype(str)
        .map(str.strip)
        .replace("", pd.NA)
        .dropna()
    )

    normalized = []
    seen = set()
    for name in names:
        display_name = name.title()
        key = display_name.lower()
        if key not in seen:
            normalized.append(display_name)
            seen.add(key)

    normalized.sort()
    return normalized
#----------------------------------------
#Logo
# --------------------------------------------------

logo_path = os.path.join(os.path.dirname(__file__), "bison_logo.png")
with open(logo_path, "rb") as logo_file:
    logo_b64 = base64.b64encode(logo_file.read()).decode()
 
st.markdown(
    f"""
    <div style="
        position: absolute;
        top: 70px;       /* move the logo down (increase this number to go lower) */
        right: 40px;     /* move logo left or right */
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
    if age >= target_age:
        st.warning("Age must be below retirement age to run the projection.")
        return pd.DataFrame({"age": [age], "baseline": [balance], "with_help": [balance]})

    if salary <= 0:
        st.warning("Salary must be greater than 0 to run the projection.")
        return pd.DataFrame({"age": [age], "baseline": [balance], "with_help": [balance]})

    years = target_age - age
    num_points = years + 1

    salary_growth_rate = 0.03
    contribution_rate = 0.078 + 0.046  # employee + employer

    r_no_help = 0.0847
    r_help = r_no_help + 0.0332

    salaries = [salary * ((1 + salary_growth_rate) ** yr) for yr in range(num_points)]
    annual_contribs = [s * contribution_rate for s in salaries]

    def project(start, contribs, rate):
        total = start
        out = [start]
        monthly_rate = (1 + rate) ** (1/12) - 1

        # Closed-form monthly contribution compounding to avoid inner loops
        monthly_factor = (1 + monthly_rate) ** 12
        contrib_multiplier = (monthly_factor - 1) / monthly_rate

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
# Initialize session_state for stored values
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
    not_listed_label = "My Company Is Not Listed"

    age_input = st.number_input("Your Age", min_value=18, max_value=100, value=42)
    salary_str = st.text_input("Current Annual Salary ($)", value="84,000")
    balance_str = st.text_input("Current 401(k) Balance ($)", value="76,500")

    company_query = st.text_input(
        "Company Name",
        placeholder="Start typing to search your company",
    )

    def matching_companies(query: str):
        if not query:
            return company_options[:6]
        lowered = query.lower()
        return [name for name in company_options if lowered in name.lower()][:6]

    filtered_companies = matching_companies(company_query)
    option_list = filtered_companies + [not_listed_label]

    selected_option = st.selectbox(
        "Select a matching company",
        option_list,
        index=None,
        placeholder="Choose a company from the list or confirm it's not listed",
    )

    st.caption(
        "Type your employer's name to see up to six matches. If nothing matches, select "
        f"'{not_listed_label}' to continue."
    )

    if selected_option:
        company_selection = selected_option
    elif company_query:
        exact_match = next(
            (
                name
                for name in company_options
                if name.lower() == company_query.lower()
            ),
            None,
        )
        company_selection = exact_match or not_listed_label
    else:
        company_selection = None

    salary_input = parse_number(salary_str)
    balance_input = parse_number(balance_str)

    
    st.markdown("""
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
        div.stButton > button:first-child:hover {
            background-color: #a76535 !important;
            color: white !important;
        }
        </style>
    """, unsafe_allow_html=True)
    calculate = st.button("Calculate", type="primary")


# --------------------------------------------------
# When user clicks Calculate → freeze values & insert
# --------------------------------------------------
if calculate:

    if salary_input is None or balance_input is None:
        st.warning("Please enter valid salary and balance numbers before calculating.")
    elif company_selection is None:
        st.warning("Please select your company or confirm it is not listed.")
    elif salary_input <= 0:
        st.warning("Salary must be greater than 0 to record a submission.")
    elif balance_input < 0:
        st.warning("Balance cannot be negative.")
    elif age_input >= 65:
        st.warning("Age must be below retirement age to record a submission.")
    else:

        st.session_state.age_used = age_input
        st.session_state.salary_used = salary_input
        st.session_state.balance_used = balance_input
        company_value = company_selection

        supabase.table("submissions").insert({
            "age": age_input,
            "salary": salary_input,
            "balance": balance_input,
            "company": company_value,
            "created_at": datetime.utcnow().isoformat()
        }).execute()

# --------------------------------------------------
# Compute Projection ONLY from stored values
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

    # Baseline Line
    fig.add_trace(go.Scatter(
        x=df["age"], y=df["baseline"],
        mode="lines",
        name="On Your Lonesome (8.5%)",
        line=dict(color="#7D7D7D", width=3),
        hovertemplate="Age %{x}<br>$%{y:,.0f}<extra></extra>"
    ))

    # With Help Line
    fig.add_trace(go.Scatter(
        x=df["age"], y=df["with_help"],
        mode="lines",
        name="With Bison by Your Side (11.8%)",
        line=dict(color="#25385A", width=4),
        hovertemplate="Age %{x}<br>$%{y:,.0f}<extra></extra>"
    ))

    # Label Offsets
    offset_base = df["baseline"].iloc[-1] * 0.04
    offset_help = df["with_help"].iloc[-1] * 0.04

    # Baseline Label
    fig.add_annotation(
        x=df["age"].iloc[-1] + 0.3,
        y=df["baseline"].iloc[-1] + offset_base,
        text=f"${df['baseline'].iloc[-1]:,.0f}",
        showarrow=False,
        font=dict(color="#7D7D7D", size=14)
    )

    # Help Label
    fig.add_annotation(
        x=df["age"].iloc[-1] + 0.3,
        y=df["with_help"].iloc[-1] + offset_help,
        text=f"${df['with_help'].iloc[-1]:,.0f}",
        showarrow=False,
        font=dict(color="#25385A", size=17)
    )

    # Layout
    fig.update_layout(
        height=450,
        margin=dict(l=20, r=20, t=20, b=40),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Montserrat, sans-serif"),
        xaxis=dict(title="Age", fixedrange=True, gridcolor="#E0E0E0"),
        yaxis=dict(title="Portfolio Value ($)", fixedrange=True, gridcolor="#E0E0E0"),
        hovermode="x unified"
    )

    # Disable zoom/pan
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    fig.update_layout(dragmode=False)

    st.plotly_chart(fig, use_container_width=True)


# --------------------------------------------------
# CTA Section
# --------------------------------------------------
final_diff = df["with_help"].iloc[-1] - df["baseline"].iloc[-1]

st.markdown(
    f"""
    <div style="text-align:center; font-size:26px; margin-top:20px; font-weight:400;">
        Is <span style="font-weight:700; color:#25385A;">${final_diff:,.0f}</span> worth 30 minutes of your time?
    </div>
    """,
    unsafe_allow_html=True
)


# Determine Calendly link based on company selection
DEFAULT_CALENDLY = "https://calendly.com/placeholder"
ALT_CALENDLY = "https://calendly.com/placeholder-not-listed"

company_for_routing = company_selection or not_listed_label
normalized_company = company_for_routing.strip().lower()
calendly_link = (
    ALT_CALENDLY
    if normalized_company == "my company is not listed".lower()
    else DEFAULT_CALENDLY
)

st.markdown(
    """
    <div style="text-align:center; margin-top:20px;">
        <a href="{calendly_link}" target="_blank"
           style="background-color:#C17A49; color:white; padding:14px 28px;
                  text-decoration:none; border-radius:8px; font-size:18px;">
           Schedule a Conversation
        </a>
    </div>
    """.format(calendly_link=calendly_link),
    unsafe_allow_html=True,
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
