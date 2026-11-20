"""Retirement Mandate Check - Streamlit app.   Run:  python -m streamlit run app.py

AI-use disclosure: built with Claude (Anthropic, Claude Code) as a coding assistant; the
optional in-app chat also uses Claude. The analysis and the decision are the author's.
Education only. Not investment advice. I am not a financial advisor.
"""
import numpy as np
import pandas as pd
import streamlit as st

import coach
import engine as eng

st.set_page_config(page_title="Retirement Mandate Check", page_icon="🧭", layout="wide")

SAMPLE = {"VTI": 0.50, "VT": 0.25, "SCHD": 0.15, "LQD": 0.05, "BIL": 0.05}
VINTAGE_FILE = eng.DATA / "DGS10_vintage_2026-09-30.csv"
LATER_FILE = eng.DATA / "DGS10_downloaded_2026-10-29.csv"


@st.cache_data
def load_inputs():
    prices = eng.load_prices()
    vintage = eng.load_yield_series(VINTAGE_FILE)
    later = eng.load_yield_series(LATER_FILE)
    return prices, vintage, later


def pct(x, digits=1):
    return "n/a" if x is None or pd.isna(x) else f"{x * 100:.{digits}f}%"


def weights_frame(named):
    """{name: weights} -> percent table indexed by fund."""
    df = pd.DataFrame({k: np.asarray(v) * 100 for k, v in named.items()}, index=eng.ASSETS)
    return df.loc[(df.abs() > 1e-9).any(axis=1)]


# ------------------------------------------------------------------ header (two statements)
st.title("🧭 Retirement Mandate Check")
st.info(
    "**AI use:** this app was built with Claude (Anthropic) as a coding assistant, and the optional "
    "chat helper uses Claude. **The analysis and the decision are mine (Brandon Oganovich). "
    "This is education, not investment advice. I am not a financial advisor.** "
    "Clients and scenarios are fictional."
)

prices, vintage, later = load_inputs()
signal = eng.signal_as_of(vintage)

# ------------------------------------------------------------------ sidebar inputs
side = st.sidebar
side.header("1. Client")
preset = side.selectbox("Who is this portfolio for?", list(eng.PRESETS), index=1)
p = eng.default_params(preset)
p["yield_10y"] = signal["value_pct"] / 100
balance = side.number_input("Portfolio value today (USD)", min_value=0.0, value=500_000.0, step=10_000.0)

side.header("2. Portfolio to check")
source = side.radio("Where do the holdings come from?", ["Sample portfolio", "Upload a CSV", "Type the weights"])
current, problem = None, None
if source == "Sample portfolio":
    current = eng.as_vector(SAMPLE)
    side.caption("Sample: 90% stocks. It is deliberately too risky for a near-retiree.")
elif source == "Upload a CSV":
    upload = side.file_uploader("CSV with columns ticker and weight (or value)", type=["csv"])
    side.caption(f"Supported tickers: {', '.join(eng.ASSETS)}. See sample_portfolio.csv.")
    if upload is not None:
        try:
            current, uploaded_value = eng.parse_portfolio(upload.getvalue().decode("utf-8-sig"))
            if uploaded_value:
                balance = uploaded_value
                side.caption(f"Portfolio value taken from the file: ${balance:,.0f}")
        except (ValueError, UnicodeDecodeError, pd.errors.ParserError) as exc:
            problem = f"Could not read that file: {exc}"
else:
    table = pd.DataFrame({"Fund": eng.ASSETS, "Weight %": [SAMPLE.get(a, 0.0) * 100 for a in eng.ASSETS]})
    edited = side.data_editor(table, hide_index=True, disabled=["Fund"], key="typed")
    typed = pd.to_numeric(edited["Weight %"], errors="coerce").fillna(0.0).values / 100
    if typed.min() < 0:
        problem = "Weights cannot be negative (the mandate is long-only)."
    elif abs(typed.sum() - 1) > 0.005:
        problem = f"Weights add up to {typed.sum():.1%}. They must add up to 100%."
    else:
        current = typed / typed.sum()
p["current"] = current

