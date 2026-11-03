# Option Pricing & Volatility Modelling Engine — v1

A small, auditable Python engine for European option valuation. Python 3.10+;
no third-party runtime packages, API keys or downloads required.

## Quick start

```bash
python option_engine.py
python option_engine.py --kind put --spot 100 --strike 110 --maturity 0.5 --volatility 0.25
python option_engine.py --market-price 10.450583572185565
python -m unittest discover -s tests -v
```

The default call is worth approximately **10.450584** for spot/strike 100,
one year, rate 5%, volatility 20%, and no dividend yield. The final command
above infers approximately **0.20** implied volatility from that market price.
Results are printed as JSON. Redirect stdout to save a scenario.

## Implemented

- Black–Scholes–Merton European call and put prices with continuous dividend yield.
- Delta, gamma, vega, theta and rho, checked against finite differences.
- Implied volatility using a bracketed bisection solver and no-arbitrage bounds.
- Expiry payoffs and deterministic zero-volatility prices.
- Finite-number and domain validation, deterministic tests, and CI.

## Inputs and conventions

| Argument | Default | Meaning |
| --- | --- | --- |
| `--spot` | 100 | Current asset price |
| `--strike` | 100 | Exercise price, same currency as spot |
| `--maturity` | 1 | Time to expiry in years |
| `--rate` | 0.05 | Annual continuously compounded risk-free rate |
| `--volatility` | 0.20 | Annual volatility as a decimal |
| `--dividend` | 0 | Annual continuous dividend yield |
| `--kind` | call | `call` or `put` |
| `--market-price` | omitted | Observed price used to infer implied volatility |

Vega and rho are per **1.0** change in volatility/rate; divide by 100 for a
one-percentage-point change. Theta is per year of calendar time passing;
divide by 365 for a simple calendar-day approximation. Greeks are omitted
at expiry or zero volatility. Negative rates are supported.

The solver returns zero at the deterministic lower price bound and rejects
prices below that bound or at/above the limiting upper bound. Deeply in/out
of the money options can have numerically unidentifiable volatility; results
near the bounds should be interpreted with care.

## Python API

```python
from option_engine import price, greeks, implied_volatility

value = price(100, 100, 1, 0.05, 0.20)
risks = greeks(100, 100, 1, 0.05, 0.20)
sigma = implied_volatility(value, 100, 100, 1, 0.05)
```

## Model scope

Assumes constant volatility/rates/yield, lognormal underlying dynamics, frictionless
markets and European exercise. No American exercise, discrete dividends, volatility
surface calibration, transaction costs or market-data integration in v1. This is a
research foundation; tests establish implementation properties, not market realism.

Useful next extensions: binomial American pricing, scenario grids, observed option
chain ingestion, and an arbitrage-aware implied volatility surface.
