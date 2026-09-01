# Bond Analytics & Interest Rate Risk Calculator

An interactive fixed-income analytics app that combines bond pricing, yield to maturity (YTM), Macaulay duration, modified duration, convexity, and yield-shock scenario analysis.

## Live Demo

[Launch the interactive Bond Analytics Calculator](https://bond-analytics-calculator-krishna.streamlit.app)

## Features

- Prices plain-vanilla fixed-rate bonds from yield
- Numerically solves YTM from market price using bisection
- Calculates current yield, Macaulay duration, modified duration, and convexity
- Compares actual repricing with duration-only and duration-plus-convexity estimates
- Visualizes the price–yield curve and contractual cash flows
- Includes automated tests for financial identities and input validation

## Run locally

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
```

Activate the environment:

```bash
# macOS/Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install and run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Run the tests:

```bash
pytest -q
```

## Calculation conventions

The calculator treats YTM as a nominal annual yield compounded at the coupon frequency. It assumes settlement on a coupon date, evenly spaced payments, no accrued interest, no embedded options, and no default. These assumptions keep the first release focused on the core mathematics and are stated in the interface.

For a yield change \(\Delta y\), the estimated percentage price change is:

```text
ΔP/P ≈ −Modified Duration × Δy + ½ × Convexity × (Δy)²
```


