import pandas as pd
import plotly.express as px
import streamlit as st

from bond_engine import Bond, duration_and_convexity, price_from_yield, shock_analysis, yield_to_maturity


st.set_page_config(page_title="Bond Analytics", page_icon="📈", layout="wide")
st.title("Bond Analytics & Interest Rate Risk Calculator")
st.caption("Price a fixed-rate bond and analyze YTM, duration, convexity, and rate-shock risk.")

with st.sidebar:
    st.header("Bond inputs")
    face_value = st.number_input("Face value", min_value=1.0, value=1000.0, step=100.0)
    coupon_rate_pct = st.number_input("Annual coupon rate (%)", min_value=0.0, value=8.0, step=0.25)
    market_price = st.number_input("Market price", min_value=0.01, value=950.0, step=10.0)
    years = st.number_input("Years to maturity", min_value=0.25, value=5.0, step=0.5)
    frequency_label = st.selectbox("Coupon frequency", ["Annual", "Semiannual", "Quarterly", "Monthly"], index=1)
    frequency = {"Annual": 1, "Semiannual": 2, "Quarterly": 4, "Monthly": 12}[frequency_label]

try:
    bond = Bond(face_value, coupon_rate_pct / 100, years, frequency)
    ytm = yield_to_maturity(bond, market_price)
    metrics = duration_and_convexity(bond, ytm)
except ValueError as error:
    st.error(str(error))
    st.stop()

current_yield = bond.coupon_payment * frequency / market_price
status = "Par" if abs(market_price - face_value) < 0.01 else ("Premium" if market_price > face_value else "Discount")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Yield to maturity", f"{ytm:.3%}")
col2.metric("Macaulay duration", f"{metrics['macaulay_duration']:.3f} years")
col3.metric("Modified duration", f"{metrics['modified_duration']:.3f}")
col4.metric("Convexity", f"{metrics['convexity']:.3f}")

st.info(
    f"This is a **{status.lower()} bond**. Its current yield is **{current_yield:.3%}**. "
    f"A 100 bp yield increase implies roughly a **{metrics['modified_duration']:.2f}%** price decline before convexity adjustment."
)

tab1, tab2, tab3 = st.tabs(["Price–yield curve", "Rate shocks", "Cash flows"])

with tab1:
    lower = max(-0.01, ytm - 0.05)
    upper = ytm + 0.05
    yields = [lower + i * (upper - lower) / 100 for i in range(101)]
    curve = pd.DataFrame({"Yield": yields, "Bond price": [price_from_yield(bond, value) for value in yields]})
    figure = px.line(curve, x="Yield", y="Bond price", title="Bond price falls as yield rises")
    figure.update_xaxes(tickformat=".1%")
    figure.add_hline(y=market_price, line_dash="dot", annotation_text="Current market price")
    figure.add_vline(x=ytm, line_dash="dot", annotation_text="Current YTM")
    st.plotly_chart(figure, width="stretch")

with tab2:
    shocks = [-200, -100, -50, -25, 25, 50, 100, 200]
    rows = [shock_analysis(bond, ytm, shock) for shock in shocks]
    shock_frame = pd.DataFrame(rows)
    display = pd.DataFrame({
        "Yield shock (bps)": shock_frame["shock_bps"].astype(int),
        "Actual price": shock_frame["actual_price"],
        "Actual change": shock_frame["actual_change"],
        "Duration estimate": shock_frame["duration_change"],
        "Duration + convexity": shock_frame["duration_convexity_change"],
    })
    st.dataframe(
        display.style.format({"Actual price": "{:,.2f}", "Actual change": "{:.3%}", "Duration estimate": "{:.3%}", "Duration + convexity": "{:.3%}"}),
        width="stretch",
        hide_index=True,
    )
    comparison = display.melt(id_vars="Yield shock (bps)", value_vars=["Actual change", "Duration estimate", "Duration + convexity"], var_name="Method", value_name="Price change")
    chart = px.line(comparison, x="Yield shock (bps)", y="Price change", color="Method", markers=True, title="Approximation accuracy")
    chart.update_yaxes(tickformat=".1%")
    st.plotly_chart(chart, width="stretch")

with tab3:
    flows = pd.DataFrame(bond.cash_flows(), columns=["Period", "Cash flow"])
    flows["Time (years)"] = flows["Period"] / frequency
    flows["Present value"] = flows.apply(lambda row: row["Cash flow"] / (1 + ytm / frequency) ** row["Period"], axis=1)
    st.dataframe(flows[["Period", "Time (years)", "Cash flow", "Present value"]].style.format({"Time (years)": "{:.2f}", "Cash flow": "{:,.2f}", "Present value": "{:,.2f}"}), width="stretch", hide_index=True)
    cash_chart = px.bar(flows, x="Time (years)", y="Cash flow", title="Promised bond cash flows")
    st.plotly_chart(cash_chart, width="stretch")

with st.expander("Methodology and assumptions"):
    st.markdown("""
    - Plain-vanilla fixed-rate bond with no embedded options or default risk.
    - Coupon dates are evenly spaced; settlement occurs on a coupon date, so accrued interest is zero.
    - YTM is the nominal annual rate compounded at the selected coupon frequency.
    - YTM assumes the bond is held to maturity and promised payments occur; reinvestment at YTM is the standard interpretation.
    - Modified duration gives the first-order price sensitivity. Convexity adds the second-order curvature adjustment.
    """)
