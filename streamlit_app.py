
import math
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="Coast FI Calculator — Zizzi Investments", page_icon="🏝", layout="centered")

import math
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="Coast FI Calculator — Zizzi Investments", page_icon="🏝", layout="centered")

# --- Branding ---
BRAND_PRIMARY = "#2F2A26"
BRAND_ACCENT  = "#E3B800"
BRAND_BG      = "#FFFFFF"
BRAND_CARD_BG = "#F7F5F2"

# Header with logo & title
cols = st.columns([1,3])
with cols[0]:
    st.image("https://zizzi-invest.com/wp-content/uploads/2022/08/Zizzi_Logo_RGB_Reverse-165x48.png", use_column_width=True)
with cols[1]:
    st.title("Coast FI Calculator")
    st.caption("Plan your freedom date with Zizzi Investments — find out if you can coast to 65 without (or with light) contributions.")

# Header action buttons
with st.container():
    btn_cols = st.columns([3,1])
    with btn_cols[1]:
        st.link_button("Book a Call", "https://zizzi-invest.com/contact/")

# Styles
st.markdown(
    """
    <style>
    .stApp { background-color: BRAND_BG; }
    .z-card {
        background: BRAND_CARD_BG;
        padding: 1.25rem;
        border-radius: 1rem;
        border: 1px solid #eae6df;
    }
    </style>
    """
    .replace("BRAND_BG", BRAND_BG)
    .replace("BRAND_CARD_BG", BRAND_CARD_BG),
    unsafe_allow_html=True
)

st.markdown("#### How it works")
with st.expander("A quick primer (click to open)"):
    st.write(
        "- **Coast FI** means your current nest egg can grow to the amount you'll need at 65 with minimal or no further contributions.\n"
        "- We compute your **target balance at 65** from your spending (inflation-adjusted) and a **safe withdrawal rate**.\n"
        "- Turn **Contributions** on to model monthly or annual investing.\n"
        "- Choose a mode to solve for the **required return**, the **ending balance**, or the **years needed**."
    )

# --- Inputs ---
st.subheader("Inputs")
left, right = st.columns(2)
with left:
    current_spending = st.number_input("Current Annual Spending ($)", min_value=0.0, value=60000.0, step=1000.0, help="Annual living expenses you'd want to replace in retirement, in today's dollars.")
    inflation_rate = st.number_input("Inflation Rate (%)", min_value=0.0, max_value=15.0, value=2.5, step=0.1, help="Long-run inflation assumption.") / 100.0
    years_until_65 = st.number_input("Years Until Age 65", min_value=0, max_value=60, value=25, step=1, help="Years between now and age 65.")
with right:
    current_portfolio = st.number_input("Current Portfolio Balance ($)", min_value=0.0, value=300000.0, step=5000.0)
    expected_return = st.number_input("Expected Annual Return (%)", min_value=0.0, max_value=20.0, value=6.0, step=0.1) / 100.0
    swr = st.number_input("Safe Withdrawal Rate (%)", min_value=2.0, max_value=6.0, value=4.0, step=0.25) / 100.0

# Contributions toggle
st.subheader("Contributions (optional)")
use_contrib = st.checkbox("Include ongoing contributions", value=False, help="Model light contributions while 'coasting'.")
contrib_amount = 0.0
contrib_freq = "Monthly"
contrib_timing = "End of period"
if use_contrib:
    c1, c2, c3 = st.columns([1.2,1,1.2])
    with c1:
        contrib_amount = st.number_input("Contribution Amount ($)", min_value=0.0, value=500.0, step=50.0)
    with c2:
        contrib_freq = st.selectbox("Frequency", ["Monthly", "Annual"], index=0)
    with c3:
        contrib_timing = st.selectbox("Timing", ["End of period", "Beginning of period"], index=0, help="Beginning applies one extra period of growth to each deposit.")

# Derived targets
future_spending = current_spending * ((1 + inflation_rate) ** years_until_65)
target_balance_at_65 = future_spending / swr if swr > 0 else float("nan")

# --- Mode selection ---
st.subheader("Choose what to solve for")
mode = st.radio(
    label="Solve for",
    options=(
        "Required Return to Coast",
        "Ending Balance with Expected Return",
        "Years Needed at Expected Return"
    ),
    help="Pick one focus. We'll still show comparisons to your spending-based target."
)

