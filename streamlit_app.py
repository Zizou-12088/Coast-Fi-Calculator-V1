
import math
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="Coast FI Calculator — Zizzi Investments", page_icon="🏝", layout="centered")

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
