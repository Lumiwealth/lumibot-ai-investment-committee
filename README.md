# Lumibot AI Investment Committee

A runnable example showing how [Lumibot](https://github.com/Lumiwealth/lumibot) can run multiple AI agents inside a normal Python trading strategy.

Lumibot itself is not only an agent framework. It is a Python trading framework for deterministic strategies, AI-agent strategies, backtesting, paper trading, and live broker execution. This repository focuses on one high-value pattern: an AI investment committee that researches a trade, builds bull and bear cases, checks risk, and can place real Lumibot orders.

Full Lumibot docs: https://lumibot.lumiwealth.com/

Managed no-code path: https://botspot.trade/?utm_source=github&utm_medium=readme&utm_campaign=lumibot_ai_investment_committee

## What This Example Shows

The strategy in this repo uses plain Lumibot code. There is no LangGraph workflow runtime. The full strategy is in [`main.py`](main.py), where the agents are created in `initialize()` and run from the normal `on_trading_iteration()` flow.

This is one concrete agent-flow example rather than a separate framework:

- An evidence researcher gathers market data, indicators, news, SEC fundamentals, SEC filings, and optional FRED macro data.
- A bull case agent builds the strongest long thesis.
- A bear case agent looks for risks, red flags, and reasons to avoid the trade.
- A portfolio manager agent checks cash, positions, open orders, and risk limits before submitting any order.

![AI investment committee workflow](assets/images/investment_committee_architecture.png)

## Why Lumibot Matters Here

Most AI trading demos stop at advice. Lumibot can run the same strategy through a backtest, paper account, or live broker account. That matters because the AI decision can be tested against historical data before it is trusted with real execution.

![Backtest and live parity](assets/images/backtest_to_live_pipeline.png)

Compared with advisory-only agent demos, this example is designed around:

- Backtesting agent decisions over a historical window.
- Point-in-time research tools so backtests do not read future filings, macro revisions, news, or indicators.
- Real Lumibot order creation and submission from the trading-enabled agent only.
- Inspectable artifacts so you can review what the agents saw, why they traded, and which tools were called.

This repository is intentionally narrow. Lumibot itself can also run single-agent flows, hybrid deterministic-plus-agent flows, risk-review flows, model-vs-model committees, and classic deterministic Python strategies.

## How The Strategy Works

The whole example is a normal Lumibot `Strategy` subclass:

```python
class AIInvestmentCommitteeStrategy(Strategy):
    def initialize(self):
        self.sleeptime = "1D"
        self.agents.create(...)

    def on_trading_iteration(self):
        evidence = self.agents["evidence_researcher"].run(...)
        bull = self.agents["bull_researcher"].run(...)
        bear = self.agents["bear_researcher"].run(...)
        decision = self.agents["portfolio_manager"].run(...)
```

On each trading day in the backtest:

1. Lumibot calls `on_trading_iteration()`.
2. The strategy builds a context object with the current simulated datetime, the allowed universe, and risk limits.
3. The evidence researcher runs first. It can call read-only tools for market data, indicators, news, SEC filings, SEC financial statements, and FRED macro data.
4. The bull researcher receives the evidence pack and argues for the best long-only opportunity.
5. The bear researcher receives the evidence pack and bull case, then looks for reasons to avoid or reduce the trade.
6. The portfolio manager receives all three outputs, checks the live/backtest account state, and is the only agent allowed to submit orders.

The important part is that the agents are not outside Lumibot. They are part of the strategy lifecycle. In a backtest, the tools see the simulated date. In paper or live trading, the same strategy code sees the broker account and current market data.

## The Code Path

`main.py` contains both the strategy and the local backtest runner:

- `AIInvestmentCommitteeStrategy.initialize()` creates the four agents.
- `AIInvestmentCommitteeStrategy.on_trading_iteration()` runs the committee.
- The `if __name__ == "__main__"` block runs a Yahoo daily-data backtest from `2026-03-29` to `2026-04-29`.

That bottom runner is only for convenience. The actual strategy is the `AIInvestmentCommitteeStrategy` class, so you can copy that class into a normal Lumibot project or adapt it for paper trading.

## Safety Model

The committee creates three read-only research agents and one trading-enabled portfolio manager:

```python
self.agents.create(
    name="evidence_researcher",
    model="openai/gpt-5.4-mini",
    allow_trading=False,
    system_prompt=research_prompt,
)
self.agents.create(
    name="bull_researcher",
    model="openai/gpt-5.5",
    allow_trading=False,
    system_prompt=bull_prompt,
)
self.agents.create(
    name="bear_researcher",
    model="openai/gpt-5.5",
    allow_trading=False,
    system_prompt=bear_prompt,
)
self.agents.create(
    name="portfolio_manager",
    model="openai/gpt-5.5",
    allow_trading=True,
    system_prompt=portfolio_prompt,
)
```

`allow_trading=False` removes submit, modify, and cancel order tools. It still allows research agents to inspect positions, cash, open orders, historical data, indicators, SEC filings, FRED macro data, memory, and notifications.

## Research Tools

The evidence pack can include:

- Market data and visible historical bars.
- Technical indicators such as RSI, MACD, moving averages, ATR, and trend context.
- Recent Alpaca/Benzinga news when Alpaca credentials are configured.
- SEC income statements, balance sheets, cash flows, company facts, filing lists, filing search, and filing documents.
- FRED macro series when `FRED_API_KEY` is configured.

![SEC fundamentals and point-in-time tools](assets/images/sec_fundamentals_filings.png)

## Repository Layout

This repo is intentionally small:

- `main.py` contains the actual Lumibot strategy plus a small local backtest runner. It imports Lumibot and Python standard-library modules only.
- `.env.example` shows the environment variables you can export before running.
- `assets/images/` contains the README visuals.
- `.venv/`, `__pycache__/`, and any local artifacts are ignored by git.

## Run Locally

![Run the committee locally](assets/images/run_committee_locally.png)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `OPENAI_API_KEY` in your shell, then run:

```bash
export OPENAI_API_KEY=your_openai_key_here
```

If you prefer to keep the values in `.env`, load them into your shell before running:

```bash
set -a
source .env
set +a
```

```bash
python main.py
```

Lumibot prints the backtest summary and writes any configured logs or outputs through the normal Lumibot backtest machinery. The example does not need a custom runner, wrapper script, or local checkout path.

## Models

Each role can use a different model:

```bash
COMMITTEE_RESEARCH_MODEL=openai/gpt-5.4-mini
COMMITTEE_BULL_MODEL=openai/gpt-5.5
COMMITTEE_BEAR_MODEL=openai/gpt-5.5
COMMITTEE_TRADER_MODEL=openai/gpt-5.5
```

Use a cheaper model for evidence gathering and a stronger model for bull, bear, and final portfolio reasoning.

## Artifacts

Backtests leave normal Lumibot artifacts plus AI-specific traces and memory files. Use these to inspect the run after it finishes.

![Backtest result artifact](assets/images/backtest_result_artifact.png)

Common files include:

- Agent prompts and responses.
- Tool calls and tool results.
- Trade decisions and order rationale.
- Memory JSONL files for decisions, lessons, and theses.
- Backtest performance outputs.

## Paper Or Live Trading

Start with the backtest runner. Once the evidence, risk limits, and artifact review look sane, adapt the same `AIInvestmentCommitteeStrategy` to a paper broker using normal Lumibot broker setup. Keep the research, bull, and bear agents read-only, and only enable trading for the portfolio manager.

Never run live trading until you have reviewed orders and risk controls in paper trading.

## Links

- Lumibot: https://github.com/Lumiwealth/lumibot
- Lumibot docs: https://lumibot.lumiwealth.com/
- BotSpot: https://botspot.trade/?utm_source=github&utm_medium=readme&utm_campaign=lumibot_ai_investment_committee
