
import math
import streamlit as st
import matplotlib.pyplot as plt
from fpdf import FPDF  # fpdf2
import tempfile
import os
import numpy as np

st.set_page_config(page_title="Coast FI Calculator — Zizzi Investments", page_icon=":desert_island:", layout="centered")

# --- Branding ---
BRAND_PRIMARY = "#2F2A26"
BRAND_ACCENT  = "#E3B800"
BRAND_BG      = "#FFFFFF"
BRAND_CARD_BG = "#F7F5F2"

# ---- Header & Fonts ----
st.markdown(
    '<link href="https://fonts.googleapis.com/css2?family=Archivo+Expanded:wght@500;600&family=Source+Sans+3:wght@400;600&family=Source+Serif+4:wght@600&display=swap" rel="stylesheet">'
    '<style>'
    'h1, h2, h3 { font-family: "Source Serif 4", serif; font-weight: 600; }'
    '.subhead, label, .stButton button, .stRadio, .stSelectbox, .stSlider, .stNumberInput { font-family: "Archivo Expanded", sans-serif; }'
    'body, .stApp, .stMarkdown, .stCaption, .stText, .stDataFrame, .z-card { font-family: "Source Sans 3", sans-serif; }'
    '</style>',
    unsafe_allow_html=True
)

st.markdown(
    '<div style="background:{BRAND_PRIMARY};padding:16px;border-radius:12px;margin-bottom:16px;">'
    '<img src="https://zizzi-invest.com/wp-content/uploads/2022/08/Zizzi_Logo_RGB_Reverse-165x48.png" style="height:44px;" alt="Zizzi Investments logo">'
    '</div>'
    .replace("{BRAND_PRIMARY}", BRAND_PRIMARY),
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
    ".stApp { background-color: {BRAND_BG}; }"
    ".z-card {"
        " background: {BRAND_CARD_BG};"
        " padding: 1.25rem;"
        " border-radius: 1rem;"
        " border: 1px solid #eae6df;"
    " }"
    ".mli-score { font-size: 1.1rem; font-weight: 600; }"
    ".legend-badge { display:inline-block; padding:4px 8px; border-radius:8px; margin-right:6px; border:1px solid #ddd; }"
    "</style>"
    .replace("{BRAND_BG}", BRAND_BG)
    .replace("{BRAND_CARD_BG}", BRAND_CARD_BG),
    unsafe_allow_html=True
)

# =============================================================
# Inputs
# =============================================================
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

# =============================================================
# Helper functions
# =============================================================
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

# =============================================================
# Target & return
# =============================================================
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

# =============================================================
# Solve mode
# =============================================================
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

# =============================================================
# Projection Chart
# =============================================================
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

    # Save chart image for PDF
    tmp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig.savefig(tmp_img.name, dpi=200)
    chart_path = tmp_img.name

# =============================================================
# Margin Lifestyle Index (MLI) - Qualitative Sliders
# =============================================================
st.subheader("Margin Lifestyle Index (Qualitative)")
st.markdown("The goal of **Coast FI** is to create more *margin* so you can invest energy into the rest of your life — relationships, purpose, health, and peace of mind.")

st.caption("Each slider is 0–20. Total score is out of 100.")
# Legend for ranges
st.markdown('<div class="z-card"><span class="legend-badge">0–39: Needs Attention</span><span class="legend-badge">40–69: Developing</span><span class="legend-badge">70–100: Strong</span></div>', unsafe_allow_html=True)

mli_cols = st.columns(2)
with mli_cols[0]:
    mli_emotional = st.slider("Emotional / Spiritual", 0, 20, 10, help="Sense of calm, meaning, resilience, and joy. Do you feel centered day-to-day?")
    mli_relationships = st.slider("Strength of Relationships", 0, 20, 10, help="Connection with partner, family, friends, and community. Do you feel supported and present?")
    mli_physical = st.slider("Physical Health / Fitness", 0, 20, 10, help="Sleep quality, energy, nutrition, and movement. Are your habits serving you?")
with mli_cols[1]:
    mli_purpose = st.slider("Current Work / Purpose", 0, 20, 10, help="Does your work feel meaningful? Do you have autonomy and time for pursuits that matter?")
    mli_finances = st.slider("Overall Feeling about Finances", 0, 20, 10, help="Stress level, clarity of plan, and confidence. Do you feel in control?")

mli_scores = {
    "Emotional/Spiritual": mli_emotional,
    "Relationships": mli_relationships,
    "Physical": mli_physical,
    "Work/Purpose": mli_purpose,
    "Finances": mli_finances,
}
mli_total = sum(mli_scores.values())

# Qualitative interpretation
if mli_total < 40:
    mli_label = "Needs Attention"
elif mli_total < 70:
    mli_label = "Developing"
else:
    mli_label = "Strong"

st.markdown(f'<div class="z-card"><span class="mli-score">Your Margin Lifestyle Index: {mli_total} / 100 — {mli_label}</span></div>', unsafe_allow_html=True)

# Radar chart for MLI
mli_chart_path = None
labels = list(mli_scores.keys())
values = list(mli_scores.values())
angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist()
values_cycle = values + values[:1]
angles_cycle = angles + angles[:1]

fig2 = plt.figure(figsize=(5, 5))
ax2 = fig2.add_subplot(111, polar=True)
ax2.plot(angles_cycle, values_cycle, linewidth=2)
ax2.fill(angles_cycle, values_cycle, alpha=0.15)
ax2.set_xticks(angles)
ax2.set_xticklabels(labels)
ax2.set_yticks([5,10,15,20])
ax2.set_ylim(0,20)
fig2.tight_layout()
st.pyplot(fig2)

