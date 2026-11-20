"""Run from the project folder:  python -m unittest discover -s tests -v

Hand-checkable cases for the formulas, plus boundary and bad-input cases.
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import coach  # noqa: E402
import engine as eng  # noqa: E402


def two_asset_est(mu_stock=0.08, mu_cash=0.03, vol_stock=0.20):
    """Tiny hand-checkable world: only VTI is risky, everything else is riskless at mu_cash."""
    mu = np.full(7, mu_cash)
    mu[0] = mu_stock
    vol = np.zeros(7)
    vol[0] = vol_stock
    return {"mu": mu, "vol": vol, "cov": np.outer(vol, vol), "corr": np.eye(7)}


def params(**changes):
    p = eng.default_params("Near-retiree (about 8 years to retirement)")
    p["yield_10y"] = 0.05
    p.update(changes)
    return p


class Formulas(unittest.TestCase):
    def test_return_volatility_and_bad_year_by_hand(self):
        est, p = two_asset_est(), params()
        m = eng.measures(eng.as_vector({"VTI": 0.5, "BIL": 0.5}), est, p)
        self.assertAlmostEqual(m["net_return"][0], 0.055)             # .5*8% + .5*3%
        self.assertAlmostEqual(m["vol"][0], 0.10)                     # .5 * 20%
        self.assertAlmostEqual(m["bad_year"][0], 0.055 - 1.645 * 0.10)

    def test_trading_cost_and_fee_reduce_return(self):
        est = two_asset_est()
        cur = eng.as_vector({"BIL": 1.0})
        p = params(current=cur, trade_cost_bps=50.0, advisory_fee=0.005)
        m = eng.measures(eng.as_vector({"VTI": 0.5, "BIL": 0.5}), est, p)
        # turnover 50% one-way -> 100% of value traded x 0.50% = 0.50%; fee 0.50%
        self.assertAlmostEqual(m["net_return"][0], 0.055 - 0.005 - 0.005)

    def test_turnover(self):
        self.assertAlmostEqual(eng.turnover([0.6, 0.4], [0.4, 0.6]), 0.2)

    def test_grid_is_complete_and_valid(self):
        w = eng.grid()
        self.assertEqual(len(w), 53130)                               # C(25, 5)
        self.assertTrue(np.allclose(w.sum(axis=1), 1) and w.min() >= 0 and (w[:, 6] == 0).all())


class Mandate(unittest.TestCase):
    def test_limit_is_inclusive_at_the_boundary(self):
        est, p = two_asset_est(), params(equity_max=0.40, fund_max=0.40, loss_limit=0.50)
        rules = eng.rule_table(eng.as_vector({"VTI": 0.40, "IEF": 0.30, "BIL": 0.30}), est, p)
        self.assertTrue(next(r for r in rules if r["rule"].startswith("Stocks"))["passed"])
        rules = eng.rule_table(eng.as_vector({"VTI": 0.45, "IEF": 0.25, "BIL": 0.30}), est, p)
        self.assertFalse(next(r for r in rules if r["rule"].startswith("Stocks"))["passed"])

    def test_verdict_names_the_broken_rules(self):
        est, p = two_asset_est(), params()
        v = eng.verdict(eng.rule_table(eng.as_vector({"VTI": 1.0}), est, p))
        self.assertFalse(v["passed"])
        for word in ("Stocks", "Cash reserve", "single fund", "Bad-year"):
            self.assertTrue(any(word in f for f in v["failed"]), word)

    def test_benchmark_fund_is_outside_the_universe(self):
        est, p = two_asset_est(), params()
        rules = eng.rule_table(eng.as_vector({"VOO": 0.3, "BIL": 0.7}), est, p)
        self.assertFalse(next(r for r in rules if r["rule"].startswith("Approved"))["passed"])

    def test_all_cash_passes_limits_but_misses_objective(self):
        est, p = two_asset_est(), params(fund_max=1.0)
        v = eng.verdict(eng.rule_table(eng.as_vector({"BIL": 1.0}), est, p))
        self.assertEqual(len(v["failed"]), 1)
        self.assertIn("Expected return", v["failed"][0])


class Search(unittest.TestCase):
    def test_growth_takes_stocks_up_to_the_binding_limit(self):
        est = two_asset_est()
        p = params(equity_max=0.65, fund_max=1.0, loss_limit=0.50)
        self.assertAlmostEqual(eng.optimise(est, p)[0], 0.65)         # the stock cap binds
        p = params(equity_max=0.65, fund_max=1.0, loss_limit=0.02)
        # loss = 1.645*.2*w - (.03 + .05*w) <= .02  ->  w <= .179  ->  15% on the grid
        self.assertAlmostEqual(eng.optimise(est, p)[0], 0.15)

    def test_protect_takes_least_risk_that_reaches_the_target(self):
        est = two_asset_est()
        p = params(priority="protect", cpi=0.02, real_target=0.03, fund_max=1.0, loss_limit=0.5)
        # need .03 + .05*w >= .05 -> w >= .40
        self.assertAlmostEqual(eng.optimise(est, p)[0], 0.40)

    def test_returns_none_when_nothing_is_feasible(self):
        p = params(priority="protect", real_target=0.50)
        self.assertIsNone(eng.optimise(two_asset_est(), p))

    def test_nearest_fix_is_compliant_and_no_further_than_the_optimum(self):
        prices = eng.load_prices()
        cur = eng.as_vector({"VTI": 0.5, "VT": 0.25, "SCHD": 0.15, "LQD": 0.05, "BIL": 0.05})
        p = params(current=cur)
        est = eng.estimates(prices, p)
        fixed, met = eng.nearest_fix(cur, est, p)
        self.assertTrue(met and eng.verdict(eng.rule_table(fixed, est, p))["passed"])
        self.assertLessEqual(eng.turnover(fixed, cur), eng.turnover(eng.optimise(est, p), cur) + 1e-12)


class RealData(unittest.TestCase):
    def setUp(self):
        self.prices = eng.load_prices()
        self.series = eng.load_yield_series(eng.DATA / "DGS10_vintage_2026-09-30.csv")

    def test_signal_uses_only_data_published_before_the_decision_date(self):
        s = eng.signal_as_of(self.series, "2026-09-30")
        self.assertEqual((s["observation_date"], s["value_pct"]), ("2026-09-29", 5.26))
        earlier = eng.signal_as_of(self.series, "2026-09-29")       # 09-29 not yet published
        self.assertEqual((earlier["observation_date"], earlier["value_pct"]), ("2026-09-28", 5.24))
        later = eng.load_yield_series(eng.DATA / "DGS10_downloaded_2026-10-29.csv")
        self.assertEqual(eng.signal_as_of(later, "2026-09-30")["value_pct"], 5.26)   # look-ahead blocked

    def test_signal_estimates(self):
        est = eng.estimates(self.prices, params(yield_10y=0.0526))
        i = eng.ASSETS.index
        self.assertAlmostEqual(est["mu"][i("IEF")], 0.0526 - 0.0015)
        self.assertAlmostEqual(est["mu"][i("LQD")], 0.0526 + 0.010 - 0.0014)
        self.assertAlmostEqual(est["mu"][i("VTI")], 0.0526 + 0.035 - 0.0003)
        self.assertEqual(est["months"], 59)

    def test_full_run_and_stress_shapes(self):
        p = params(yield_10y=0.0526)
        base = eng.solve(self.prices, p)
        self.assertTrue(base["recommended"]["verdict"]["passed"])
        self.assertIn("Equal weight", base["candidates"])
        self.assertIn("Inverse volatility", base["candidates"])
        stress = eng.stress_run(self.prices, p, base)
        self.assertEqual({r["group"] for r in stress}, {"Estimates", "Window", "Costs", "Constraints"})
        self.assertIn(eng.process_decision(base, stress, p)["call"], {"ADOPT", "PILOT", "REJECT"})
        rng = eng.allocation_range(base, stress)
        self.assertTrue(((rng["Low"] <= rng["Base"] + 1e-12) & (rng["Base"] <= rng["High"] + 1e-12)).all())

    def test_impossible_mandate_is_rejected(self):
        p = params(yield_10y=0.0526, real_target=0.30, priority="protect")
        base = eng.solve(self.prices, p)
        self.assertIsNone(base["recommended"])
        d = eng.process_decision(base, eng.stress_run(self.prices, p, base), p)
        self.assertTrue(d["stop"] and d["call"] == "REJECT")

    def test_price_gaps_are_rejected(self):
        broken = self.prices.reset_index().drop(index=10)
        with self.assertRaises(ValueError):
            eng.load_prices(pd.io.common.StringIO(broken.to_csv(index=False)))


class Outlook(unittest.TestCase):
    def test_zero_risk_matches_compound_interest(self):
        v = eng.outlook(1000, 100, 2, 0, 0, 0.10, 0.0, paths=10)
        self.assertAlmostEqual(v["median_at_retirement"], ((1000 + 100) * 1.1 + 100) * 1.1)

    def test_money_runs_out_when_withdrawals_are_too_large(self):
        self.assertEqual(eng.outlook(100, 0, 0, 5, 60, 0.0, 0.0, paths=10)["success"], 0.0)
        self.assertEqual(eng.outlook(100, 0, 0, 5, 10, 0.0, 0.0, paths=10)["success"], 1.0)


class Upload(unittest.TestCase):
    def test_values_and_percent_weights(self):
        w, total = eng.parse_portfolio("Ticker,Value\nvti,\"$6,000\"\nBIL,4000\n")
        self.assertAlmostEqual(w[0], 0.6)
        self.assertEqual(total, 10000)
        w, total = eng.parse_portfolio("ticker,weight\nVTI,60%\nIEF,40%\n")
        self.assertAlmostEqual(w[eng.ASSETS.index("IEF")], 0.4)
        self.assertIsNone(total)

    def test_bad_files_are_refused_with_a_reason(self):
        for text in ("ticker,weight\nTSLA,100\n", "ticker,weight\nVTI,-10\nBIL,110\n",
                     "name,amount\nVTI,1\n", "ticker,weight\nVTI,abc\n", "ticker,weight\nVTI,0\n"):
            with self.assertRaises(ValueError):
                eng.parse_portfolio(text)


class Coach(unittest.TestCase):
    def test_trades_net_to_zero(self):
        t = coach.trades(eng.as_vector({"VTI": 1.0}), eng.as_vector({"VTI": 0.6, "IEF": 0.4}))
        self.assertEqual(t[0][0] in ("VTI", "IEF"), True)
        self.assertAlmostEqual(sum(c for _, c in t), 0.0)

    def test_output_guard_flags_numbers_not_in_the_facts(self):
        facts = '{"expected_return_pct": 7.27, "bad_year_loss_pct": 9.99}'
        self.assertEqual(coach.unsupported_figures("It returns 7.27% with a 10.0% loss.", facts), [])
        self.assertEqual(coach.unsupported_figures("Stocks will return 12% next year.", facts), ["12%"])


if __name__ == "__main__":
    unittest.main()
