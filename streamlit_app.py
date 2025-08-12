
import math
import streamlit as st
import matplotlib.pyplot as plt
from fpdf import FPDF
import tempfile
import os

st.set_page_config(page_title="Coast FI Calculator — Zizzi Investments", page_icon=":desert_island:", layout="centered")

# --- Branding ---
BRAND_PRIMARY = "#2F2A26"
BRAND_ACCENT  = "#E3B800"
BRAND_BG      = "#FFFFFF"
BRAND_CARD_BG = "#F7F5F2"

# ---- Header ----
st.markdown(
    '<div style="background:BRAND_PRIMARY;padding:16px;border-radius:12px;margin-bottom:16px;">'
    '<img src="LOGO_URL" style="height:44px;" alt="Zizzi Investments logo">'
    '</div>'
    .replace("BRAND_PRIMARY", BRAND_PRIMARY)
    .replace("LOGO_URL", "https://zizzi-invest.com/wp-content/uploads/2022/08/Zizzi_Logo_RGB_Reverse-165x48.png"),
    unsafe_allow_html=True
)

st.title("Coast FI Calculator")
st.caption("Plan your freedom date with Zizzi Investments - see if you can coast to 65 with or without small contributions.")

with st.container():
    btn_cols = st.columns([3,1])
    with btn_cols[1]:
        st.link_button("Book a Call", "https://zizzi-invest.com/contact/")

# Styles
st.markdown(
    "<style>"
    ".stApp { background-color: BRAND_BG; }"
    ".z-card {"
        " background: BRAND_CARD_BG;"
        " padding: 1.25rem;"
        " border-radius: 1rem;"
        " border: 1px solid #eae6df;"
    " }"
    "</style>"
    .replace("BRAND_BG", BRAND_BG)
    .replace("BRAND_CARD_BG", BRAND_CARD_BG),
    unsafe_allow_html=True
)

# Inputs
st.subheader("Inputs")
left, right = st.columns(2)
with left:
    current_spending = st.number_input("Current Annual Spending ($)", min_value=0.0, value=100000.0, step=1000.0)
    inflation_rate = st.number_input("Inflation Rate (%)", min_value=0.0, max_value=15.0, value=2.5, step=0.1) / 100.0
    years_until_65 = st.number_input("Years Until Age 65", min_value=0, max_value=60, value=25, step=1)
with right:
    current_portfolio = st.number_input("Current Portfolio Balance ($)", min_value=0.0, value=1000000.0, step=5000.0)
    expected_return_nominal = st.number_input("Expected Annual Return (nominal, %)", min_value=0.0, max_value=20.0, value=6.0, step=0.1) / 100.0
    swr = st.number_input("Safe Withdrawal Rate (%)", min_value=2.0, max_value=6.0, value=4.0, step=0.25) / 100.0

# Target basis
st.subheader("Target basis")
basis = st.radio("How do you want to compute the target at 65?", ["Nominal (inflate spending)", "Real (today's dollars)"], index=0)

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
        contrib_timing = st.selectbox("Timing", ["End of period", "Beginning of period"], index=0)

# Helper functions
def real_return(nominal, infl):
    return (1 + nominal) / (1 + infl) - 1

def fv_with_contrib(pv, r_annual, years, pmt=0.0, freq="Monthly", when="End of period"):
    if years < 0 or r_annual <= -0.999999999:
        return float("nan")
    if freq == "Monthly":
        m = int(round(years * 12))
        r = (1 + r_annual) ** (1/12) - 1
        fv_pv = pv * ((1 + r) ** m)
        fv_pmt = pmt * (((1 + r) ** m) - 1) / (r if r != 0 else 1e-12) * ((1 + r) if when == "Beginning of period" else 1) if pmt > 0 else 0
        return fv_pv + fv_pmt
    else:
        n = int(round(years))
        r = r_annual
        fv_pv = pv * ((1 + r) ** n)
        fv_pmt = pmt * (((1 + r) ** n) - 1) / (r if r != 0 else 1e-12) * ((1 + r) if when == "Beginning of period" else 1) if pmt > 0 else 0
        return fv_pv + fv_pmt

def fv_simple(pv, r_annual, years):
    return pv * ((1 + r_annual) ** years) if years >= 0 else float("nan")