def fv_with_contrib(pv, r_annual, years, pmt=0.0, freq="Monthly", when="End of period"):
    """Future value with optional contributions.
    pv: present value (current_portfolio)
    r_annual: annual return as decimal
    years: number of years
    pmt: contribution per period (monthly or annual depending on freq)
    freq: 'Monthly' or 'Annual'
    when: 'End of period' or 'Beginning of period'
    """
    if years < 0:
        return float("nan")
    if r_annual <= -0.999999999:
        return float("nan")
    if freq == "Monthly":
        m = int(round(years * 12))
        r = (1 + r_annual) ** (1/12) - 1  # effective monthly
        fv_pv = pv * ((1 + r) ** m)
        if pmt > 0 and m > 0:
            factor = (((1 + r) ** m) - 1) / (r if r != 0 else 1e-12)
            if when == "Beginning of period":
                factor *= (1 + r)
            fv_pmt = pmt * factor
        else:
            fv_pmt = 0.0
        return fv_pv + fv_pmt
    else:  # Annual
        n = int(round(years))
        r = r_annual
        fv_pv = pv * ((1 + r) ** n)
        if pmt > 0 and n > 0:
            factor = (((1 + r) ** n) - 1) / (r if r != 0 else 1e-12)
            if when == "Beginning of period":
                factor *= (1 + r)
            fv_pmt = pmt * factor
        else:
            fv_pmt = 0.0
        return fv_pv + fv_pmt

def fv_simple(pv, r_annual, years):
    return pv * ((1 + r_annual) ** years) if years >= 0 else float("nan")

def fv_wrapper(pv, r_annual, years, use_contrib, pmt, freq, when):
    if use_contrib and pmt > 0:
        return fv_with_contrib(pv, r_annual, years, pmt, freq, when)
    else:
        return fv_simple(pv, r_annual, years)

def solve_required_return(target, pv, years, use_contrib=False, pmt=0.0, freq="Monthly", when="End of period"):
    """Find annual return r so that FV == target. Uses bisection on r in [-0.99, 1.0] (i.e., -99% to +100%)."""
    if pv <= 0 or years <= 0 or target <= 0:
        return float("nan")
    lo, hi = -0.99, 1.0
    def f(r):
        return fv_wrapper(pv, r, years, use_contrib, pmt, freq, when) - target
    f_lo, f_hi = f(lo), f(hi)
    if math.isnan(f_lo) or math.isnan(f_hi):
        return float("nan")
    # Ensure sign change; if not, return NaN to indicate outside bounds
    if f_lo * f_hi > 0:
        return float("nan")
    for _ in range(80):
        mid = (lo + hi) / 2
        fm = f(mid)
        if abs(fm) < 1e-6:
            return mid
        if f_lo * fm <= 0:
            hi, f_hi = mid, fm
        else:
            lo, f_lo = mid, fm
    return (lo + hi) / 2

def solve_years_needed(target, pv, r_annual, use_contrib=False, pmt=0.0, freq="Monthly", when="End of period"):
    """Find years so that FV == target at given r. Bisection on years in [0, 80]."""
    if pv <= 0 or r_annual <= -0.999999999 or target <= 0:
        return float("nan")
    lo, hi = 0.0, 80.0
    def f(y):
        return fv_wrapper(pv, r_annual, y, use_contrib, pmt, freq, when) - target
    f_lo, f_hi = f(lo), f(hi)
    if math.isnan(f_lo) or math.isnan(f_hi):
        return float("nan")
    if f_lo >= 0:
        return 0.0
    if f_hi < 0:
        return float("nan")  # even after 80 years not enough
    for _ in range(80):
        mid = (lo + hi) / 2
        fm = f(mid)
        if abs(fm) < 1e-2:
            return mid
        if fm < 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2

# Calculations
fv_at_expected = fv_wrapper(current_portfolio, expected_return, years_until_65, use_contrib, contrib_amount, contrib_freq, contrib_timing)
fv_gap = (target_balance_at_65 - fv_at_expected) if (not math.isnan(target_balance_at_65)) else float("nan")
required_return = solve_required_return(target_balance_at_65, current_portfolio, years_until_65, use_contrib, contrib_amount, contrib_freq, contrib_timing) if years_until_65 > 0 else float("nan")
required_years = solve_years_needed(target_balance_at_65, current_portfolio, expected_return, use_contrib, contrib_amount, contrib_freq, contrib_timing)

# --- Results ---
st.subheader("Results")
st.markdown('<div class="z-card">', unsafe_allow_html=True)

if mode == "Required Return to Coast":
    if math.isnan(required_return):
        st.info("Enter positive values for portfolio, target, and years to calculate the required return (or values may be outside solvable bounds).")
    else:
        st.write(f"**Required Return to Coast:** {required_return*100:.2f}% annualized")
        st.write(f"**Future Value at Your Expected Return ({expected_return*100:.2f}%):** ${fv_at_expected:,.0f}")
        st.write(f"**Target at 65 (from spending & SWR):** ${target_balance_at_65:,.0f}")
        if use_contrib and contrib_amount > 0:
            st.caption(f"Including contributions of ${contrib_amount:,.0f} {contrib_freq.lower()} ({contrib_timing.lower()}).")

