# Video 3: live demo of the app (script and steps)

The live part of Video 3, which must open with the app running. It takes about 2 minutes. Then switch to `video-3-slides.pptx` and read the speaker notes (about 2:30). The total is about 4:30, under the 5:00 limit. If a practice run goes over, skip step 6.

Every number below was checked against the app on 2026-11-20 (near-retiree, sample portfolio, growth first, default assumptions).

## Before you press record

1. Start the app from the project folder and open http://localhost:8501:
   ```
   python -m streamlit run app.py
   ```
2. Sidebar: **Near-retiree (about 8 years to retirement)**, **$500,000**, **Sample portfolio**. Change nothing else.
3. Above the tabs: leave **Growth first** selected.
4. Click the **Overview** tab and scroll to the top.
5. Have `example_upload.csv` on your Desktop (step 6), and `video-3-slides.pptx` open on slide 1 in PowerPoint.
6. Close other browser tabs and notifications.

## Steps and script

### 1. Overview tab: the two statements (about 25 s)
**Do:** start recording on the app. Point at the blue AI-use box at the top.

> This is my Retirement Mandate Check, running live. Two statements first. I used Claude, from Anthropic, through Claude Code, to build and test this app and to draft my documents, and its optional chat helper also calls Claude. The analysis and the decision are mine; this is education, not investment advice, and I am not a financial advisor.

### 2. Overview tab: the client's portfolio fails (about 30 s)
**Do:** point at the four numbers (FAIL, 8.3%, 14.2%, $264), then at "Smallest set of trades" on the right.

> Our client is a near-retiree, about eight years out, with 500,000 dollars. Their portfolio is 90 percent stocks. The app says FAIL: an 8.3 percent expected return, but an estimated 14 percent loss in a one-in-twenty bad year, against a 10 percent limit. On the right it names each broken rule and the smallest fix: sell 25 points of stock funds, and buy Treasury bills and Treasuries.

### 3. Mandate and portfolios tab (about 10 s)
**Do:** click **Mandate and portfolios** and point at the verdict table.

> Every portfolio gets the same eight rules. Equal weight passes, inverse volatility fails, and the constrained portfolio passes at 7.3 percent.

### 4. Stress run tab (about 15 s)
**Do:** click **Stress run** and point at the yellow box, then the table.

> The stress run changes one input at a time. All twelve scenarios still find a passing portfolio, but four move the weights more than 25 percent, so the rule says pilot, not adopt.

### 5. Retirement outlook tab (about 20 s)
**Do:** click **Retirement outlook**. Leave the four inputs as they are (8 years, 30 years, $15,000 saved, $40,000 withdrawn). Read the numbers, then change **Using the portfolio** to **Constrained portfolio**.

> For the client's retirement: today's portfolio gives a median balance of about 901,000 dollars at retirement. Switching to the constrained mix lowers that to 852,000, but raises the poor-markets balance from 561,000 to 596,000. Less upside, a better floor.

### 6. Upload a portfolio (about 20 s, optional)
**Do:** in the sidebar under **Portfolio to check**, choose **Upload a CSV**, click **Browse files**, pick `example_upload.csv` from the Desktop, then click **Overview**.

> Any portfolio can be uploaded. This file holds VOO, which isn't on the approved list, and its bad-year loss is 10.04 percent, so it fails two rules, and the fix sells the VOO.

### 7. Switch to the slides
**Do:** go to PowerPoint, start the slide show on slide 1 ("Recommendation: a 12-month pilot") and read each slide's speaker notes.

## If something goes wrong

- **The page shows an error, or the numbers differ:** check the sidebar is back to Near-retiree, $500,000, Sample portfolio and Growth first, or refresh the page (F5).
- **"This site can't be reached":** the app isn't running. Start it again with the command above.
- **The chance the money lasts:** it shows 71% for today's portfolio and 67% for the constrained mix. If asked, the honest answer is that the fix trades some upside for a better worst case; it does not raise the chance the money lasts.
