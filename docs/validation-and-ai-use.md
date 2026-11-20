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

**The prediction below is mine, made without AI, and committed to GitHub before I run the change.** I wrote my answers myself on 2026-11-20 and sent them to Claude, which copied them into this table word for word. Claude did not suggest, check or comment on the prediction. After I confirmed the prediction was committed to GitHub, Claude ran the change and filled in rows 6 to 8 from the app; rows 9 and 10 were drafted by Claude for me to review.

Suggested change (I may pick another in the app's "Changed-input run" tab): inflation (CPI) assumption from 2.50% to 3.50%, near-retiree, growth first, sample portfolio loaded. Do not pick anything already shown in the stress run, because that result is already visible.

Steps, in this order:

1. With AI off, fill in the first five rows below (input, old value, new value, prediction, why).
2. Commit this file to GitHub. Copy the commit link and time into row 6.
3. Only now open the app's "Changed-input run" tab, apply the change and press the button.
4. Fill in the last four rows from the app, then commit again.

| Field | Entry |
|---|---|
| Input changed | Inflation (CPI) assumption. |
| Old value (units) | 2.50% per year. |
| New value (units) | 3.50% per year. |
| My AI-off prediction: direction of stocks %, expected return, verdict | For the near-retiree, growth-first, sample portfolio: (a) Stocks %: Stay the same at 65%. (b) Expected return: Stay the same at approximately 7.27% per year. (c) Verdict: Still PASS. No rule breaks. |
| Why I expect that | Growth first already selects the highest expected return within the portfolio limits, and changing CPI does not change the return estimates or those limits. Higher inflation raises the required nominal return from 5.50% to 6.50%, which remains below the portfolio's 7.27% expected return. |
| Commit link and time of the prediction (before the run) | https://github.com/BrandonOganovich19/AI-In_finance-439-project2/commit/bfaa11a4f2490337260f5417afa2fec19de2983c , 2026-11-20 14:22:13 UTC (08:22 Central). Claude first ran the change after this, at about 14:24 UTC, after confirming the prediction was in this commit. |
| Actual result (from the app) | "Changed-input run" tab, Inflation (CPI) 2.50% -> 3.50%. Constrained portfolio before / after: verdict PASS / PASS; expected return 7.27% / 7.27%; bad-year loss 9.99% / 9.99%; stocks 65.0% / 65.0%; weights 15/20/30/10/10/15 both times (VTI/VT/SCHD/IEF/LQD/BIL); 0.0% turnover. The return target rose from 5.5% to 6.5%. |
| Expected direction vs actual direction | Stocks %: predicted no change, actual no change. Expected return: predicted no change (about 7.27%), actual no change (7.27%). Verdict: predicted still PASS, actual PASS. All three match. |
| Effect on the decision | *(Drafted by Claude from the app's output; Brandon to confirm or edit.)* The base portfolio and the recommendation (pilot) do not change. But the margin shrinks: expected return is now 0.77 points above the 6.5% target instead of 1.77 points above 5.5%. Re-running the stress test at 3.50% CPI, three of twelve scenarios no longer reach the target (stock premium 2 points lower: 5.94%; 10-year yield 1 point lower: 6.35%; all volatilities 25% higher: 6.33%). Before, none failed. Higher inflation makes the plan more fragile, so CPI should be added to the monitoring triggers. |
| If they differ: what I got wrong | *(Drafted by Claude; Brandon to confirm or edit.)* They did not differ. My reasoning held: CPI only moves the return target, not the estimates or the limits, and the target stayed below 7.27%. What I did not predict was the knock-on effect on the stress run (above). |

## 6. AI use

| Date | Tool / model | Used for | How I checked it |
|---|---|---|---|
| 2026-11-16 | Claude Code desktop, Claude Fable 5.2 | Read the assignment; asked me four design questions; wrote `engine.py`, `app.py`, `coach.py`, the tests; drafted README, memo and this record | 23 unit tests including hand-worked cases; **one output I checked myself: ____ (Brandon to fill in, also used in Video 1)** |
| 2026-11-20 | Claude Code desktop, Claude Opus 5.5 | Checked the three DGS10 values against FRED; ran the README in a fresh Python environment; drafted the video scripts (`docs/video-scripts.md`); finished the memo's "Who decided what" table from my answers; copied my AI-off prediction into section 5 word for word; after the prediction was on GitHub, ran the changed input and drafted rows 9 and 10 | I read the scripts and the memo before recording and submitting |
| At run time, optional | Claude Opus 5.5 through the Anthropic API | In-app chat that explains the app's own numbers | Restricted to a facts block; percentages not in the facts are flagged on screen |
| Oct 2026 | ChatGPT / Codex | Labs 13 to 17 (mandate, price downloads, FRED vintages) reused here | Lab verification files |

Decisions I made versus decisions the AI proposed: see the table at the end of `docs/decision-memo.md`.
