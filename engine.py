"""Retirement Mandate Check - calculation engine (no Streamlit in this file).

AI-use disclosure: built with Claude (Anthropic, Claude Code) as a coding assistant.
Education only. Not investment advice. I am not a financial advisor.

Conventions
- Weights, returns, volatilities are DECIMALS inside this file (0.05 = 5%).
- Asset order is always ASSETS: six mandate funds, then VOO (benchmark only).
- All estimates are annual and nominal, in USD, net of fund expense ratios.
"""
from functools import lru_cache
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DECISION_DATE = "2026-09-30"          # last month-end in data/prices.csv
Z_95 = 1.645                          # one-sided 5% point of a normal distribution

# kind: stock / bond / cash. expense = annual expense ratio (decimal) typed in by the
# author from fund fact sheets; editable in the app. Verify before relying on it.
FUNDS = {
    "VTI":  {"name": "Vanguard Total US Stock Market", "kind": "stock", "expense": 0.0003},
    "VT":   {"name": "Vanguard Total World Stock",     "kind": "stock", "expense": 0.0006},
    "SCHD": {"name": "Schwab US Dividend Equity",      "kind": "stock", "expense": 0.0006},
    "IEF":  {"name": "iShares 7-10 Year Treasury",     "kind": "bond",  "expense": 0.0015},
    "LQD":  {"name": "iShares Inv. Grade Corporate",   "kind": "bond",  "expense": 0.0014},
    "BIL":  {"name": "SPDR 1-3 Month T-Bill (cash)",   "kind": "cash",  "expense": 0.001356},
    "VOO":  {"name": "Vanguard S&P 500 (benchmark)",   "kind": "stock", "expense": 0.0003},
}
ASSETS = list(FUNDS)                  # 7 names
UNIVERSE = ASSETS[:6]                 # the funds the mandate may hold
KINDS = np.array([FUNDS[a]["kind"] for a in ASSETS])
IS_STOCK, IS_CASH = KINDS == "stock", KINDS == "cash"

# Client presets. Percent values here are converted to decimals by default_params().
PRESETS = {
    "Mid-career saver (about 20 years to retirement)": dict(
        years_to_retire=20, real_target=4.0, equity_max=85, loss_limit=15, reserve_min=2, bench_stock=80),
    "Near-retiree (about 8 years to retirement)": dict(
        years_to_retire=8, real_target=3.0, equity_max=65, loss_limit=10, reserve_min=5, bench_stock=60),
    "Already retired (drawing income)": dict(
        years_to_retire=0, real_target=2.0, equity_max=45, loss_limit=6, reserve_min=4, bench_stock=40),
}


def default_params(preset=None):
    """Every input the engine uses, in one dict. Decimals unless the name says otherwise."""
    m = PRESETS[preset or list(PRESETS)[1]]
    return dict(
        # mandate
        cpi=0.025, real_target=m["real_target"] / 100, equity_max=m["equity_max"] / 100,
        fund_max=0.40, reserve_min=m["reserve_min"] / 100, loss_limit=m["loss_limit"] / 100,
        turnover_max=0.25, bench_stock=m["bench_stock"] / 100,
        # estimates
        mode="signal", window=None, yield_10y=None, equity_premium=0.035, credit_spread=0.010,
        vol_mult=1.0,
        # costs
        advisory_fee=0.0, trade_cost_bps=5.0,
        # process
        priority="growth", current=None,
    )


# ------------------------------------------------------------------ data loading
def load_prices(source=None):
    """Month-end adjusted closes. Rejects gaps instead of filling them."""
    df = pd.read_csv(source if source is not None else DATA / "prices.csv")
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date").sort_index()
    missing = [a for a in ASSETS if a not in df.columns]
    if missing:
        raise ValueError(f"Price file is missing columns: {missing}")
    df = df[ASSETS].astype(float)
    if df.isna().any().any() or (df <= 0).any().any():
        raise ValueError("Prices must be present and positive for every fund and month.")
    months = df.index.year * 12 + df.index.month
    if (np.diff(months) != 1).any():
        raise ValueError("Prices must be consecutive months with no gaps.")
    return df


def load_yield_series(path):
    """FRED/ALFRED two-column CSV -> Series of percent yields. '.' rows are market holidays."""
    df = pd.read_csv(path)
    df.columns = ["date", "value"]
    df["value"] = pd.to_numeric(df["value"], errors="coerce")   # '.' -> NaN, then dropped
    df = df.dropna()
    return pd.Series(df["value"].values, index=pd.to_datetime(df["date"])).sort_index()


