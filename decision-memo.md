# Decision memo: Retirement Mandate Check

**AI use:** I used Claude (Anthropic; Claude Code, model Claude Fable 5.2) to write and test the app and to draft this memo. The optional in-app chat helper also calls Claude.

**Ownership and purpose:** The analysis and the decision are mine (Brandon Oganovich). This is education, not investment advice. I am not a financial advisor. The client is fictional.

To: Investment committee | From: Brandon Oganovich | Decision date: 2026-09-30 | FIN43900 Project 2

## Recommendation

**Pilot** the process for the near-retiree mandate. Do not adopt it as an automatic allocator yet.

The process finds a portfolio that meets every limit and the return target in the base case and in all twelve stress scenarios. But four scenarios move the weights by more than the mandate's 25% turnover limit, so the exact fund weights are not stable enough to trade on without review.

**Committee ask:** approve a 12-month pilot in which the app's output is a starting point reviewed by a person, traded only inside the range below.

## Mandate (from Lab 13, re-written for a retirement client)

| Item | Near-retiree, about 8 years to retirement, $500,000 |
|---|---|
| Objective | CPI + 3.0% a year net of fees = 5.5% nominal with CPI assumed at 2.5% |
| Universe | VTI, VT, SCHD (stocks); IEF, LQD (bonds); BIL (T-bills) |
| Benchmark | 60% S&P 500 (VOO) / 40% 7-10 year Treasuries (IEF) |
| Risk measure | Estimated loss in a 1-in-20 bad year = -(expected return - 1.645 x volatility) |
| Limits | Long-only, fully invested; stocks at most 65%; one fund at most 40%; cash reserve at least 5%; bad-year loss at most 10%; turnover above 25% a year needs approval |

Lab 13's mandate was written for a campus scholarship reserve. I kept its structure (objective, universe, benchmark, risk measure, limits) and re-wrote the numbers for a retirement saver, because that is the user this app is built for.

Lab 13 left one question open for the client: when the return target and the loss tolerance conflict, which wins? The app asks it on screen. This memo uses **growth first** (highest expected return inside every limit). Lab 13's loss statement (S9) could not be tested; here it is defined as the 1-in-20 estimate above so that it can be.

## Results (growth first, signal-based estimates)

| Portfolio | VTI / VT / SCHD / IEF / LQD / BIL % | Expected return | Bad-year loss | Verdict |
|---|---|---:|---:|---|
| Sample client portfolio | 50 / 25 / 15 / 0 / 5 / 5 | 8.33% | 14.25% | **Fail:** stocks 90% > 65%; one fund 50% > 40%; loss > 10% |
| Baseline 1: equal weight | 16.7 each | 6.77% | 8.74% | Pass |
| Baseline 2: inverse volatility | 3 / 3 / 3 / 5 / 4 / 83 | 4.05% | 0% | **Fail:** one fund 83% > 40%; return < 5.5% |
| **Constrained portfolio** | 15 / 20 / 30 / 10 / 10 / 15 | 7.27% | 9.99% | Pass |
| Benchmark 60/40 (reference) | n/a | 7.28% | 11.35% | n/a |

The constrained portfolio beats equal weight by 0.50 points of expected return and sits at the loss limit. It matches the benchmark's expected return with less estimated risk. Fixing the sample portfolio takes these trades: sell 15% VTI and 10% VT, buy 15% BIL and 10% IEF (25% turnover).

## Signal

The 10-year Treasury yield known on the decision date was **5.26%** (observation of 2026-09-29, ALFRED vintage 2026-09-30), the highest reading of the previous ten years. It sets the expected return of bonds directly and of stocks through a 3.5% premium that I assumed. Data card: app tab "Signal".

## Stress run and stop condition

Twelve scenarios, each changing one input: all twelve still produce a compliant portfolio. Expected return ranged from 5.94% (stock premium 2 points lower) to 8.81% (historical averages). Four scenarios moved more than 25% of the portfolio: stock premium 2 points lower (30%), risk from the last 36 or 24 months (45% each), and historical averages instead of the signal (50%).

**Stop condition:** the process stops and the recommendation becomes reject if the base case has no compliant portfolio, or if more than half of the stress scenarios have none. Neither happened.

## Allocation range and triggers

| | Base | Range across compliant runs |
|---|---:|---:|
| Stocks in total | 65% | 40% to 65% |
| VTI | 15% | 0% to 40% |
| VT | 20% | 10% to 30% |
| SCHD | 30% | 0% to 35% |
| IEF | 10% | 0% to 15% |
| LQD | 10% | 0% to 40% |
| BIL | 15% | 5% to 40% |

Stocks stay between 50% and 65% in eleven of the twelve scenarios; only a stock premium 2 points lower pulls them to 40%. The choice of fund within each group is much less stable than the stock/bond/cash split, so I would hold the split and treat the individual fund weights as loose.

Re-run the process, and reverse the pilot if it then fails, when any of these happens:

- the 10-year yield moves 1 point from 5.26% (below 4.26% or above 6.26%);
- the held portfolio's estimated bad-year loss rises above 10%;
- stocks drift above 70%, or cash falls below 5%;
- the trailing 12-month return is worse than -10% (the loss estimate has failed);
- the client starts drawing income, or at the annual rebalance.

## What this cannot establish

The price window is five years and includes 2022. The loss figure assumes normal returns: the constrained mix's worst peak-to-trough fall in the window was 17.3%, larger than its 10% one-year estimate. The 3.5% stock premium and 1.0% credit spread are assumptions, not measurements. Nothing here covers taxes, Social Security or the client's actual tolerance for loss.

## Who decided what

| Decision | Made by |
|---|---|
| Target user (a person checking their retirement outlook), Empower-style layout, upload-a-portfolio feature | Me |
| Client presets offered in the app instead of one fixed client | Me (Claude asked, I chose) |
| Universe of six stock, bond and cash ETFs | Me (Claude recommended, I chose) |
| Signal: 10-year Treasury yield | Me (from three options Claude offered) |
| Helper design: rule-based coach plus optional chat | Me (Claude recommended, I chose) |
| Preset numbers, 3.5% stock premium, 1.0% credit spread, 40% single-fund cap, 5-point grid, the twelve stress scenarios, the stop rule | Proposed by Claude. Claude walked me through each value; I accepted them unchanged (2026-11-20) |
| Growth first versus protection first for this memo | Me: the app asks this question on screen, and I chose growth first |
| Final recommendation (pilot) | The app's stop rule produced it; I reviewed the stress results and accepted it |
| Writing the memo, README and validation record | Drafted by Claude from the app's output; I reviewed them |
| Prediction in the Locked Changed-Input Record | Me, with AI off, committed before the run |