side.header("3. Mandate")
with side.expander("Edit the mandate limits"):
    p["cpi"] = st.number_input("Inflation (CPI) assumption %", 0.0, 10.0, p["cpi"] * 100, 0.1) / 100
    p["real_target"] = st.number_input("Return target above inflation %", 0.0, 10.0, p["real_target"] * 100, 0.5) / 100
    p["equity_max"] = st.number_input("Most allowed in stocks %", 0.0, 100.0, p["equity_max"] * 100, 5.0) / 100
    p["loss_limit"] = st.number_input("Largest acceptable bad-year loss %", 0.0, 50.0, p["loss_limit"] * 100, 1.0) / 100
    p["reserve_min"] = st.number_input("Smallest cash reserve (BIL) %", 0.0, 40.0, p["reserve_min"] * 100, 1.0) / 100
    p["fund_max"] = st.number_input("Most allowed in one fund %", 20.0, 100.0, p["fund_max"] * 100, 5.0) / 100
    p["bench_stock"] = st.number_input("Benchmark: S&P 500 share % (rest in Treasuries)", 0.0, 100.0,
                                       p["bench_stock"] * 100, 10.0) / 100

side.header("4. Assumptions")
with side.expander("Edit the estimates and costs"):
    p["mode"] = "signal" if st.radio(
        "Expected returns come from", ["The 10-year Treasury yield signal", "5-year historical averages"]
    ).startswith("The") else "historical"
    p["equity_premium"] = st.number_input("Stock premium over Treasuries %", -5.0, 10.0, 3.5, 0.5) / 100
    p["credit_spread"] = st.number_input("Corporate bond spread over Treasuries %", 0.0, 5.0, 1.0, 0.25) / 100
    p["advisory_fee"] = st.number_input("Advisory or platform fee % a year", 0.0, 3.0, 0.0, 0.05) / 100
    p["trade_cost_bps"] = st.number_input("Trading cost (basis points of value traded)", 0.0, 200.0, 5.0, 5.0)

# ------------------------------------------------------------------ the helper's question
st.subheader("The helper has one question before it builds a portfolio")
answer = st.radio(
    "If the return target and the loss limit pull in different directions, which should win?",
    ["Growth first: the highest expected return that stays inside every limit",
     "Protection first: the smallest bad-year loss that still reaches the return target"],
    help="This is the open question from my Lab 13 mandate. The app does not choose it for you: "
         "the answer changes which portfolio it builds.",
)
p["priority"] = "growth" if answer.startswith("Growth") else "protect"

if problem:
    st.error(problem)

# ------------------------------------------------------------------ run the process
try:
    base = eng.solve(prices, p)
    stress = eng.stress_run(prices, p, base)
    decision = eng.process_decision(base, stress, p)
except ValueError as exc:
    st.error(f"Input error: {exc}")
    st.stop()

est, cands, rec = base["est"], base["candidates"], base["recommended"]
target = p["cpi"] + p["real_target"]
focus_name = "Your portfolio" if "Your portfolio" in cands else ("Constrained portfolio" if rec else "Equal weight")
focus = cands[focus_name]

tabs = st.tabs(["Overview", "Mandate and portfolios", "Signal", "Stress run", "Recommendation",
                "Retirement outlook", "Changed-input run", "AI helper", "About"])

