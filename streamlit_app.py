

import math
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="Coast FI Calculator — Zizzi Investments", page_icon="🏝", layout="centered")

# --- Branding ---
BRAND_PRIMARY = "#2F2A26"  # dark charcoal
BRAND_ACCENT  = "#E3B800"  # gold
BRAND_BG      = "#FFFFFF"  # page
BRAND_CARD_BG = "#F7F5F2"  # card

# ---- Header (dark bar so reverse logo is readable) ----
st.markdown(
    f'''
    <div style="background:{BRAND_PRIMARY};padding:16px;border-radius:12px;margin-bottom:16px;">
        <img src="https://zizzi-invest.com/wp-content/uploads/2022/08/Zizzi_Logo_RGB_Reverse-165x48.png" style="height:44px;" alt="Zizzi Investments logo">
    </div>
    ''',
    unsafe_allow_html=True
)

st.title("Coast FI Calculator")
st.caption("Plan your freedom date with Zizzi Investments — see if you can coast to 65 with or without small contributions.")

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
        "- Compute the **target at 65** two ways:\n"
        "  - **Nominal**: Inflate today's spending to age 65, then divide by SWR.\n"
        "  - **Real**: Keep spending in today's dollars and convert your return to a **real** (after-inflation) return.\n"
        "- Turn **Contributions** on to model monthly or annual investing.\n"
        "- Use the modes to solve for the **required return**, the **ending balance**, or the **years needed**."
    )

# --- Inputs ---
st.subheader("Inputs")
left, right = st.columns(2)
with left:
    current_spending = st.number_input("Current Annual Spending ($)", min_value=0.0, value=100000.0, step=1000.0, help="Annual living expenses you'd want to replace in retirement, in today's dollars.")
    inflation_rate = st.number_input("Inflation Rate (%)", min_value=0.0, max_value=15.0, value=2.5, step=0.1, help="Long-run inflation assumption.") / 100.0
    years_until_65 = st.number_input("Years Until Age 65", min_value=0, max_value=60, value=25, step=1, help="Years between now and age 65.")
with right:
    current_portfolio = st.number_input("Current Portfolio Balance ($)", min_value=0.0, value=1000000.0, step=5000.0)
    expected_return_nominal = st.number_input("Expected Annual Return (nominal, %)", min_value=0.0, max_value=20.0, value=6.0, step=0.1) / 100.0
    swr = st.number_input("Safe Withdrawal Rate (%)", min_value=2.0, max_value=6.0, value=4.0, step=0.25) / 100.0

# Target basis
st.subheader("Target basis")
basis = st.radio("How do you want to compute the target at 65?", ["Nominal (inflate spending)", "Real (today's dollars)"], index=0, help="Nominal inflates spending to age 65. Real keeps spending in today's dollars and uses real returns.")

# Contributions
st.subheader("Contributions (optional)")
use_contrib = st.checkbox("Include ongoing contributions", value=False)
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

# Helper functions
def real_return(nominal, infl):
    return (1 + nominal) / (1 + infl) - 1

def fv_with_contrib(pv, r_annual, years, pmt=0.0, freq="Monthly", when="End of period"):
    if years < 0 or r_annual <= -0.999999999:
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
    else:
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
    if pv <= 0 or years <= 0 or target <= 0:
        return float("nan")
    lo, hi = -0.99, 1.0
    def f(r):
        return fv_wrapper(pv, r, years, use_contrib, pmt, freq, when) - target
    f_lo, f_hi = f(lo), f(hi)
    if math.isnan(f_lo) or math.isnan(f_hi) or f_lo * f_hi > 0:
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
        return float("nan")
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

# Target & return per basis
if basis.startswith("Nominal"):
    future_spending = current_spending * ((1 + inflation_rate) ** years_until_65)
    target_balance_at_65 = future_spending / swr if swr > 0 else float("nan")
    r_for_math = expected_return_nominal
else:
    # Real mode: target in today's dollars, use real return
    future_spending = current_spending  # stays in today's dollars
    target_balance_at_65 = current_spending / swr if swr > 0 else float("nan")
    r_for_math = real_return(expected_return_nominal, inflation_rate)

