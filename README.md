# Retirement Mandate Check

**AI use:** I used Claude (Anthropic; Claude Code desktop app, model Claude Fable 5.2) to write and test the code and to draft these documents. The optional in-app chat helper also calls Claude. Earlier course labs that this project builds on used ChatGPT/Codex.

**Ownership and purpose:** The analysis and the decision are mine (Brandon Oganovich). This is education, not investment advice. I am not a financial advisor. The clients are fictional.

FIN43900 Project 2, Investment Management Application. Decision date for all data: **2026-09-30**.

## What it does

Upload a retirement portfolio and the app checks it against a written mandate: can it earn the required return, is it weighted within the limits, and is the risk acceptable. If it is too risky, the app shows the smallest set of trades (typically stocks into bonds and T-bills) that brings it back inside the mandate.

## Run it

Needs Python 3.10 or newer.

```bash
pip install -r requirements.txt
```

```bash
python -m streamlit run app.py
```

The browser opens at http://localhost:8501. No account, API key or internet connection is needed: all data is in `data/`.

Then:

1. Pick the client in the sidebar (mid-career saver, near-retiree, or already retired).
2. Leave "Sample portfolio" selected, or upload `sample_portfolio.csv`, or your own CSV with columns `ticker` and `weight` (or `value`). Supported tickers: VTI, VT, SCHD, IEF, LQD, BIL, VOO.
3. Answer the helper's question (growth first or protection first).
4. Read the tabs left to right.

Optional chat helper: `pip install anthropic`, then paste an Anthropic API key in the **AI helper** tab or set `ANTHROPIC_API_KEY`. Everything else works without it.

Run the tests:

```bash
python -m unittest discover -s tests -v
```

## Where each requirement is

| # | Requirement | Where |
|---|---|---|
| 1 | The app runs | `app.py`, steps above |
| 2 | Mandate: objective, universe, benchmark, risk measure, limits | Tab **Mandate and portfolios**; `PRESETS` and `rule_table()` in `engine.py` |
| 3 | Two baselines plus my portfolio, each with a verdict | Same tab: Equal weight, Inverse volatility, Constrained portfolio, with pass/fail and the rule broken |
| 4 | One point-in-time signal with its data card | Tab **Signal**; `signal_as_of()` in `engine.py`; `data/SOURCES.md` |
| 5 | Stress run and the stop condition | Tab **Stress run**; `stress_run()` and `process_decision()` |
| 6 | Locked Changed-Input Record | `docs/validation-and-ai-use.md`; run it in tab **Changed-input run** |
| 7 | Recommendation, allocation range, triggers | Tab **Recommendation**; `docs/decision-memo.md` |
| 8 | Two statements | Top of this file, the memo, the app header, and each video |

## Files

| File | Purpose |
|---|---|
| `app.py` | Streamlit screens only |
| `engine.py` | All calculations: estimates, mandate rules, search, stress, outlook, upload parsing |
| `coach.py` | Rule-based helper, optional Claude chat, and the output check on the chat's numbers |
| `tests/test_engine.py` | 23 tests: hand-checked formulas, boundaries, bad inputs, point-in-time |
| `data/` | Month-end prices, two downloads of the 10-year Treasury yield, `SOURCES.md` |
| `docs/` | Decision memo, validation and AI-use record, submission manifest |

## Method in five lines

- **Expected returns:** Treasuries earn the 10-year yield known on the decision date; corporate bonds earn that plus 1.0%; stocks earn it plus 3.5%; cash earns the T-bill fund's trailing 12-month return. Fund expense ratios are subtracted. The two premiums are my assumptions and are editable.
- **Risk:** volatility and correlation from 59 monthly returns (Nov 2021 to Sep 2026). The risk measure is the estimated loss in a 1-in-20 bad year: expected return minus 1.645 x volatility.
- **Constrained portfolio:** every long-only mix of the six funds in 5-point steps (53,130 mixes) is tested against the limits; the best one for the chosen priority is kept.
- **Stress run:** twelve scenarios each change one input (estimates, window, costs, constraints) and re-run everything.
- **Stop condition:** reject if the base case has no compliant portfolio, or if more than half the stress scenarios have none.

## Limits of this app

It cannot tell you future returns, your real risk tolerance, or anything about taxes, account types or Social Security. Five years of prices is a short window, and it includes 2022, when stocks and bonds fell together. The bad-year loss is an estimate under a normal distribution: in the same window the constrained portfolio's worst peak-to-trough fall was larger than its one-year estimate. Expense ratios were typed in by hand and should be verified.