# ------------------------------------------------------------------ overview
with tabs[0]:
    st.caption(f"Showing: **{focus_name}** for **{preset}**. Decision date {eng.DECISION_DATE}.")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Mandate verdict", "PASS" if focus["verdict"]["passed"] else "FAIL",
              None if focus["verdict"]["passed"] else f"-{len(focus['verdict']['failed'])} rule(s) broken")
    c2.metric("Expected return a year", pct(focus["net_return"]), f"{(focus['net_return'] - target) * 100:+.1f} pts vs target")
    c3.metric("Loss in a bad year (1-in-20)", pct(focus["loss"]),
              f"{(focus['loss'] - p['loss_limit']) * 100:+.1f} pts vs limit", delta_color="inverse")
    expense = float(focus["weights"] @ np.array([eng.FUNDS[a]["expense"] for a in eng.ASSETS])) + p["advisory_fee"]
    c4.metric("Fees a year", f"${expense * balance:,.0f}", f"{expense * 100:.2f}% of the portfolio", delta_color="off")

    left, right = st.columns([3, 2])
    with left:
        st.markdown("**Allocation (% of portfolio)**")
        shown = {focus_name: focus["weights"]}
        if rec is not None and focus_name != "Constrained portfolio":
            shown["Constrained portfolio"] = rec["weights"]
        shown["Benchmark"] = base["benchmark"]["weights"]
        st.bar_chart(weights_frame(shown), stack=False, y_label="% of portfolio")
        mix = pd.DataFrame({name: [w[eng.IS_STOCK].sum(), w[eng.KINDS == "bond"].sum(), w[eng.IS_CASH].sum()]
                            for name, w in shown.items()}, index=["Stocks", "Bonds", "Cash"]) * 100
        st.dataframe(mix.round(1), width="stretch")
    with right:
        st.markdown("**What the helper sees**")
        for line in coach.explain(focus):
            st.markdown("- " + line)
        if current is not None and not focus["verdict"]["passed"]:
            fixed, met = eng.nearest_fix(current, est, p)
            if fixed is None:
                st.warning("No portfolio on the grid satisfies these limits. Loosen a limit in the sidebar.")
            else:
                st.markdown("**Smallest set of trades that brings it inside the mandate**")
                for ticker, change in coach.trades(current, fixed):
                    st.markdown(f"- {'Buy' if change > 0 else 'Sell'} **{abs(change) * 100:.0f}%** {ticker} "
                                f"({eng.FUNDS[ticker]['name']})")
                after = eng.describe(fixed, est, p)
                moved = float(eng.turnover(fixed, current))
                st.caption(
                    f"After the trades: expected return {pct(after['net_return'])}, bad-year loss {pct(after['loss'])}, "
                    f"verdict {after['verdict']['text']}. Turnover {pct(moved)}"
                    + (f", which is above the {pct(p['turnover_max'], 0)} limit and needs committee approval."
                       if moved > p["turnover_max"] else ".")
                    + ("" if met else " The return target cannot be reached inside these limits."))
    st.caption("Expected returns are estimates and the bad-year loss is a statistical estimate "
               "(expected return minus 1.645 x volatility, assuming normal returns). Neither is a promise.")

