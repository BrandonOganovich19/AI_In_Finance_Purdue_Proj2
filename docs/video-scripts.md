# Video scripts (drafted by Claude, to be read and adapted by Brandon)

These are speaking scripts, not transcripts. After recording, save what you actually said as `docs/transcript-video-1.txt`, `-2.txt` and `-3.txt` (YouTube's auto-captions are a good start; correct them). Rewrite any line that does not sound like you. Roughly 150 spoken words is one minute.

Every video opens with the same two statements:

> "I used Claude, from Anthropic, through Claude Code, to write and test this app and to draft the documents. The app's optional chat helper also calls Claude. The analysis and the decision are mine. This is education, not investment advice, and I am not a financial advisor."

---

## Video 1: how my system and thinking changed (3:00 max, about 380 words)

**[0:00, face or title slide]** Opening statements (above).

**[0:20]** "I'm Brandon Oganovich, and this is Project 2 for FIN 439. My app is a retirement mandate checker. Someone looking at their retirement outlook uploads their portfolio, and the app checks it against a written mandate: does it reach the return target, is it weighted properly, is the risk inside the limit. If it fails, it shows the smallest set of trades that fixes it, usually by moving money from stocks into bonds and T-bills."

**[0:50] How my thinking changed.** "In Lab 13, a mandate was a document. Here I learned it only matters if every rule can be tested by code. Lab 13's loss rule couldn't be tested, so I turned it into a number: the estimated loss in a one-in-twenty bad year. The second change was about data. Bond returns from 2021 to 2026 were negative, so if I'd trusted historical averages the app would never buy bonds, even for a near-retiree. I used the 10-year Treasury yield as known on the decision date instead, which was 5.26 percent. The third change was about the AI. Claude wrote most of the code, but it asked me questions first: who the client is, what funds are allowed, what kind of helper, which signal. Those choices were mine."

**[1:50] One AI output I checked.** [Do this check yourself before recording.] "Here's one output I checked by hand. The app said the sample portfolio fails, and the fix is: sell 15 percent VTI and 10 percent VT, buy 15 percent BIL and 10 percent IEF. Starting from 50, 25, 15 in stocks, after the trades that's 35 plus 15 plus 15, which is 65 percent in stocks: exactly the cap. The largest fund is 35 percent, under the 40 percent cap. Cash goes from 5 to 20 percent, above the 5 percent minimum. Turnover is 25 percent, right at the limit. So the fix does what the app claims."

**[2:35] Close.** "The honest result is a pilot, not an adoption. The stock-bond split holds up under stress, but the individual fund weights don't. My memo explains why. Thanks."

---

## Video 2: code walkthrough (5:00 max, about 650 words)

**[0:00]** Opening statements.

**[0:20] Layout.** Show the folder in VS Code. "Three Python files. `engine.py` holds every calculation and has no Streamlit in it. `app.py` is only the screen. `coach.py` is the helper. The tests are in `tests/test_engine.py`, and the data, with sources and hashes, is in `data/`."

**[0:50] Data and the signal.** Open `engine.py`, show `FUNDS`, `load_prices`, `signal_as_of`. "Six funds can be held: three stock, two bond, one T-bill. VOO is benchmark-only. `signal_as_of` takes only observations strictly before the decision date, from the ALFRED vintage. That's how I block look-ahead. A test proves the later download gives the same answer."

**[1:30] Estimates.** Show `estimates`. "Expected returns are built from the yield: IEF earns the yield, LQD the yield plus a 1 percent credit spread, stocks the yield plus a 3.5 percent premium, minus each fund's expense ratio. Volatility and correlations come from 59 monthly returns."

**[2:00] Mandate rules.** Show `rule_table`. "Eight rules: fully invested, long-only, approved funds only, cash reserve, stock cap, single-fund cap, bad-year loss, and the return objective. The bad-year loss is minus the expected return plus 1.645 times volatility. Each rule returns pass or fail and the actual number, so the verdict names what broke."

**[2:40] Search and fix.** Show `grid`, `optimise`, `nearest_fix`. "Instead of an optimizer I check every long-only mix in 5 percent steps. That's 53,130 portfolios. Growth-first picks the highest return that passes everything; protection-first picks the lowest loss that still hits the target. `nearest_fix` finds the passing portfolio that needs the least trading."

**[3:20] Stress and stop rule.** Show `stress_scenarios` and `process_decision`. "Twelve scenarios, each changing one input: estimates, the window, costs, constraints. The stop rule: reject if the base case or more than half the scenarios have no passing portfolio; pilot if any fail or the weights move more than 25 percent; otherwise adopt."

**[4:00] Helper and tests.** Show `coach.py`, then run `python -m unittest discover -s tests -v`. "The built-in coach explains each failed rule in plain English. The optional Claude chat only sees a facts block from the app, and any percentage it gives that isn't in the facts is flagged. The 23 tests include hand-worked cases: 50 percent in an 8 percent asset and 50 percent at 3 percent must give 5.5 percent. All pass."

**[4:40] Close.** "Calculation in one file, screen in another, tests on the formulas. Thanks."

---

## Video 3: committee presentation (5:00 max, about 650 words). Must open with the app running live.

Before recording, run `python -m streamlit run app.py` and have the browser open.

**[0:00, app on screen]** Opening statements, said over the live app.

**[0:20] The ask.** "Committee, I'm asking for a 12-month pilot of this process for a near-retiree: about 8 years out, $500,000. The app's output is a starting point reviewed by a person, traded only inside a set range."

**[0:40] Mandate.** Open "Mandate and portfolios". "The objective is inflation plus 3 percent, which is 5.5 percent nominal. Stocks at most 65 percent, any one fund at most 40, cash at least 5, and the estimated loss in a one-in-twenty bad year at most 10 percent. The benchmark is 60/40, the S&P 500 and Treasuries."

**[1:20] The client's portfolio fails.** Overview tab with the sample portfolio. "This sample portfolio is 90 percent stocks, with half of it in one fund. Expected return 8.3 percent, but a bad-year loss of 14 percent. It fails three rules, and the app names them. Here's the fix: sell 25 percent of stock funds, put 15 into T-bills and 10 into Treasuries."

**[2:00] Baselines.** "Against two simple baselines: equal weight passes, with 6.8 percent expected. Inverse volatility fails, because it puts 83 percent in T-bills and misses the return target. The constrained portfolio passes with 7.3 percent and sits right at the 10 percent loss limit. Same expected return as the 60/40 benchmark, with less risk."

**[2:40] Signal.** Signal tab. "Returns are anchored on the 10-year Treasury yield known on September 30: 5.26 percent, the highest in ten years. Here's what a later download would have shown. I don't use it."

**[3:10] Stress.** Stress tab. "Twelve one-change scenarios. All twelve still find a passing portfolio, with expected return between 5.9 and 8.8 percent. But four move the weights more than 25 percent. That's why I say pilot, not adopt."

**[3:40] Recommendation and triggers.** Recommendation tab. "Hold stocks between 40 and 65 percent. Re-run, and reverse the pilot if it then fails, if the 10-year yield moves a full point, the estimated loss goes above 10 percent, stocks drift above 70 percent or cash falls below 5, or the trailing year loses more than 10 percent."

**[4:20] Limits.** "The weak points: five years of data including 2022, a normal-distribution loss estimate (the real worst drawdown was 17 percent), and a stock premium I assumed. No taxes, no Social Security."

**[4:45] Close.** "Approve the pilot, with a person reviewing every trade. Thank you."