def signal_as_of(series, decision_date=DECISION_DATE, history_years=10):
    """Point-in-time read of the 10-year Treasury yield.

    DGS10 for day t is published on the next business day, so on the decision date the
    latest usable observation is the last one dated strictly BEFORE that date.
    """
    decision = pd.Timestamp(decision_date)
    known = series[series.index < decision]
    if known.empty:
        raise ValueError("No yield observation was published before the decision date.")
    value = float(known.iloc[-1])
    history = known[known.index >= decision - pd.DateOffset(years=history_years)]
    return {
        "decision_date": decision.date().isoformat(),
        "observation_date": known.index[-1].date().isoformat(),
        "value_pct": value,
        "percentile": float((history <= value).mean() * 100),
        "history_median_pct": float(history.median()),
        "history_years": history_years,
        "last_three": [(d.date().isoformat(), float(v)) for d, v in known.iloc[-3:].items()],
    }


# ------------------------------------------------------------------ estimates
def estimates(prices, p):
    """Expected returns (net of fund expenses), volatilities and covariance for ASSETS.

    mode 'signal'     : bonds earn the as-of 10-year yield, stocks earn yield + premium,
                        cash earns BIL's trailing-12-month return. Fund expenses subtracted.
    mode 'historical' : average monthly return in the window x 12 (already net of expenses
                        because adjusted prices are net).
    Risk (volatility, correlation) always comes from the price window.
    """
    rets = prices.pct_change().dropna()
    if p["window"]:
        rets = rets.iloc[-int(p["window"]):]
    if len(rets) < 24:
        raise ValueError("Need at least 24 monthly returns to estimate risk.")
    vol = rets.std(ddof=1).values * np.sqrt(12) * p["vol_mult"]
    corr = rets.corr().values
    cov = np.outer(vol, vol) * corr
    if p["mode"] == "historical":
        mu = rets.mean().values * 12
    else:
        if p["yield_10y"] is None:
            raise ValueError("Signal mode needs the as-of 10-year yield.")
        y = p["yield_10y"]
        cash = float(prices["BIL"].iloc[-1] / prices["BIL"].iloc[-13] - 1)
        gross = {"stock": y + p["equity_premium"], "cash": cash}
        mu = np.array([gross.get(FUNDS[a]["kind"], y) for a in ASSETS], dtype=float)
        mu[ASSETS.index("LQD")] = y + p["credit_spread"]
        mu = mu - np.array([FUNDS[a]["expense"] for a in ASSETS])
    return {"mu": mu, "vol": vol, "corr": corr, "cov": cov, "months": len(rets),
            "start": rets.index[0].date().isoformat(), "end": rets.index[-1].date().isoformat()}


# ------------------------------------------------------------------ portfolios
@lru_cache(maxsize=4)
def grid(step_pct=5):
    """Every long-only, fully invested mix of the six universe funds on a 5-point grid.
    Returned with a zero column for VOO so rows line up with ASSETS."""
    units, n = 100 // step_pct, len(UNIVERSE)

    def mixes(left, count):
        if count == 1:
            yield (left,)
        else:
            for u in range(left + 1):
                for tail in mixes(left - u, count - 1):
                    yield (u,) + tail

    w = np.array(list(mixes(units, n)), dtype=float) / units
    return np.hstack([w, np.zeros((len(w), 1))])


def as_vector(weights):
    """dict or sequence of decimals -> length-7 array in ASSETS order."""
    if isinstance(weights, dict):
        return np.array([float(weights.get(a, 0.0)) for a in ASSETS])
    w = np.asarray(weights, dtype=float)
    return np.append(w, 0.0) if len(w) == len(UNIVERSE) else w


def turnover(new, old):
    """One-way turnover: the share of the portfolio that has to be sold."""
    return 0.5 * np.abs(np.asarray(new) - np.asarray(old)).sum(axis=-1)