# ------------------------------------------------------------------ mandate and portfolios
with tabs[1]:
    st.subheader("The mandate")
    st.table(pd.DataFrame({
        "Item": ["Client", "Objective", "Universe", "Benchmark", "Risk measure", "Limits"],
        "This run": [
            preset,
            f"Earn CPI + {pct(p['real_target'])} a year = {pct(target)} nominal, net of fees (CPI assumed {pct(p['cpi'])})",
            ", ".join(eng.UNIVERSE) + " (US stocks, world stocks, dividend stocks, Treasuries, corporate bonds, T-bills)",
            f"{pct(p['bench_stock'], 0)} S&P 500 (VOO) / {pct(1 - p['bench_stock'], 0)} 7-10 year Treasuries (IEF)",
            "Estimated loss in a 1-in-20 bad year = -(expected return - 1.645 x volatility)",
            f"Long-only and fully invested; stocks at most {pct(p['equity_max'], 0)}; one fund at most "
            f"{pct(p['fund_max'], 0)}; cash reserve at least {pct(p['reserve_min'])}; bad-year loss at most "
            f"{pct(p['loss_limit'], 0)}; turnover above {pct(p['turnover_max'], 0)} a year needs approval",
        ]}).set_index("Item"))

    st.subheader("Baselines and the constrained portfolio")
    rows = []
    for name, c in list(cands.items()) + [("Benchmark (reference only)", base["benchmark"])]:
        rows.append({"Portfolio": name, "Verdict": "PASS" if c["verdict"]["passed"] else "FAIL",
                     "Rules broken": "; ".join(c["verdict"]["failed"]) or "none",
                     "Expected return %": round(c["net_return"] * 100, 2), "Volatility %": round(c["vol"] * 100, 2),
                     "Bad-year loss %": round(c["loss"] * 100, 2), "Stocks %": round(c["stock"] * 100, 1)})
    st.dataframe(pd.DataFrame(rows).set_index("Portfolio"), width="stretch")
    if rec is None:
        st.error("No constrained portfolio exists: no mix on the 5-point grid satisfies every limit"
                 + (" and the return target." if p["priority"] == "protect" else "."))
    st.caption("Equal weight = one sixth in each fund. Inverse volatility = each fund weighted by 1 / its volatility. "
               "Constrained portfolio = best mix on a 5-point grid of all 53,130 combinations, for the priority chosen above. "
               "The benchmark holds VOO, which is outside the universe, so it is a yardstick, not a candidate.")
    st.markdown("**Weights (%)**")
    st.dataframe(weights_frame({k: v["weights"] for k, v in cands.items()}).round(1), width="stretch")

    pick = st.selectbox("Show every rule for", list(cands))
    detail = pd.DataFrame(cands[pick]["rules"])
    detail["value"] = (detail["value"] * 100).round(2)
    detail["limit"] = (detail["limit"] * 100).round(2)
    detail["passed"] = detail["passed"].map({True: "pass", False: "FAIL"})
    st.dataframe(detail.rename(columns={"rule": "Rule", "kind": "Type", "value": "Portfolio %", "limit": "Limit %",
                                        "passed": "Result"}).set_index("Rule"), width="stretch")

    st.subheader("How these mixes behaved over the price window")
    lines = {k: v["weights"] for k, v in cands.items()}
    lines["Benchmark"] = base["benchmark"]["weights"]
    lines["S&P 500 (VOO)"] = eng.as_vector({"VOO": 1.0})
    growth, drawdown = eng.history(prices, lines)
    st.line_chart(growth, y_label="Growth of $100")
    st.dataframe(pd.DataFrame({"Worst peak-to-trough fall %": (drawdown * 100).round(1),
                               "Ending value of $100": growth.iloc[-1].round(1)}).T, width="stretch")
    st.caption(f"Monthly rebalancing, {growth.index[0]:%b %Y} to {growth.index[-1]:%b %Y}, before trading costs. "
               "This describes the past; the portfolios were built using risk numbers from the same period, "
               "so it is not an out-of-sample test.")

    st.subheader("Estimates used")
    st.dataframe(pd.DataFrame({
        "Fund": [eng.FUNDS[a]["name"] for a in eng.ASSETS], "Type": eng.KINDS,
        "Expected return %": (est["mu"] * 100).round(2), "Volatility %": (est["vol"] * 100).round(2),
        "Expense ratio %": [round(eng.FUNDS[a]["expense"] * 100, 3) for a in eng.ASSETS]}, index=eng.ASSETS),
        width="stretch")
    st.caption(f"Risk from {est['months']} monthly returns ({est['start']} to {est['end']}). Expense ratios were typed "
               "in by the author and should be verified on each fund's fact sheet.")

