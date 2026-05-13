"""
AI Investment Committee - Multi-Agent Lumibot Demo
--------------------------------------------------

This is a standalone Lumibot strategy. The agents are created in initialize()
and run inside the normal on_trading_iteration() lifecycle.

The workflow:
1. Evidence Researcher gathers market data, indicators, news, SEC fundamentals,
   SEC filings, and FRED macro data.
2. Bull Researcher builds the strongest long-only case.
3. Bear Researcher attacks the trade and identifies risks.
4. Portfolio Manager decides whether to place real Lumibot orders.
"""

import os
from datetime import datetime

from lumibot.backtesting import YahooDataBacktesting
from lumibot.entities import Asset, TradingFee
from lumibot.strategies.strategy import Strategy


DEFAULT_UNIVERSE = ["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA", "SPY", "QQQ"]


class AIInvestmentCommitteeStrategy(Strategy):
    parameters = {
        "universe": DEFAULT_UNIVERSE,
        "max_position_pct": 0.20,
        "max_new_positions_per_run": 2,
        "enable_notifications": False,
    }

    def initialize(self):
        self.sleeptime = "1D"
        self.vars.last_evidence_pack = None
        self.vars.last_bull_case = None
        self.vars.last_bear_case = None

        if self.parameters.get("enable_notifications"):
            self.notifications.enabled = True
            self.notifications.configure_telegram()

        self.agents.create(
            name="evidence_researcher",
            model=os.environ.get("COMMITTEE_RESEARCH_MODEL", "openai/gpt-5.4-mini"),
            allow_trading=False,
            system_prompt=self._evidence_researcher_prompt(),
        )
        self.agents.create(
            name="bull_researcher",
            model=os.environ.get("COMMITTEE_BULL_MODEL", "openai/gpt-5.5"),
            allow_trading=False,
            system_prompt=self._bull_researcher_prompt(),
        )
        self.agents.create(
            name="bear_researcher",
            model=os.environ.get("COMMITTEE_BEAR_MODEL", "openai/gpt-5.5"),
            allow_trading=False,
            system_prompt=self._bear_researcher_prompt(),
        )
        self.agents.create(
            name="portfolio_manager",
            model=os.environ.get("COMMITTEE_TRADER_MODEL", "openai/gpt-5.5"),
            allow_trading=True,
            system_prompt=self._portfolio_manager_prompt(),
        )

    def on_trading_iteration(self):
        universe = list(self.parameters.get("universe") or DEFAULT_UNIVERSE)
        context = {
            "universe": universe,
            "max_position_pct": self.parameters.get("max_position_pct", 0.20),
            "max_new_positions_per_run": self.parameters.get("max_new_positions_per_run", 2),
            "datetime": self.get_datetime().isoformat(),
        }

        evidence = self.agents["evidence_researcher"].run(
            task_prompt=(
                "Build the evidence pack for today's committee. Start with the full universe, "
                "then focus deeply on the best long-only candidates. Use SEC fundamentals, SEC filings, "
                "FRED macro data, news, market data, and indicators before handing off."
            ),
            context=context,
        )
        self.vars.last_evidence_pack = evidence.summary or evidence.text

        bull = self.agents["bull_researcher"].run(
            task_prompt="Build the strongest long-only investment case from the evidence pack.",
            context={**context, "evidence_pack": self.vars.last_evidence_pack},
        )
        self.vars.last_bull_case = bull.summary or bull.text

        bear = self.agents["bear_researcher"].run(
            task_prompt="Attack the long case and identify reasons to avoid, delay, reduce, or monitor the trade.",
            context={
                **context,
                "evidence_pack": self.vars.last_evidence_pack,
                "bull_case": self.vars.last_bull_case,
            },
        )
        self.vars.last_bear_case = bear.summary or bear.text

        decision = self.agents["portfolio_manager"].run(
            task_prompt=(
                "Make the final long-only portfolio decision. Review current positions, cash, open orders, "
                "the evidence pack, bull case, and bear case. Trade only symbols in context.universe. Place orders "
                "only when justified by the evidence and within the risk limits."
            ),
            context={
                **context,
                "evidence_pack": self.vars.last_evidence_pack,
                "bull_case": self.vars.last_bull_case,
                "bear_case": self.vars.last_bear_case,
            },
        )
        self.log_message(f"[investment_committee] {decision.summary}", color="yellow")

    def _evidence_researcher_prompt(self) -> str:
        return """
You are the Evidence Researcher for a Lumibot AI investment committee.

You cannot place, modify, or cancel trades. Build a compact, source-backed evidence pack.

For each candidate symbol, gather:
1. Market context and current/visible historical prices.
2. Technical indicators using get_indicator/get_indicators. Include RSI, MACD, moving averages, volatility/ATR, and trend context when available.
3. Recent news using alpaca_news when credentials are available.
4. SEC fundamentals using get_income_statement, get_balance_sheet, get_cash_flow, and get_company_facts.
5. SEC filings using get_filings. For promising or risky names, use search_filing for risks, margins, debt, liquidity, customers, accounting changes, buybacks, dilution, and management commentary.
6. Macro context using list_fred_series, get_fred_snapshot, and get_fred_latest for rates, inflation, labor, growth, liquidity, credit spreads, and market risk when relevant.
7. Any additional read-only tools needed to reduce uncertainty.

Return JSON-like markdown with candidate symbols reviewed, top long candidates, price/technical summary, fundamental summary, filing highlights, macro regime summary, news/catalyst summary, bull evidence, bear evidence, missing data, and tools used.
"""

    def _bull_researcher_prompt(self) -> str:
        return """
You are the Bull Researcher. You cannot place, modify, or cancel trades.

Build the strongest long-only case from the evidence pack. You may use read-only tools to dig deeper.
Focus on catalysts, fundamentals, technical setup, filing evidence, market regime, and why the reward is worth the risk.

Return the strongest buy candidates, thesis, evidence, catalysts, accepted risks, invalidation points, and monitoring points.
"""

    def _bear_researcher_prompt(self) -> str:
        return """
You are the Bear Researcher. You cannot place, modify, or cancel trades.

Attack the long case. Find reasons the portfolio manager should avoid, delay, reduce size, or demand more evidence.
Look for valuation risk, technical weakness, bad filing details, balance-sheet issues, deteriorating cash flow, crowding, liquidity risk, and missing data.

Return strongest objections, downside catalysts, contradictory evidence, red flags, and conditions that would make the trade acceptable.
"""

    def _portfolio_manager_prompt(self) -> str:
        return """
You are the Portfolio Manager for a long-only Lumibot strategy.

You may place real Lumibot orders, but only within the strategy risk limits. Before trading:
1. Check current portfolio, positions, open orders, and prices.
2. Review the evidence pack, bull case, and bear case.
3. Respect max_position_pct and max_new_positions_per_run from context.
4. Trade only symbols in context.universe.
5. Do not short. Do not use options in this v1 committee example.
6. Prefer doing nothing when evidence is weak or contradictory.
7. If you trade, use remember_decision and optionally notify_user.

Return the final decision, orders submitted if any, sizing rationale, risk controls applied, why the bear case was accepted or rejected, and monitoring points.
"""


if __name__ == "__main__":
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("Set OPENAI_API_KEY in your shell environment before running this example.")

    trading_fee = TradingFee(percent_fee=0.001)
    AIInvestmentCommitteeStrategy.backtest(
        YahooDataBacktesting,
        backtesting_start=datetime(2026, 3, 29),
        backtesting_end=datetime(2026, 4, 29),
        benchmark_asset=Asset("SPY", Asset.AssetType.STOCK),
        buy_trading_fees=[trading_fee],
        sell_trading_fees=[trading_fee],
        quote_asset=Asset("USD", Asset.AssetType.FOREX),
        budget=10000,
        quiet_logs=False,
    )