def measures(W, est, p):
    """Vectorised portfolio numbers for one weight vector or a matrix of them."""
    W = np.atleast_2d(W)
    gross = W @ est["mu"]
    cost = 0.0
    if p["current"] is not None:
        # selling x% and buying x% trades 2x% of the portfolio
        cost = 2 * turnover(W, p["current"]) * p["trade_cost_bps"] / 10000
    net = gross - p["advisory_fee"] - cost
    vol = np.sqrt(np.maximum(np.einsum("ij,jk,ik->i", W, est["cov"], W), 0))
    return {
        "net_return": net, "vol": vol,
        "bad_year": net - Z_95 * vol,                 # estimated 1-in-20 one-year return
        "stock": W[:, IS_STOCK].sum(axis=1), "cash": W[:, IS_CASH].sum(axis=1),
        "largest": W.max(axis=1), "outside": W[:, len(UNIVERSE):].sum(axis=1),
        "total": W.sum(axis=1), "lowest": W.min(axis=1),
    }


TOL = 1e-9


def rule_table(w, est, p):
    """The mandate as a list of checks for ONE portfolio. kind: 'limit' or 'objective'."""
    m = {k: float(v[0]) for k, v in measures(w, est, p).items()}
    target = p["cpi"] + p["real_target"]
    loss = max(0.0, -m["bad_year"])
    rows = [
        ("Fully invested (weights sum to 100%)", "limit", m["total"], 1.0, abs(m["total"] - 1) < 1e-6),
        ("Long-only (no negative weights)", "limit", m["lowest"], 0.0, m["lowest"] >= -TOL),
        ("Approved universe only", "limit", m["outside"], 0.0, m["outside"] <= TOL),
        (f"Cash reserve (BIL) at least {p['reserve_min']:.1%}", "limit", m["cash"], p["reserve_min"],
         m["cash"] >= p["reserve_min"] - TOL),
        (f"Stocks at most {p['equity_max']:.0%}", "limit", m["stock"], p["equity_max"],
         m["stock"] <= p["equity_max"] + TOL),
        (f"Any single fund at most {p['fund_max']:.0%}", "limit", m["largest"], p["fund_max"],
         m["largest"] <= p["fund_max"] + TOL),
        (f"Bad-year loss (1-in-20) at most {p['loss_limit']:.0%}", "limit", loss, p["loss_limit"],
         loss <= p["loss_limit"] + TOL),
        (f"Expected return at least CPI + {p['real_target']:.1%} = {target:.1%}", "objective",
         m["net_return"], target, m["net_return"] >= target - TOL),
    ]
    return [dict(rule=r, kind=k, value=v, limit=l, passed=bool(ok)) for r, k, v, l, ok in rows]


def verdict(rules):
    failed = [r["rule"] for r in rules if not r["passed"]]
    return {"passed": not failed, "failed": failed,
            "text": "PASS" if not failed else "FAIL: " + "; ".join(failed)}


def feasible_mask(est, p, need_objective=True):
    """Which grid portfolios satisfy every limit (and the objective if asked)."""
    W = grid()
    m = measures(W, est, p)
    ok = ((m["cash"] >= p["reserve_min"] - TOL) & (m["stock"] <= p["equity_max"] + TOL)
          & (m["largest"] <= p["fund_max"] + TOL) & (-m["bad_year"] <= p["loss_limit"] + TOL))
    if need_objective:
        ok &= m["net_return"] >= p["cpi"] + p["real_target"] - TOL
    return W, m, ok


def optimise(est, p):
    """The constrained portfolio.

    priority 'growth'  : highest expected net return among portfolios inside every limit.
    priority 'protect' : smallest bad-year loss among portfolios that are inside every
                         limit AND reach the return objective.
    Returns None when no grid portfolio qualifies. Ties go to the lower-risk mix.
    """
    W, m, ok = feasible_mask(est, p, need_objective=p["priority"] == "protect")
    if not ok.any():
        return None
    idx = np.flatnonzero(ok)
    if p["priority"] == "protect":
        order = np.lexsort((-m["net_return"][idx], np.round(-m["bad_year"][idx], 10)))
    else:
        order = np.lexsort((m["vol"][idx], np.round(-m["net_return"][idx], 10)))
    return W[idx[order[0]]]


def nearest_fix(current, est, p):
    """Smallest set of trades that brings `current` inside the mandate.
    Tries limits + objective first; if impossible, limits only. Returns (weights, met_objective)."""
    for need in (True, False):
        W, m, ok = feasible_mask(est, p, need_objective=need)
        if ok.any():
            idx = np.flatnonzero(ok)
            t = turnover(W[idx], current)
            order = np.lexsort((-m["net_return"][idx], np.round(t, 10)))
            return W[idx[order[0]]], need
    return None, False


def equal_weight():
    return as_vector([1 / len(UNIVERSE)] * len(UNIVERSE))