# ------------------------------------------------------------------ signal
with tabs[2]:
    st.subheader("Point-in-time signal: the 10-year Treasury yield")
    s1, s2, s3 = st.columns(3)
    s1.metric("Yield known on the decision date", f"{signal['value_pct']:.2f}%",
              f"observation of {signal['observation_date']}", delta_color="off")
    s2.metric(f"Rank in the last {signal['history_years']} years", f"{signal['percentile']:.0f}th percentile",
              f"median {signal['history_median_pct']:.2f}%", delta_color="off")
    naive = float(later.iloc[-1])
    s3.metric("Latest value in a later download", f"{naive:.2f}%",
              f"dated {later.index[-1]:%Y-%m-%d}: NOT usable", delta_color="off")
    st.markdown(
        f"**How the signal is used.** In signal mode the expected return of Treasuries (IEF) is the yield itself, "
        f"corporate bonds (LQD) are the yield plus {pct(p['credit_spread'])}, and stocks are the yield plus "
        f"{pct(p['equity_premium'])}. A higher yield raises what bonds are expected to earn, so the app can reach "
        f"the target with fewer stocks.\n\n"
        f"**Why point-in-time matters.** The decision date is {signal['decision_date']}. The yield for a given day is "
        f"published the next business day, so the newest number that existed then was the "
        f"{signal['observation_date']} reading. A file downloaded later also contains October readings; using them "
        f"would be look-ahead bias.")
    if rec is not None:
        cheat = eng.solve(prices, dict(p, yield_10y=naive / 100))["recommended"]
        if cheat is not None:
            compare = weights_frame({"As-of signal (correct)": rec["weights"], "Look-ahead (wrong)": cheat["weights"]})
            st.dataframe(compare.round(1), width="stretch")
            st.caption(f"Using the later value would have changed {pct(float(eng.turnover(cheat['weights'], rec['weights'])))} "
                       "of the constrained portfolio.")
    st.line_chart(vintage[vintage.index >= "2016-09-30"].rename("10-year Treasury yield %"), y_label="%")

    st.subheader("Data card")
    st.table(pd.DataFrame({"Field": [
        "Series", "Source and link", "What it measures", "Units", "How late it is published", "Is it revised?",
        "Vintage used", "Download date", "Last three values in the file", "Hand check against the FRED page"],
        "Entry": [
            "DGS10",
            "Board of Governors of the Federal Reserve System (H.15), via FRED/ALFRED: "
            "https://fred.stlouisfed.org/series/DGS10",
            "Market yield on US Treasury securities at 10-year constant maturity, quoted on an investment basis",
            "Percent per year, not seasonally adjusted, daily (business days)",
            "The next business day (FRED updates at about 4:15 pm Eastern for the prior day)",
            "Rarely. I use the ALFRED vintage dated on the decision date so a later correction cannot leak in",
            "ALFRED vintage_date=2026-09-30 (data/DGS10_vintage_2026-09-30.csv)",
            "2026-10-29 (UTC), see data/SOURCES.md for URLs and SHA-256 hashes",
            "; ".join(f"{d}: {v:.2f}" for d, v in signal["last_three"]),
            "To be done by the author: see docs/validation-and-ai-use.md",
        ]}).set_index("Field"))

# ------------------------------------------------------------------ stress run
with tabs[3]:
    st.subheader("Stress run: does the answer survive different inputs?")
    (st.error if decision["stop"] else st.warning if decision["call"] == "PILOT" else st.success)(decision["why"])
    st.markdown(
        f"**The condition that stops the process.** The process stops and the recommendation becomes REJECT if "
        f"(a) the base case has no portfolio meeting every limit and the return target, or (b) more than half of "
        f"the {len(stress)} scenarios below have none. One or more failures, or a scenario that moves the weights "
        f"by more than the {pct(p['turnover_max'], 0)} turnover limit, downgrades ADOPT to PILOT.")
    table = pd.DataFrame([{
        "Group": r["group"], "Scenario": r["scenario"], "Compliant": "yes" if r["compliant"] else "NO",
        "Expected return %": None if pd.isna(r["net_return"]) else round(r["net_return"] * 100, 2),
        "Bad-year loss %": None if pd.isna(r["loss"]) else round(r["loss"] * 100, 2),
        "Weights moved vs base %": None if pd.isna(r["shift"]) else round(r["shift"] * 100, 1),
        "Portfolio": "none" if r["weights"] is None else " / ".join(
            f"{a} {w * 100:.0f}" for a, w in zip(eng.ASSETS, r["weights"]) if w > 1e-9),
        "Rule broken": r["failed"]} for r in stress])
    st.dataframe(table.set_index("Scenario"), width="stretch")
    st.caption("Each scenario changes one input and re-runs the whole process: new estimates, new search, new verdict. "
               "'Weights moved' is one-way turnover from the base constrained portfolio.")