elif mode == "Ending Balance with Expected Return":
    st.write(f"**Ending Balance with Expected Return ({expected_return*100:.2f}%):** ${fv_at_expected:,.0f}")
    st.write(f"**Target at 65 (from spending & SWR):** ${target_balance_at_65:,.0f}")
    if not math.isnan(fv_gap):
        if fv_gap <= 0:
            st.success("✅ At your expected return, you're on track (or better) for Coast FI.")
        else:
            st.warning(f"Short of target by about **${fv_gap:,.0f}**.")
    if use_contrib and contrib_amount > 0:
        st.caption(f"Including contributions of ${contrib_amount:,.0f} {contrib_freq.lower()} ({contrib_timing.lower()}).")

elif mode == "Years Needed at Expected Return":
    if math.isnan(required_years):
        st.info("Enter positive values and a non-zero expected return to calculate years needed (or target may be unattainable within 80 years).")
    else:
        st.write(f"**Years Needed at {expected_return*100:.2f}%:** {required_years:.1f} years")
        st.write(f"**Target at 65 (from spending & SWR):** ${target_balance_at_65:,.0f}")
        if years_until_65 > 0:
            delta = required_years - years_until_65
            if delta <= 0:
                st.success("✅ On your current timeline, you're at or ahead of target.")
            else:
                st.warning(f"You'd need about **{delta:.1f}** more years at this return to hit the target.")
        if use_contrib and contrib_amount > 0:
            st.caption(f"Including contributions of ${contrib_amount:,.0f} {contrib_freq.lower()} ({contrib_timing.lower()}).")

st.markdown("</div>", unsafe_allow_html=True)

# --- Chart: growth vs. target ---
# Build a yearly projection line using the same math (monthly/annual as chosen)
if years_until_65 > 0 and current_portfolio > 0:
    st.subheader("Projection to Age 65")
    years = list(range(0, years_until_65 + 1))
    values = []
    for y in years:
        values.append(fv_wrapper(current_portfolio, expected_return, y, use_contrib, contrib_amount, contrib_freq, contrib_timing))
    target_line = [target_balance_at_65 for _ in years]

    fig, ax = plt.subplots()
    ax.plot(years, values, label="Projection @ Expected Return")
    ax.plot(years, target_line, linestyle="--", label="Target at 65")
    ax.set_xlabel("Years from now")
    ax.set_ylabel("Portfolio value ($)")
    ax.legend(loc="best")
    st.pyplot(fig)

st.divider()
st.write("Questions or want help dialing in the assumptions? [Contact us](https://zizzi-invest.com/contact/).")

# --- Branding (adjust hex codes later if needed) ---
BRAND_PRIMARY = "#2F2A26"   # dark charcoal (adjust to match brand)
BRAND_ACCENT  = "#E3B800"   # gold accent (adjust to match brand)
BRAND_BG      = "#FFFFFF"
BRAND_CARD_BG = "#F7F5F2"

# Header with logo & title
cols = st.columns([1,3])
with cols[0]:
    st.image("https://zizzi-invest.com/wp-content/uploads/2022/08/Zizzi_Logo_RGB_Reverse-165x48.png", use_column_width=True)
with cols[1]:
    st.title("Coast FI Calculator")
    st.caption("Plan your freedom date with Zizzi Investments — find out if you can coast to 65 without new contributions.")

# Header action buttons
with st.container():
    btn_cols = st.columns([3,1])
    with btn_cols[1]:
        st.link_button("Book a Call", "https://zizzi-invest.com/contact/")


st.markdown(
    """
    <style>
    .stApp {
        background-color: BRAND_BG;
    }
    .z-card {
        background: BRAND_CARD_BG;
        padding: 1.25rem;
        border-radius: 1rem;
        border: 1px solid #eae6df;
    }
    .metric-good { color: #1a7f37; font-weight: 600; }
    .metric-warn { color: #b43c00; font-weight: 600; }
    .metric-need { color: #8a1c1c; font-weight: 600; }
    a, .stButton>button { background: BRAND_PRIMARY; border-color: BRAND_PRIMARY; }
    </style>
    """
    .replace("BRAND_BG", BRAND_BG)
    .replace("BRAND_CARD_BG", BRAND_CARD_BG)
    .replace("BRAND_PRIMARY", BRAND_PRIMARY),
    unsafe_allow_html=True
)

st.markdown("#### How it works")
with st.expander("A quick primer (click to open)"):
    st.write(
        "- **Coast FI** means your current nest egg can grow, without new contributions, to the amount you'll need at 65.\n"
        "- We compare the **future value (FV)** of your current portfolio to the **target** you say you'll need at 65 (often spending ÷ 4%).\n"
        "- We also solve for the **exact return required** to coast from where you are today."
    )

