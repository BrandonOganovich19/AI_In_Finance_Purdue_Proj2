# Data sources

No data in this folder is filled, interpolated or synthetic. All files are as of the decision date 2026-09-30 unless stated.

| File | What it is | Source | Downloaded (UTC) | SHA-256 |
|---|---|---|---|---|
| `prices.csv` | Last adjusted close of each month, Oct 2021 to Sep 2026 (60 prices, 59 returns), USD, for VTI, VT, SCHD, IEF, LQD, BIL, VOO | Yahoo Finance chart API, `https://query1.finance.yahoo.com/v8/finance/chart/<TICKER>?period1=1633046400&period2=1790812800&interval=1d&events=div%2Csplits`, field `adjclose` | BIL, IEF, LQD, VT: 2026-10-20. VTI, VOO, SCHD: 2026-10-22 | `1f8d978bbacddbcc6c80e5b87cc6809011aa3d42aea85a0a3891bff676db003b` |
| `DGS10_vintage_2026-09-30.csv` | 10-year Treasury constant-maturity yield as it was known on 2026-09-30 | ALFRED, `https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=DGS10&vintage_date=2026-09-30` | 2026-10-29 | `213908baaefee0ee1b37bcd02cde846fa3c9975a1c9bbfb1f320e2cf4e029ec2` |
| `DGS10_downloaded_2026-10-29.csv` | The same series as it stood on 2026-10-29. Used only to demonstrate look-ahead bias; never used for the decision | FRED, `https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10` | 2026-10-29 | `f3b6b3956f888551c21cfbae007f157bb6433b4db8f557bd7a08b9eb8fd5a97b` |

`prices.csv` is the two price files from Labs 14 and 15 joined on date with no other change (the join required all 60 dates to match one-to-one). Six decimal places are kept. The two yield files are byte-for-byte copies of the Lab 17 downloads.

Adjusted closes include dividends and are net of each fund's expense ratio.

## Expense ratios

Typed in by the author in `engine.py` (`FUNDS`), not downloaded: VTI 0.03%, VT 0.06%, SCHD 0.06%, IEF 0.15%, LQD 0.14%, BIL 0.1356%, VOO 0.03%. **Verify against each fund's current fact sheet before relying on them.**