# ------------------------------------------------------------------ recommendation
with tabs[4]:
    st.subheader(f"Rule-based suggestion: {decision['call']}")
    st.write(decision["why"])
    st.caption("This is what the app's fixed rule returns. The recommendation in docs/decision-memo.md is the "
               "author's own decision and may differ.")
    ranges = eng.allocation_range(base, stress)
    if ranges is None:
        st.error("No allocation range: the base case has no compliant portfolio.")
    else:
        st.markdown("**Allocation range** (base case, and the lowest and highest weight across compliant stress runs)")
        st.dataframe((ranges * 100).round(0).rename(columns=lambda c: c + " %"), width="stretch")
        stocks = [w[eng.IS_STOCK].sum() for w in [rec["weights"]] + [r["weights"] for r in stress if r["compliant"]]]
        st.write(f"Stocks in total: base {pct(rec['stock'], 0)}, range {pct(min(stocks), 0)} to {pct(max(stocks), 0)}.")
    st.markdown("**Triggers to monitor** (any one sends the portfolio back through this app)")
    st.markdown(
        f"- The 10-year Treasury yield moves 1 point from {signal['value_pct']:.2f}% "
        f"(below {signal['value_pct'] - 1:.2f}% or above {signal['value_pct'] + 1:.2f}%).\n"
        f"- The estimated bad-year loss of the held portfolio rises above {pct(p['loss_limit'], 0)}.\n"
        f"- Stocks drift more than 5 points above the {pct(p['equity_max'], 0)} cap, or cash falls below {pct(p['reserve_min'])}.\n"
        f"- Trailing 12-month return falls more than {pct(p['loss_limit'], 0)}: the loss estimate has failed and the risk model is reviewed.\n"
        f"- The client changes group (for example passes from saving to drawing income), or annually at the rebalance date.")

# ------------------------------------------------------------------ retirement outlook
with tabs[5]:
    st.subheader("Retirement outlook (simulation, today's dollars)")
    preset_years = eng.PRESETS[preset]["years_to_retire"]
    o1, o2, o3, o4 = st.columns(4)
    years_to = o1.number_input("Years until retirement", 0, 50, preset_years)
    years_in = o2.number_input("Years in retirement", 0, 50, 30)
    saving = o3.number_input("Saved each year until then (USD)", 0.0, 1e6, 15_000.0 if preset_years else 0.0, 1_000.0)
    spending = o4.number_input("Withdrawn each year in retirement (USD)", 0.0, 1e7, 40_000.0, 1_000.0)
    which = st.selectbox("Using the portfolio", list(cands), index=list(cands).index(focus_name))
    chosen = cands[which]
    real = chosen["net_return"] - p["cpi"]
    view = eng.outlook(balance, saving, years_to, years_in, spending, real, chosen["vol"])
    m1, m2, m3 = st.columns(3)
    m1.metric("Median balance at retirement", f"${view['median_at_retirement']:,.0f}")
    m2.metric("In poor markets (10th percentile)", f"${view['p10_at_retirement']:,.0f}")
    m3.metric("Chance the money lasts", "n/a" if view["success"] is None else f"{view['success']:.0%}")
    st.line_chart(view["bands"], y_label="Balance, today's dollars")
    st.caption(f"2,000 simulated paths with a fixed random seed. Real return {pct(real)} a year "
               f"(expected {pct(chosen['net_return'])} minus {pct(p['cpi'])} inflation), volatility {pct(chosen['vol'])}. "
               "Returns are drawn from a normal distribution with the same mix held throughout; taxes and Social "
               "Security are not modelled. A simulation is an illustration of a range, not a forecast.")

