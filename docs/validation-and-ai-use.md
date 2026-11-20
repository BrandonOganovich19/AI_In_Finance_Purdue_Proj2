# Validation and AI use

**AI use:** I used Claude (Anthropic; Claude Code, model Claude Fable 5.2) to write and test the app and to draft this record. The optional in-app chat helper also calls Claude.

**Ownership and purpose:** The analysis and the decision are mine (Brandon Oganovich). This is education, not investment advice. I am not a financial advisor.

## 1. Sources and as-of boundary

Decision date: **2026-09-30**. Nothing published after that date is used in a decision.

- Prices: month-end adjusted closes, Oct 2021 to Sep 2026, Yahoo Finance. The last price is the 2026-09-30 close.
- Signal: 10-year Treasury yield (DGS10), ALFRED vintage 2026-09-30. Latest usable observation: 2026-09-29 = 5.26%.
- A later download (2026-10-29, latest value 5.05% for 2026-10-28) is kept only to show what look-ahead would have done.
- URLs, download dates and SHA-256 hashes: `data/SOURCES.md`.

### Data card: DGS10

| Field | Entry |
|---|---|
| Source and link | Board of Governors of the Federal Reserve System, H.15, via FRED: https://fred.stlouisfed.org/series/DGS10 |
| What it measures | Market yield on US Treasury securities at 10-year constant maturity |
| Units | Percent per year, daily, not seasonally adjusted |
| How late it is published | Next business day |
| Revised? | Rarely; the ALFRED vintage for the decision date is used so a correction cannot leak in |
| Download date | 2026-10-29 (UTC) |
| Three values checked against FRED | 2026-09-25: file 5.17, FRED 5.17; 2026-09-28: file 5.24, FRED 5.24; 2026-09-29: file 5.26, FRED 5.26. All match. Checked by me, Brandon Oganovich, on the FRED page (https://fred.stlouisfed.org/series/DGS10) on 2026-11-20. Claude also fetched the same values from `https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10&cosd=2026-09-20&coed=2026-10-02` the same day. |

## 2. Tests

Command: `python -m unittest discover -s tests -v`. Result on 2026-11-16: **23 tests, all pass**.

| What is tested | How |
|---|---|
| Return, volatility, bad-year figure | Two-asset case worked by hand: 50% in an 8%/20%-vol asset and 50% at 3% gives 5.5% return, 10% volatility |
| Costs | 50% turnover at 50 bps and a 0.50% fee reduce return by exactly 1.00 point |
| Limits are inclusive | Stocks at exactly the cap pass; 5 points over fail |
| Verdict names the broken rules | 100% stock portfolio fails four named rules |
| Search | Stock cap binds when it should; loss limit binds when it should (15% by algebra); protect mode finds the 40% minimum; impossible mandate returns nothing |
| Point-in-time | As of 2026-09-30 the signal is the 09-29 value; as of 09-29 it is the 09-28 value; the later download gives the same answer, so look-ahead is blocked |
| Stop condition | An impossible mandate produces REJECT |
| Bad inputs | Missing month in prices, unknown ticker, negative weight, non-numeric weight, wrong columns are all refused with a message |
| Outlook | Zero-risk simulation equals compound interest by hand |
| Chat output check | A percentage that is not in the app's numbers is flagged |

App-level check: the app was run headless (Streamlit `AppTest`) for all three clients, both priorities, all three portfolio sources and the changed-input button with no exceptions, and opened in a browser.

## 3. Results

See `docs/decision-memo.md`. Base case (near-retiree, growth first): constrained portfolio 15/20/30/10/10/15 (VTI/VT/SCHD/IEF/LQD/BIL), expected return 7.27%, bad-year loss 9.99%, passes. All twelve stress scenarios compliant; four exceed the 25% turnover limit. Suggestion: pilot.

## 4. Limitations

- Five-year window containing 2022; bond-stock correlations of 0.5 to 0.8 are higher than longer histories usually show.
- Normal-distribution loss estimate; the historical worst peak-to-trough fall of the constrained mix (17.3%) exceeded it.
- Stock premium (3.5%) and credit spread (1.0%) are assumptions.
- 5-point grid: the true optimum can lie between grid points.
- History chart is in-sample.
- Expense ratios typed by hand, not verified against fact sheets.
- Fresh-environment run (Claude, 2026-11-20): a new Python virtual environment, `pip install -r requirements.txt` (streamlit 1.67.0, pandas 3.1.1, numpy 2.5.5), 23 tests pass, app loads with no errors.
- The first cold run by another person has not been done yet. **Brandon: have someone follow the README on a clean machine and record the first failure here.**

## 5. Locked Changed-Input Record

**This section must be written by me without AI, and committed to GitHub before I run the change.** Claude left it blank on purpose and did not run this change.

Suggested change (I may pick another in the app's "Changed-input run" tab): inflation (CPI) assumption from 2.50% to 3.50%, near-retiree, growth first, sample portfolio loaded. Do not pick anything already shown in the stress run, because that result is already visible.

Steps, in this order:

1. With AI off, fill in the first five rows below (input, old value, new value, prediction, why).
2. Commit this file to GitHub. Copy the commit link and time into row 6.
3. Only now open the app's "Changed-input run" tab, apply the change and press the button.
4. Fill in the last four rows from the app, then commit again.

| Field | Entry |
|---|---|
| Input changed | |
| Old value (units) | |
| New value (units) | |
| My AI-off prediction: direction of stocks %, expected return, verdict | |
| Why I expect that | |
| Commit link and time of the prediction (before the run) | |
| Actual result (from the app) | |
| Expected direction vs actual direction | |
| Effect on the decision | |
| If they differ: what I got wrong | |

## 6. AI use

| Date | Tool / model | Used for | How I checked it |
|---|---|---|---|
| 2026-11-16 | Claude Code desktop, Claude Fable 5.2 | Read the assignment; asked me four design questions; wrote `engine.py`, `app.py`, `coach.py`, the tests; drafted README, memo and this record | 23 unit tests including hand-worked cases; **one output I checked myself: ____ (Brandon to fill in, also used in Video 1)** |
| 2026-11-20 | Claude Code desktop, Claude Opus 5.5 | Checked the three DGS10 values against FRED; ran the README in a fresh Python environment; drafted the video scripts (`docs/video-scripts.md`); finished the memo's "Who decided what" table from my answers | I read the scripts and the memo before recording and submitting |
| At run time, optional | Claude Opus 5.5 through the Anthropic API | In-app chat that explains the app's own numbers | Restricted to a facts block; percentages not in the facts are flagged on screen |
| Oct 2026 | ChatGPT / Codex | Labs 13 to 17 (mandate, price downloads, FRED vintages) reused here | Lab verification files |

Decisions I made versus decisions the AI proposed: see the table at the end of `docs/decision-memo.md`.