# Main calcs
fv_at_expected = fv_wrapper(current_portfolio, r_for_math, years_until_65, use_contrib, contrib_amount, contrib_freq, contrib_timing)
fv_gap = (target_balance_at_65 - fv_at_expected) if (not math.isnan(target_balance_at_65)) else float("nan")
required_return = solve_required_return(target_balance_at_65, current_portfolio, years_until_65, use_contrib, contrib_amount, contrib_freq, contrib_timing) if years_until_65 > 0 else float("nan")
required_years = solve_years_needed(target_balance_at_65, current_portfolio, r_for_math, use_contrib, contrib_amount, contrib_freq, contrib_timing)

# Solve modes
st.subheader("Choose what to solve for")
mode = st.radio(
    label="Solve for",
    options=("Required Return to Coast", "Ending Balance with Expected Return", "Years Needed at Expected Return"),
    help="We'll always compare to your target at 65 based on the selected basis (Nominal or Real)."
)

# --- Results ---
st.subheader("Results")
st.markdown('<div class="z-card">', unsafe_allow_html=True)

if mode == "Required Return to Coast":
    if math.isnan(required_return):
        st.info("Enter positive values for portfolio, target, and years to calculate the required return (or values may be outside solvable bounds).")
    else:
        label_r = "nominal" if basis.startswith("Nominal") else "real"
        st.write(f"**Required Return to Coast ({label_r}):** {required_return*100:.2f}% annualized")
        st.write(f"**Ending Balance at Your Expected Return ({(expected_return_nominal if basis.startswith('Nominal') else r_for_math)*100:.2f}% {label_r}):** ${fv_at_expected:,.0f}")
        st.write(f"**Target at 65 ({basis.split()[0]} basis):** ${target_balance_at_65:,.0f}")
        if use_contrib and contrib_amount > 0:
            st.caption(f"Including contributions of ${contrib_amount:,.0f} {contrib_freq.lower()} ({contrib_timing.lower()}).")

elif mode == "Ending Balance with Expected Return":
    label_r = "nominal" if basis.startswith("Nominal") else "real"
    st.write(f"**Ending Balance with Expected Return ({(expected_return_nominal if basis.startswith('Nominal') else r_for_math)*100:.2f}% {label_r}):** ${fv_at_expected:,.0f}")
    st.write(f"**Target at 65 ({basis.split()[0]} basis):** ${target_balance_at_65:,.0f}")
    if not math.isnan(fv_gap):
        if fv_gap <= 0:
            st.success("✅ On track (or better) for Coast FI.")
        else:
            st.warning(f"Short of target by about **${fv_gap:,.0f}**.")
    if use_contrib and contrib_amount > 0:
        st.caption(f"Including contributions of ${contrib_amount:,.0f} {contrib_freq.lower()} ({contrib_timing.lower()}).")

elif mode == "Years Needed at Expected Return":
    if math.isnan(required_years):
        st.info("Enter positive values and a valid expected return to calculate years needed (or target may be unattainable within 80 years).")
    else:
        label_r = "nominal" if basis.startswith("Nominal") else "real"
        st.write(f"**Years Needed at {(expected_return_nominal if basis.startswith('Nominal') else r_for_math)*100:.2f}% {label_r}:** {required_years:.1f} years")
        st.write(f"**Target at 65 ({basis.split()[0]} basis):** ${target_balance_at_65:,.0f}")
        if years_until_65 > 0:
            delta = required_years - years_until_65
            if delta <= 0:
                st.success("✅ On your current timeline, you're at or ahead of target.")
            else:
                st.warning(f"You'd need about **{delta:.1f}** more years at this return to hit the target.")
        if use_contrib and contrib_amount > 0:
            st.caption(f"Including contributions of ${contrib_amount:,.0f} {contrib_freq.lower()} ({contrib_timing.lower()}).")

st.markdown("</div>", unsafe_allow_html=True)

# --- Chart: projection ---
if years_until_65 > 0 and current_portfolio > 0:
    st.subheader("Projection to Age 65")
    years = list(range(0, years_until_65 + 1))
    values = [fv_wrapper(current_portfolio, r_for_math, y, use_contrib, contrib_amount, contrib_freq, contrib_timing) for y in years]
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
