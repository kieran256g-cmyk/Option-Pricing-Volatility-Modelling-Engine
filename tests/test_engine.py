import math
import unittest
from option_engine import greeks, implied_volatility, price


class PricingTests(unittest.TestCase):
    def test_reference_prices(self):
        self.assertAlmostEqual(price(100, 100, 1, .05, .2), 10.450583572185565)
        self.assertAlmostEqual(price(100, 100, 1, .05, .2, kind="put"), 5.573526022256971)

    def test_put_call_parity_with_dividends(self):
        call = price(90, 100, 2, -.01, .4, .03)
        put = price(90, 100, 2, -.01, .4, .03, "put")
        self.assertAlmostEqual(call - put, 90 * math.exp(-.06) - 100 * math.exp(.02))

    def test_expiry_and_zero_volatility(self):
        self.assertEqual(price(120, 100, 0, .05, .2), 20)
        self.assertEqual(price(80, 100, 0, .05, .2, kind="put"), 20)
        self.assertAlmostEqual(price(100, 100, 1, .05, 0), 100 - 100 * math.exp(-.05))

    def test_implied_volatility_round_trip(self):
        for kind in ("call", "put"):
            for vol in (.08, .2, .8, 2.0):
                value = price(105, 100, .7, -.01, vol, .02, kind)
                self.assertAlmostEqual(implied_volatility(value, 105, 100, .7, -.01, .02, kind), vol, places=8)

    def test_invalid_market_prices(self):
        for value in (-1, 101, float("nan")):
            with self.assertRaises(ValueError):
                implied_volatility(value, 100, 100, 1, .05)

    def test_greeks_against_finite_differences(self):
        for kind in ("call", "put"):
            s, k, t, r, v, q, h = 100, 110, .8, .03, .25, .01, .001
            g = greeks(s, k, t, r, v, q, kind)
            f = lambda s=s, t=t, r=r, v=v: price(s, k, t, r, v, q, kind)
            self.assertAlmostEqual(g["delta"], (f(s=s+h)-f(s=s-h))/(2*h), places=6)
            self.assertAlmostEqual(g["gamma"], (f(s=s+h)-2*f()+f(s=s-h))/h**2, places=6)
            self.assertAlmostEqual(g["vega"], (f(v=v+h)-f(v=v-h))/(2*h), places=3)
            self.assertAlmostEqual(g["theta"], -(f(t=t+h)-f(t=t-h))/(2*h), places=4)
            self.assertAlmostEqual(g["rho"], (f(r=r+h)-f(r=r-h))/(2*h), places=3)

    def test_bad_inputs(self):
        for spot, vol in [(0, .2), (100, -.1), (float("inf"), .2)]:
            with self.assertRaises(ValueError):
                price(spot, 100, 1, .05, vol)


if __name__ == "__main__":
    unittest.main()