def inverse_volatility(est):
    inv = 1 / est["vol"][:len(UNIVERSE)]
    return as_vector(inv / inv.sum())


def benchmark(p):
    w = np.zeros(len(ASSETS))
    w[ASSETS.index("VOO")] = p["bench_stock"]
    w[ASSETS.index("IEF")] = 1 - p["bench_stock"]
    return w


def describe(w, est, p):
    rules = rule_table(w, est, p)
    m = {k: float(v[0]) for k, v in measures(w, est, p).items()}
    return {"weights": np.asarray(w, dtype=float), "rules": rules, "verdict": verdict(rules), **m,
            "loss": max(0.0, -m["bad_year"])}


def solve(prices, p):
    """One full run: estimates, baselines, constrained portfolio, verdicts."""
    est = estimates(prices, p)
    out = {"est": est, "params": dict(p), "candidates": {}}
    if p["current"] is not None:
        out["candidates"]["Your portfolio"] = describe(p["current"], est, p)
    out["candidates"]["Equal weight"] = describe(equal_weight(), est, p)
    out["candidates"]["Inverse volatility"] = describe(inverse_volatility(est), est, p)
    best = optimise(est, p)
    out["recommended"] = None if best is None else describe(best, est, p)
    if best is not None:
        out["candidates"]["Constrained portfolio"] = out["recommended"]
    out["benchmark"] = describe(benchmark(p), est, dict(p, current=None))
    return out


# ------------------------------------------------------------------ stress run
def stress_scenarios(p):
    """(group, label, overrides). Each one changes exactly one thing from the base case."""
    y = p["yield_10y"]
    return [
        ("Estimates", "Stock premium 2 points lower", {"equity_premium": p["equity_premium"] - 0.02}),
        ("Estimates", "10-year yield 1 point lower", {"yield_10y": y - 0.01}),
        ("Estimates", "10-year yield 1 point higher", {"yield_10y": y + 0.01}),
        ("Estimates", "All volatilities 25% higher", {"vol_mult": p["vol_mult"] * 1.25}),
        ("Estimates", "Historical average returns instead of the signal", {"mode": "historical"}),
        ("Window", "Risk from last 36 months only", {"window": 36}),
        ("Window", "Risk from last 24 months only", {"window": 24}),
        ("Costs", "Advisory fee of 0.50% a year", {"advisory_fee": p["advisory_fee"] + 0.005}),
        ("Costs", "Trading cost 50 bps instead of 5", {"trade_cost_bps": 50.0}),
        ("Constraints", "Stock cap 10 points tighter", {"equity_max": p["equity_max"] - 0.10}),
        ("Constraints", "Loss limit 2 points tighter", {"loss_limit": p["loss_limit"] - 0.02}),
        ("Constraints", "Cash reserve doubled", {"reserve_min": p["reserve_min"] * 2}),
    ]


def stress_run(prices, p, base):
    """Re-run the whole process under each scenario and compare with the base portfolio."""
    rows = []
    base_w = None if base["recommended"] is None else base["recommended"]["weights"]
    for group, label, change in stress_scenarios(p):
        run = solve(prices, dict(p, **change))
        rec = run["recommended"]
        row = {"group": group, "scenario": label, "weights": None, "compliant": False,
               "net_return": np.nan, "loss": np.nan, "shift": np.nan, "failed": "no portfolio inside the limits"}
        if rec is not None:
            row.update(weights=rec["weights"], compliant=rec["verdict"]["passed"],
                       net_return=rec["net_return"], loss=rec["loss"],
                       failed="; ".join(rec["verdict"]["failed"]))
            if base_w is not None:
                row["shift"] = float(turnover(rec["weights"], base_w))
        rows.append(row)
    return rows


def process_decision(base, stress, p):
    """Rule-based suggestion and the stop condition. The human makes the final call."""
    rec = base["recommended"]
    fails = [r for r in stress if not r["compliant"]]
    unstable = [r for r in stress if r["compliant"] and r["shift"] > p["turnover_max"] + TOL]
    if rec is None or not rec["verdict"]["passed"]:
        return {"call": "REJECT", "stop": True, "fails": fails, "unstable": unstable,
                "why": "STOP: the base case has no portfolio that meets every limit and the return objective."}
    if len(fails) > len(stress) / 2:
        return {"call": "REJECT", "stop": True, "fails": fails, "unstable": unstable,
                "why": f"STOP: {len(fails)} of {len(stress)} stress scenarios have no compliant portfolio."}
    if fails or unstable:
        return {"call": "PILOT", "stop": False, "fails": fails, "unstable": unstable,
                "why": f"Base case passes, but {len(fails)} stress scenario(s) fail the mandate and "
                       f"{len(unstable)} move the weights by more than the {p['turnover_max']:.0%} turnover limit."}
    return {"call": "ADOPT", "stop": False, "fails": fails, "unstable": unstable,
            "why": "Base case and all stress scenarios produce a compliant, stable portfolio."}