def fv_wrapper(pv, r_annual, years, use_contrib, pmt, freq, when):
    return fv_with_contrib(pv, r_annual, years, pmt, freq, when) if use_contrib and pmt > 0 else fv_simple(pv, r_annual, years)

def solve_required_return(target, pv, years, use_contrib=False, pmt=0.0, freq="Monthly", when="End of period"):
    if pv <= 0 or years <= 0 or target <= 0:
        return float("nan")
    lo, hi = -0.99, 1.0
    def f(r): return fv_wrapper(pv, r, years, use_contrib, pmt, freq, when) - target
    f_lo, f_hi = f(lo), f(hi)
    if f_lo * f_hi > 0: return float("nan")
    for _ in range(80):
        mid = (lo + hi) / 2
        fm = f(mid)
        if abs(fm) < 1e-6: return mid
        if f_lo * fm <= 0:
            hi, f_hi = mid, fm
        else:
            lo, f_lo = mid, fm
    return (lo + hi) / 2

def solve_years_needed(target, pv, r_annual, use_contrib=False, pmt=0.0, freq="Monthly", when="End of period"):
    if pv <= 0 or r_annual <= -0.999999999 or target <= 0:
        return float("nan")
    lo, hi = 0.0, 80.0
    def f(y): return fv_wrapper(pv, r_annual, y, use_contrib, pmt, freq, when) - target
    f_lo, f_hi = f(lo), f(hi)
    if f_lo >= 0: return 0.0
    if f_hi < 0: return float("nan")
    for _ in range(80):
        mid = (lo + hi) / 2
        fm = f(mid)
        if abs(fm) < 1e-2: return mid
        if fm < 0: lo = mid
        else: hi = mid
    return (lo + hi) / 2

# Target & return
if basis.startswith("Nominal"):
    future_spending = current_spending * ((1 + inflation_rate) ** years_until_65)
    target_balance_at_65 = future_spending / swr if swr > 0 else float("nan")
    r_for_math = expected_return_nominal
else:
    future_spending = current_spending
    target_balance_at_65 = current_spending / swr if swr > 0 else float("nan")
    r_for_math = real_return(expected_return_nominal, inflation_rate)

# Calcs
fv_at_expected = fv_wrapper(current_portfolio, r_for_math, years_until_65, use_contrib, contrib_amount, contrib_freq, contrib_timing)
fv_gap = target_balance_at_65 - fv_at_expected
required_return = solve_required_return(target_balance_at_65, current_portfolio, years_until_65, use_contrib, contrib_amount, contrib_freq, contrib_timing)
required_years = solve_years_needed(target_balance_at_65, current_portfolio, r_for_math, use_contrib, contrib_amount, contrib_freq, contrib_timing)

# Solve mode
st.subheader("Choose what to solve for")
mode = st.radio("Solve for", ("Required Return to Coast", "Ending Balance with Expected Return", "Years Needed at Expected Return"))

st.subheader("Results")
st.markdown('<div class="z-card">', unsafe_allow_html=True)

if mode == "Required Return to Coast":
    st.write(f"Required Return to Coast: {required_return*100:.2f}% annualized")
    st.write(f"Future Value at Expected Return: ${fv_at_expected:,.0f}")
    st.write(f"Target at 65: ${target_balance_at_65:,.0f}")

elif mode == "Ending Balance with Expected Return":
    st.write(f"Ending Balance at Expected Return: ${fv_at_expected:,.0f}")
    st.write(f"Target at 65: ${target_balance_at_65:,.0f}")
    if fv_gap <= 0:
        st.success("On track or ahead.")
    else:
        st.warning(f"Short by ${fv_gap:,.0f}")

elif mode == "Years Needed at Expected Return":
    st.write(f"Years Needed: {required_years:.1f}")
    st.write(f"Target at 65: ${target_balance_at_65:,.0f}")

st.markdown("</div>", unsafe_allow_html=True)

