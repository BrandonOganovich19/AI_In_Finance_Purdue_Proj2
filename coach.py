"""The in-app helper.

Two layers:
1. A rule-based coach (always on, no key, no network). It only restates numbers the
   engine calculated and applies fixed if-then advice.
2. An optional chat with Claude (Anthropic API). It is given the engine's numbers as its
   only facts, and its reply is checked: any percentage it states that is not in those
   facts is flagged to the reader.

Education only. Not investment advice.
"""
import json
import os
import re

import numpy as np

from engine import ASSETS, FUNDS, UNIVERSE

MODEL = "claude-opus-5-5"
DISCLAIMER = "Educational tool, not investment advice. Check the numbers on the other tabs."

ADVICE = {
    "Stocks at most": "Stocks are above the cap. Sell stock funds and buy bonds (IEF, LQD) or cash (BIL).",
    "Bad-year loss": "The portfolio could lose more in a bad year than the mandate allows. "
                     "Moving money from stocks into Treasuries (IEF) or T-bills (BIL) lowers that loss.",
    "Cash reserve": "There is not enough cash-like reserve. Raise the T-bill fund (BIL).",
    "Any single fund": "One fund is too large a share. Spread it across the other funds of the same type.",
    "Approved universe": "It holds a fund outside the mandate's universe (VOO is the benchmark, not a holding). "
                         "VTI is the closest approved replacement.",
    "Expected return": "The expected return is below the target. It needs more growth assets, "
                       "lower fees, or a lower target agreed with the client.",
    "Fully invested": "The weights do not add up to 100%.",
    "Long-only": "Short positions are not allowed.",
}


def explain(candidate):
    """Plain-English reading of one portfolio's mandate check."""
    if candidate["verdict"]["passed"]:
        return ["Passes every mandate rule that this app can check."]
    lines = []
    for rule in candidate["rules"]:
        if not rule["passed"]:
            hint = next((text for key, text in ADVICE.items() if rule["rule"].startswith(key)), "")
            lines.append(f"**{rule['rule']}**: yours is {rule['value']:.1%}. {hint}")
    return lines


def trades(current, target):
    """Buy/sell list in percentage points of the portfolio, largest first."""
    diff = np.asarray(target) - np.asarray(current)
    rows = [(ASSETS[i], float(d)) for i, d in enumerate(diff) if abs(d) > 1e-9]
    return sorted(rows, key=lambda r: -abs(r[1]))


def facts(base, decision, signal, preset):
    """Everything the chat model is allowed to know, as plain JSON. Percent units."""
    def pct(x):
        return round(float(x) * 100, 2)

    p = base["params"]
    out = {
        "client": preset, "decision_date": signal["decision_date"],
        "ten_year_treasury_yield_pct": signal["value_pct"],
        "mandate": {"return_target_pct": pct(p["cpi"] + p["real_target"]), "cpi_assumption_pct": pct(p["cpi"]),
                    "max_stocks_pct": pct(p["equity_max"]), "max_single_fund_pct": pct(p["fund_max"]),
                    "min_cash_reserve_pct": pct(p["reserve_min"]), "max_bad_year_loss_pct": pct(p["loss_limit"]),
                    "priority": p["priority"]},
        "funds": {a: FUNDS[a]["name"] for a in ASSETS},
        "portfolios": {},
        "process_suggestion": {"call": decision["call"], "reason": decision["why"]},
    }
    for name, c in base["candidates"].items():
        out["portfolios"][name] = {
            "weights_pct": {a: pct(w) for a, w in zip(UNIVERSE + ["VOO"], c["weights"]) if w > 1e-9},
            "expected_return_pct": pct(c["net_return"]), "volatility_pct": pct(c["vol"]),
            "bad_year_loss_pct": pct(c["loss"]), "verdict": c["verdict"]["text"]}
    return out


SYSTEM = """You are the helper inside a student-built retirement portfolio app for a university \
finance course. The reader is not a finance expert.

Answer only from the FACTS block. It holds every number the app calculated. Do not introduce \
any figure, fund, forecast or market view that is not in it; if the answer is not there, say the \
app does not calculate that. Quote numbers exactly as given.

You explain and compare. You do not tell the reader what to buy or sell with their own money, \
and you do not promise outcomes: the returns are estimates and the loss figure is a statistical \
estimate, not a floor. If asked for personal advice, say this is an educational tool and a \
licensed adviser should be consulted.

When the reader's goal is unclear, ask one short question back before answering. Keep answers \
under 150 words, in plain sentences."""


def api_key(typed=""):
    return (typed or os.environ.get("ANTHROPIC_API_KEY", "")).strip()


def ask_claude(history, fact_sheet, key):
    """history: list of {'role','content'}. Returns (reply text, list of unsupported figures)."""
    import anthropic                      # optional dependency, imported only when used

    client = anthropic.Anthropic(api_key=key, timeout=60.0)
    fact_text = json.dumps(fact_sheet, indent=1)
    system = SYSTEM + "\n\nFACTS\n" + fact_text
    try:
        try:
            # 'fallbacks' lets another Claude model answer if a safety filter declines by mistake.
            response = client.beta.messages.create(
                model=MODEL, max_tokens=2000,
                betas=["server-side-fallback-2026-07-01"], fallbacks="default",
                output_config={"effort": "low"}, system=system, messages=history)
        except TypeError:                 # older SDK without these options
            response = client.messages.create(model=MODEL, max_tokens=2000, system=system, messages=history)
    except anthropic.AuthenticationError:
        return "The API key was rejected. Check it and try again.", []
    except anthropic.RateLimitError:
        return "The AI service is busy (rate limit). Try again in a minute.", []
    except anthropic.APIStatusError as exc:
        return f"The AI service returned an error ({exc.status_code}). The built-in coach still works.", []
    except anthropic.APIConnectionError:
        return "Could not reach the AI service. The built-in coach still works offline.", []
    if response.stop_reason == "refusal":
        return "The AI declined to answer that question.", []
    text = "".join(block.text for block in response.content if block.type == "text").strip()
    return text, unsupported_figures(text, fact_text)


def unsupported_figures(reply, fact_text):
    """Output guard: percentages in the reply that do not appear in the facts."""
    known = {round(float(n), 1) for n in re.findall(r"-?\d+(?:\.\d+)?", fact_text)}
    flagged = []
    for n in re.findall(r"(-?\d+(?:\.\d+)?)\s*%", reply):
        if round(abs(float(n)), 1) not in known and round(float(n), 1) not in known:
            flagged.append(n + "%")
    return sorted(set(flagged))