def allocation_range(base, stress):
    """Lowest and highest weight per fund across the base case and compliant stress runs."""
    if base["recommended"] is None:
        return None
    stack = [base["recommended"]["weights"]] + [r["weights"] for r in stress if r["compliant"]]
    stack = np.array(stack)
    return pd.DataFrame({"Base": base["recommended"]["weights"], "Low": stack.min(axis=0),
                         "High": stack.max(axis=0)}, index=ASSETS).iloc[:len(UNIVERSE)]


# ------------------------------------------------------------------ history and outlook
def history(prices, portfolios):
    """Growth of $100, rebalanced monthly to fixed weights. In-sample: a description of the
    past five years, not evidence the portfolio will repeat it."""
    rets = prices.pct_change().dropna()
    growth = pd.DataFrame({name: 100 * (1 + rets.values @ w).cumprod() for name, w in portfolios.items()},
                          index=rets.index)
    drawdown = (growth / growth.cummax() - 1).min()
    return growth, drawdown


def outlook(balance, contribution, years_to_retire, years_retired, withdrawal,
            real_return, vol, paths=2000, seed=7):
    """Monte Carlo of the balance in TODAY'S dollars. Annual real returns are drawn from a
    normal distribution (a simplification: real markets have fatter tails). Contributions are
    added while working; withdrawals taken while retired. Seeded so reruns match."""
    if balance < 0 or years_to_retire < 0 or years_retired < 0:
        raise ValueError("Balance and years cannot be negative.")
    years = int(years_to_retire + years_retired)
    rng = np.random.default_rng(seed)
    r = np.maximum(rng.normal(real_return, vol, size=(paths, max(years, 1))), -0.95)
    bal = np.full(paths, float(balance))
    track = [bal.copy()]
    for t in range(years):
        flow = contribution if t < years_to_retire else -withdrawal
        bal = np.maximum((bal + flow) * (1 + r[:, t]), 0.0)
        track.append(bal.copy())
    track = np.array(track)
    bands = pd.DataFrame(np.percentile(track, [10, 50, 90], axis=1).T,
                         columns=["Poor markets (10th pct)", "Median", "Strong markets (90th pct)"])
    bands.index.name = "Years from now"
    at_retire = track[int(years_to_retire)]
    return {"bands": bands, "median_at_retirement": float(np.median(at_retire)),
            "p10_at_retirement": float(np.percentile(at_retire, 10)),
            "success": float((track[-1] > 0).mean()) if years_retired else None}


# ------------------------------------------------------------------ upload
def parse_portfolio(text):
    """CSV with a 'ticker' column and either 'weight' (percent or fraction) or 'value' (USD).
    Returns (weights length-7 decimals, total value or None). Unknown tickers are an error:
    the app has no price history to judge them with."""
    df = pd.read_csv(StringIO(text))
    df.columns = [c.strip().lower() for c in df.columns]
    if "ticker" not in df.columns or not ({"weight", "value"} & set(df.columns)):
        raise ValueError("CSV needs a 'ticker' column and a 'weight' or 'value' column.")
    col = "value" if "value" in df.columns else "weight"
    df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()
    amounts = pd.to_numeric(df[col].astype(str).str.replace(r"[$,%\s]", "", regex=True), errors="coerce")
    if amounts.isna().any():
        raise ValueError(f"Every '{col}' must be a number.")
    unknown = sorted(set(df["ticker"]) - set(ASSETS))
    if unknown:
        raise ValueError(f"No data for {', '.join(unknown)}. Supported tickers: {', '.join(ASSETS)}.")
    if (amounts < 0).any():
        raise ValueError("Negative holdings (short positions) are not allowed: the mandate is long-only.")
    totals = amounts.groupby(df["ticker"]).sum()
    if totals.sum() <= 0:
        raise ValueError("Holdings add up to zero.")
    weights = as_vector((totals / totals.sum()).to_dict())
    return weights, (float(totals.sum()) if col == "value" else None)
