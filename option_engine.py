"""European Black-Scholes-Merton prices, Greeks and implied volatility."""
import argparse
import json
import math
from statistics import NormalDist

NORMAL = NormalDist()


def validate(spot, strike, maturity, rate, volatility, dividend=0.0, kind="call"):
    values = (spot, strike, maturity, rate, volatility, dividend)
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in values):
        raise ValueError("Inputs must be finite numbers")
    if spot <= 0 or strike <= 0 or maturity < 0 or volatility < 0:
        raise ValueError("Spot/strike must be positive; maturity/volatility must be nonnegative")
    if kind not in ("call", "put"):
        raise ValueError("Option kind must be call or put")


def price(spot, strike, maturity, rate, volatility, dividend=0.0, kind="call"):
    """Rates and volatility are annual decimals; maturity is in years."""
    validate(spot, strike, maturity, rate, volatility, dividend, kind)
    a = spot * math.exp(-dividend * maturity)
    b = strike * math.exp(-rate * maturity)
    if maturity == 0 or volatility == 0:
        return max(a - b, 0.0) if kind == "call" else max(b - a, 0.0)
    width = volatility * math.sqrt(maturity)
    d1 = (math.log(spot / strike) + (rate - dividend + volatility**2 / 2) * maturity) / width
    d2 = d1 - width
    if kind == "call":
        return max(0.0, a * NORMAL.cdf(d1) - b * NORMAL.cdf(d2))
    return max(0.0, b * NORMAL.cdf(-d2) - a * NORMAL.cdf(-d1))


def greeks(spot, strike, maturity, rate, volatility, dividend=0.0, kind="call"):
    """Vega/rho per unit decimal; theta per year, delta per spot unit."""
    validate(spot, strike, maturity, rate, volatility, dividend, kind)
    if maturity == 0 or volatility == 0:
        raise ValueError("Greeks require positive maturity and volatility")
    root = math.sqrt(maturity)
    d1 = (math.log(spot / strike) + (rate - dividend + volatility**2 / 2) * maturity) / (volatility * root)
    d2 = d1 - volatility * root
    discount_q, discount_r = math.exp(-dividend * maturity), math.exp(-rate * maturity)
    density = NORMAL.pdf(d1)
    sign = 1 if kind == "call" else -1
    delta = sign * discount_q * NORMAL.cdf(sign * d1)
    theta = (-spot * discount_q * density * volatility / (2 * root)
             - sign * rate * strike * discount_r * NORMAL.cdf(sign * d2)
             + sign * dividend * spot * discount_q * NORMAL.cdf(sign * d1))
    return {"delta": delta, "gamma": discount_q * density / (spot * volatility * root),
            "vega": spot * discount_q * density * root, "theta": theta,
            "rho": sign * strike * maturity * discount_r * NORMAL.cdf(sign * d2)}


def implied_volatility(market_price, spot, strike, maturity, rate, dividend=0.0, kind="call"):
    validate(spot, strike, maturity, rate, 0.0, dividend, kind)
    if isinstance(market_price, bool) or not math.isfinite(market_price) or market_price < 0:
        raise ValueError("Market price must be finite and nonnegative")
    if maturity == 0:
        raise ValueError("Implied volatility requires positive maturity")
    lower = price(spot, strike, maturity, rate, 0.0, dividend, kind)
    upper = spot * math.exp(-dividend * maturity) if kind == "call" else strike * math.exp(-rate * maturity)
    if market_price < lower or market_price >= upper:
        raise ValueError("Market price is outside finite-volatility no-arbitrage bounds")
    if market_price == lower:
        return 0.0
    lo, hi = 0.0, 1.0
    while price(spot, strike, maturity, rate, hi, dividend, kind) < market_price:
        hi *= 2
        if hi > 1024:
            raise ValueError("Could not bracket implied volatility")
    for _ in range(160):
        mid = (lo + hi) / 2
        if price(spot, strike, maturity, rate, mid, dividend, kind) < market_price:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for flag, default in [("spot", 100), ("strike", 100), ("maturity", 1), ("rate", .05), ("volatility", .2), ("dividend", 0)]:
        parser.add_argument("--" + flag, type=float, default=default)
    parser.add_argument("--kind", choices=["call", "put"], default="call")
    parser.add_argument("--market-price", type=float, help="Infer volatility from this observed option price")
    args = vars(parser.parse_args(argv))
    market_price = args.pop("market_price")
    try:
        result = {"version": "1.0.0", "inputs": args, "price": price(**args)}
        if args["maturity"] > 0 and args["volatility"] > 0:
            result["greeks"] = greeks(**args)
        if market_price is not None:
            iv_args = {k: v for k, v in args.items() if k != "volatility"}
            result["implied_volatility"] = implied_volatility(market_price, **iv_args)
        print(json.dumps(result, indent=2, allow_nan=False))
    except (ValueError, OverflowError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