# -------- Chart (prettier) --------
chart_path = None
if years_until_65 > 0 and current_portfolio > 0:
    years = list(range(0, years_until_65 + 1))
    values = [fv_wrapper(current_portfolio, r_for_math, y, use_contrib, contrib_amount, contrib_freq, contrib_timing) for y in years]
    target_line = [target_balance_at_65] * len(years)

    st.subheader("Projection to Age 65")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(years, values, label="Projection @ Expected Return", linewidth=2)
    ax.plot(years, target_line, linestyle="--", label="Target at 65", linewidth=2)
    ax.set_xlabel("Years from now")
    ax.set_ylabel("Portfolio value ($)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")
    fig.tight_layout()
    st.pyplot(fig)

    # Save chart to a temporary PNG for PDF export
    tmp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig.savefig(tmp_img.name, dpi=200)
    chart_path = tmp_img.name

# -------- PDF Download (includes chart + disclaimer) --------
st.subheader("Download Results")

def _latin1(s: str) -> str:
    try:
        return s.encode("latin-1", "replace").decode("latin-1")
    except Exception:
        return s

def build_pdf(path_to_chart: str):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, _latin1("Coast FI Calculator - Zizzi Investments"), ln=True)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 8, _latin1(f"Mode: {mode}"), ln=True)
    pdf.cell(0, 8, _latin1(f"Basis: {'Nominal' if basis.startswith('Nominal') else 'Real'}"), ln=True)
    pdf.ln(2)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, _latin1("Inputs"), ln=True)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 7, _latin1(f"Current Spending: ${current_spending:,.0f}"), ln=True)
    pdf.cell(0, 7, _latin1(f"Inflation Rate: {inflation_rate*100:.2f}%"), ln=True)
    pdf.cell(0, 7, _latin1(f"Years Until 65: {years_until_65}"), ln=True)
    pdf.cell(0, 7, _latin1(f"Current Portfolio: ${current_portfolio:,.0f}"), ln=True)
    pdf.cell(0, 7, _latin1(f"Expected Return (nominal): {expected_return_nominal*100:.2f}%"), ln=True)
    pdf.cell(0, 7, _latin1(f"Safe Withdrawal Rate: {swr*100:.2f}%"), ln=True)
    if use_contrib and contrib_amount > 0:
        pdf.cell(0, 7, _latin1(f"Contributions: ${contrib_amount:,.0f} {contrib_freq.lower()} ({contrib_timing.lower()})"), ln=True)

    pdf.ln(2)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, _latin1("Results"), ln=True)
    pdf.set_font("Arial", '', 12)
    if mode == "Required Return to Coast":
        pdf.cell(0, 7, _latin1(f"Required Return to Coast: {required_return*100:.2f}%"), ln=True)
    elif mode == "Ending Balance with Expected Return":
        pdf.cell(0, 7, _latin1(f"Ending Balance @ Expected Return: ${fv_at_expected:,.0f}"), ln=True)
    else:
        pdf.cell(0, 7, _latin1(f"Years Needed @ Expected Return: {required_years:.1f}"), ln=True)
    pdf.cell(0, 7, _latin1(f"Target at 65: ${target_balance_at_65:,.0f}"), ln=True)

    if path_to_chart and os.path.exists(path_to_chart):
        pdf.ln(4)
        pdf.image(path_to_chart, w=180)

    pdf.ln(6)
    pdf.set_font("Arial", 'I', 10)
    pdf.multi_cell(0, 6, _latin1("This calculator is provided for educational purposes only and should not be considered investment, legal, or tax advice. The calculations are based on user-provided assumptions, which may not reflect actual market conditions or your personal situation. Zizzi Investments, LLC makes no guarantee as to the accuracy or completeness of the results and assumes no liability for decisions made based on this information. Please consult a qualified professional before making financial decisions."))
    return pdf

if st.button("Download PDF Report"):
    pdf = build_pdf(chart_path)
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp_file.name)
    with open(tmp_file.name, "rb") as f:
        st.download_button("Click to Download PDF", f, file_name="coast_fi_report.pdf")
    if chart_path and os.path.exists(chart_path):
        os.unlink(chart_path)

# Disclaimer
st.markdown("---")
st.markdown("**Disclaimer:** This calculator is provided for educational purposes only and should not be considered investment, legal, or tax advice. The calculations are based on user-provided assumptions, which may not reflect actual market conditions or your personal situation. Zizzi Investments, LLC makes no guarantee as to the accuracy or completeness of the results and assumes no liability for decisions made based on this information. Please consult a qualified professional before making financial decisions.")