# --- Inputs ---
with st.container():
    st.subheader("Inputs")
    left, right = st.columns(2)
    with left:
        current_spending = st.number_input("Current Annual Spending ($)", min_value=0.0, value=60000.0, step=1000.0, help="Annual living expenses you'd want to replace in retirement, in today's dollars.")
        inflation_rate = st.number_input("Inflation Rate (%)", min_value=0.0, max_value=15.0, value=2.5, step=0.1, help="Long-run inflation assumption.") / 100.0
        years_until_65 = st.number_input("Years Until Age 65", min_value=0, max_value=60, value=25, step=1, help="Years between now and age 65.")
    with right:
        current_portfolio = st.number_input("Current Portfolio Balance ($)", min_value=0.0, value=300000.0, step=5000.0)
        needed_balance_at_65 = st.number_input("Needed Portfolio at 65 ($)", min_value=0.0, value=1500000.0, step=5000.0, help="Your target portfolio at 65 (e.g., spending ÷ 0.04 for a 4% rule).")
        expected_return = st.number_input("Expected Annual Return (%)", min_value=0.0, max_value=20.0, value=6.0, step=0.1) / 100.0

# --- Calculations ---
def compute_results(current_spending, inflation_rate, current_portfolio, years_until_65, needed_balance_at_65, expected_return):
    # Inflation-adjusted spending at 65 (for info only)
    future_spending = current_spending * ((1 + inflation_rate) ** years_until_65)
    # FV with expected return
    fv_portfolio = current_portfolio * ((1 + expected_return) ** years_until_65) if years_until_65 > 0 else current_portfolio
    # Required return to exactly hit target
    if current_portfolio > 0 and years_until_65 > 0 and needed_balance_at_65 > 0:
        required_return = (needed_balance_at_65 / current_portfolio) ** (1.0 / years_until_65) - 1.0
    else:
        required_return = float("nan")
    coast_fi_reached = fv_portfolio >= needed_balance_at_65 if needed_balance_at_65 > 0 else False
    return future_spending, fv_portfolio, required_return, coast_fi_reached

future_spending, fv_portfolio, required_return, coast_fi_reached = compute_results(
    current_spending, inflation_rate, current_portfolio, years_until_65, needed_balance_at_65, expected_return
)

# --- Results ---
st.subheader("Results")
res_cols = st.columns(2)
with res_cols[0]:
    st.markdown('<div class="z-card">', unsafe_allow_html=True)
    st.markdown(f"**Future Spending at 65 (inflation-adjusted):** ${{future_spending:,.2f}}")
    st.markdown(f"**Future Value of Portfolio @ Expected Return:** ${{fv_portfolio:,.2f}}")
    st.markdown(f"**Needed Portfolio @ 65:** ${{needed_balance_at_65:,.2f}}")
    if not math.isnan(required_return):
        st.markdown(f"**Required Return to Coast:** {{required_return*100:.2f}}%")
    else:
        st.markdown("**Required Return to Coast:** —")
    st.markdown("</div>", unsafe_allow_html=True)

with res_cols[1]:
    # Status message
    st.markdown('<div class="z-card">', unsafe_allow_html=True)
    if needed_balance_at_65 <= 0 or current_portfolio <= 0 or years_until_65 == 0:
        st.info("Enter positive values for current portfolio, years until 65, and needed balance to calculate Coast FI status.")
    else:
        if coast_fi_reached:
            st.success("✅ You're at **Coast FI** — your current portfolio can grow to your target by 65 without new contributions.")
        else:
            gap = needed_balance_at_65 - fv_portfolio
            if gap <= 0:
                st.success("✅ You're at **Coast FI**.")
            else:
                st.warning(f"You're **not there yet**. Short by about **${{gap:,.0f}}** at your expected return.")
                if not math.isnan(required_return):
                    st.caption(f"You'd need about **{{required_return*100:.2f}}%** annualized from here to coast.")
    st.markdown("</div>", unsafe_allow_html=True)

# --- Chart: growth vs. target ---
if years_until_65 > 0 and current_portfolio > 0:
    st.subheader("Projection to Age 65")
    years = list(range(0, years_until_65 + 1))
    values_expected = [current_portfolio * ((1 + expected_return) ** y) for y in years]
    target_line = [needed_balance_at_65 for _ in years]

    fig, ax = plt.subplots()
    ax.plot(years, values_expected, label="FV @ Expected Return")
    ax.plot(years, target_line, linestyle="--", label="Target at 65")
    ax.set_xlabel("Years from now")
    ax.set_ylabel("Portfolio value ($)")
    ax.legend(loc="best")
    st.pyplot(fig)

st.divider()
st.write("Questions or want help dialing in the assumptions? [Contact us](https://zizzi-invest.com/contact/).")