tmp_img2 = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
fig2.savefig(tmp_img2.name, dpi=200)
mli_chart_path = tmp_img2.name

# =============================================================
# PDF Download (Unicode fonts embedded with fpdf2, includes both charts + disclaimer)
# =============================================================
st.subheader("Download Results")

def build_pdf(path_to_chart: str, path_to_mli: str):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    # Register DejaVu fonts (bundled in ./fonts); fall back to core if not found
    try:
        pdf.add_font("DejaVu", "", "fonts/DejaVuSans.ttf", uni=True)
        pdf.add_font("DejaVu", "B", "fonts/DejaVuSans-Bold.ttf", uni=True)
        fam_regular = ("DejaVu", "", 12)
        fam_bold = ("DejaVu", "B", 12)
        fam_title = ("DejaVu", "B", 16)
        fam_small = ("DejaVu", "", 10)
    except Exception:
        fam_regular = ("Arial", "", 12)
        fam_bold = ("Arial", "B", 12)
        fam_title = ("Arial", "B", 16)
        fam_small = ("Arial", "", 10)

    pdf.add_page()
    pdf.set_font(*fam_title)
    pdf.cell(0, 10, "Coast FI Calculator - Zizzi Investments", ln=True)
    pdf.set_font(*fam_regular)
    pdf.cell(0, 8, f"Mode: {mode}", ln=True)
    pdf.cell(0, 8, f"Basis: {'Nominal' if basis.startswith('Nominal') else 'Real'}", ln=True)
    pdf.ln(2)
    pdf.set_font(*fam_bold)
    pdf.cell(0, 8, "Inputs", ln=True)
    pdf.set_font(*fam_regular)
    pdf.cell(0, 7, f"Current Spending: ${current_spending:,.0f}", ln=True)
    pdf.cell(0, 7, f"Inflation Rate: {inflation_rate*100:.2f}%", ln=True)
    pdf.cell(0, 7, f"Years Until 65: {years_until_65}", ln=True)
    pdf.cell(0, 7, f"Current Portfolio: ${current_portfolio:,.0f}", ln=True)
    pdf.cell(0, 7, f"Expected Return (nominal): {expected_return_nominal*100:.2f}%", ln=True)
    pdf.cell(0, 7, f"Safe Withdrawal Rate: {swr*100:.2f}%", ln=True)
    if use_contrib and contrib_amount > 0:
        pdf.cell(0, 7, f"Contributions: ${contrib_amount:,.0f} {contrib_freq.lower()} ({contrib_timing.lower()})", ln=True)

    pdf.ln(2)
    pdf.set_font(*fam_bold)
    pdf.cell(0, 8, "Results", ln=True)
    pdf.set_font(*fam_regular)
    if mode == "Required Return to Coast":
        pdf.cell(0, 7, f"Required Return to Coast: {required_return*100:.2f}%", ln=True)
    elif mode == "Ending Balance with Expected Return":
        pdf.cell(0, 7, f"Ending Balance @ Expected Return: ${fv_at_expected:,.0f}", ln=True)
    else:
        pdf.cell(0, 7, f"Years Needed @ Expected Return: {required_years:.1f}", ln=True)
    pdf.cell(0, 7, f"Target at 65: ${target_balance_at_65:,.0f}", ln=True)

    if path_to_chart and os.path.exists(path_to_chart):
        pdf.ln(4)
        pdf.image(path_to_chart, w=180)

    # MLI section
    pdf.ln(6)
    pdf.set_font(*fam_bold)
    pdf.cell(0, 8, "Margin Lifestyle Index", ln=True)
    pdf.set_font(*fam_regular)
    for k, v in mli_scores.items():
        pdf.cell(0, 7, f"{k}: {v}/20", ln=True)
    pdf.cell(0, 7, f"Total: {mli_total}/100 ({mli_label})", ln=True)
    pdf.cell(0, 7, "Ranges: 0–39 Needs Attention | 40–69 Developing | 70–100 Strong", ln=True)

    if path_to_mli and os.path.exists(path_to_mli):
        pdf.ln(4)
        pdf.image(path_to_mli, w=150)

    pdf.ln(6)
    pdf.set_font(*fam_small)
    pdf.multi_cell(0, 6, "This calculator is provided for educational purposes only and should not be considered investment, legal, or tax advice. The calculations are based on user-provided assumptions, which may not reflect actual market conditions or your personal situation. Zizzi Investments, LLC makes no guarantee as to the accuracy or completeness of the results and assumes no liability for decisions made based on this information. Please consult a qualified professional before making financial decisions.")
    return pdf

if st.button("Download PDF Report"):
    pdf = build_pdf(chart_path, mli_chart_path)
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp_file.name)
    with open(tmp_file.name, "rb") as f:
        st.download_button("Click to Download PDF", f, file_name="coast_fi_report.pdf")
    # cleanup temp images
    if chart_path and os.path.exists(chart_path):
        os.unlink(chart_path)
    if mli_chart_path and os.path.exists(mli_chart_path):
        os.unlink(mli_chart_path)

# Disclaimer
st.markdown("---")
st.markdown("**Disclaimer:** This calculator is provided for educational purposes only and should not be considered investment, legal, or tax advice. The calculations are based on user-provided assumptions, which may not reflect actual market conditions or your personal situation. Zizzi Investments, LLC makes no guarantee as to the accuracy or completeness of the results and assumes no liability for decisions made based on this information. Please consult a qualified professional before making financial decisions.")
