# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

Requires a `.env` file in `research-agent/` with:
```
GOOGLE_API_KEY=your_key_here
```

Free tier: 500 requests/day with `gemini-2.5-flash`, no credit card required.

Install dependencies:
```bash
cd research-agent
pip install -r requirements.txt
```

## Running

```bash
cd research-agent

# Interactive REPL
python agent.py

# Run demo with 3 preset queries (outputs to logs/session.log)
python run_demo.py
```

## Architecture

A LangChain ReAct agent backed by Google Gemini 2.5 Flash. The agent iterates (max 8 rounds) through Thought → Action → Observation cycles, routing actions to one of four tools:

- **web_search** — DuckDuckGo for real-time information
- **wikipedia** — Background/historical lookups
- **calculator** (`tools/calculator.py`) — Math via regex-validated `eval()` with restricted builtins
- **csv_reader** (`tools/csv_reader.py`) — Pattern-matched analysis of `data/sample_data.csv`

**`agent.py`** is the core: initializes the LLM and tools, builds the ReAct agent (pulling prompt from LangChain hub with a local fallback), exposes `run_agent(query)` and `print_trace()`.

**`run_demo.py`** is a batch runner that executes 3 hardcoded queries, logs to `logs/session.log`, and prints a summary table.

The agent captures `intermediate_steps` from the executor to render the full reasoning trace with box-drawing characters in the console output.