# ------------------------------------------------------------------ changed-input run
with tabs[6]:
    st.subheader("Changed-input run")
    st.warning("For the Locked Changed-Input Record: write your own prediction in "
               "docs/validation-and-ai-use.md and commit it to GitHub BEFORE pressing the button.")
    options = {"10-year Treasury yield": "yield_10y", "Stock premium over Treasuries": "equity_premium",
               "Most allowed in stocks": "equity_max", "Largest acceptable bad-year loss": "loss_limit",
               "Inflation (CPI) assumption": "cpi", "Advisory or platform fee": "advisory_fee"}
    label = st.selectbox("Input to change", list(options))
    key = options[label]
    new = st.number_input(f"New value % (currently {p[key] * 100:.2f}%)", -5.0, 100.0, round(p[key] * 100, 2), 0.25)
    if st.button("Run with the changed input"):
        after = eng.solve(prices, dict(p, **{key: new / 100}))
        a, b = rec, after["recommended"]
        st.write(f"**{label}: {p[key] * 100:.2f}% -> {new:.2f}%**")
        st.dataframe(pd.DataFrame({
            "Before": ["none" if a is None else a["verdict"]["text"], None if a is None else round(a["net_return"] * 100, 2),
                       None if a is None else round(a["loss"] * 100, 2), None if a is None else round(a["stock"] * 100, 1)],
            "After": ["none" if b is None else b["verdict"]["text"], None if b is None else round(b["net_return"] * 100, 2),
                      None if b is None else round(b["loss"] * 100, 2), None if b is None else round(b["stock"] * 100, 1)]},
            index=["Verdict", "Expected return %", "Bad-year loss %", "Stocks %"]).astype(str), width="stretch")
        if a is not None and b is not None:
            st.dataframe(weights_frame({"Before": a["weights"], "After": b["weights"]}).round(1), width="stretch")
            st.write(f"Weights moved: {pct(float(eng.turnover(b['weights'], a['weights'])))} one-way turnover.")

# ------------------------------------------------------------------ AI helper
with tabs[7]:
    st.subheader("Ask the helper")
    st.markdown("**Built-in coach (no AI model, always available)**")
    for name, c in cands.items():
        with st.expander(f"{name}: {'PASS' if c['verdict']['passed'] else 'FAIL'}"):
            for line in coach.explain(c):
                st.markdown("- " + line)
    st.markdown("**Optional chat with Claude**")
    typed_key = st.text_input("Anthropic API key (not stored; leave blank to use ANTHROPIC_API_KEY)", type="password")
    key_value = coach.api_key(typed_key)
    if not key_value:
        st.caption("No key found, so the chat is off. Everything else in the app works without it.")
    else:
        sheet = coach.facts(base, decision, signal, preset)
        chat = st.session_state.setdefault("chat", [])
        for turn in chat:
            st.chat_message(turn["role"]).write(turn["content"])
        question = st.chat_input("For example: why does my portfolio fail, in simple terms?")
        if question:
            chat.append({"role": "user", "content": question})
            st.chat_message("user").write(question)
            with st.spinner("Thinking..."):
                try:
                    reply, flagged = coach.ask_claude(chat, sheet, key_value)
                except ImportError:
                    reply, flagged = "The 'anthropic' package is not installed. Run: pip install anthropic", []
            if flagged:
                reply += ("\n\n⚠️ Output check: the figures " + ", ".join(flagged) +
                          " are not in the app's calculations. Treat them as unverified.")
            reply += "\n\n_" + coach.DISCLAIMER + "_"
            chat.append({"role": "assistant", "content": reply})
            st.chat_message("assistant").write(reply)
        with st.expander("The facts the AI is given (and nothing else)"):
            st.json(sheet)

# ------------------------------------------------------------------ about
with tabs[8]:
    st.markdown(f"""
**What this is.** A mandate checker for a retirement portfolio. Load a portfolio, pick the client, and the app
tests it against a written mandate, compares it with two simple baselines and a constrained portfolio, stress-tests
the result, and states when the process should stop.

**What it cannot establish.** Future returns. Whether the client's real risk tolerance matches the preset. Taxes,
account types, Social Security, or anything outside the seven funds. A five-year price window ({est['start']} to
{est['end']}) is short, and in it bonds moved with stocks more than usual, which makes bonds look like weak
diversifiers.

**Data.** Month-end adjusted closes from Yahoo Finance (downloaded 2026-10-20 and 2026-10-22) and the 10-year
Treasury yield from FRED/ALFRED (downloaded 2026-10-29). No live feed: every number is as of {eng.DECISION_DATE}.
Sources and file hashes are in data/SOURCES.md.

**AI use.** Claude (Anthropic) was used to write and test the code and to draft the documents. The optional chat
helper calls Claude and is restricted to numbers the app computed. The client choice, universe, signal, helper
design and the final recommendation were decided by the author; see docs/decision-memo.md.

**Not advice.** Educational project for FIN43900 at Purdue. Fictional clients. Not investment, tax or legal advice.
""")
