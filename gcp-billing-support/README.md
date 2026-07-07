# GCP Billing Support Agent with Hermes Self-Evolution

A self-improving GCP billing support agent built with **Google ADK** + **Gemini 3.1 Pro**, automatically evolved using **Hermes GEPA** (Genetic-Pareto Prompt Evolution).

## Results

| Metric | Value |
|--------|-------|
| Baseline accuracy | 53% |
| Evolved accuracy | 70% |
| Improvement | +17 percentage points |
| Evolution cost | ~$10/run vs $2,000/month manual |
| Hermes iterations | 5 |

## Architecture

```
User Query
    │
    ▼
GCP Billing Agent (Google ADK + Gemini 3.1 Pro)
    ├── Cost Analysis Tool        (gcloud billing data)
    ├── Usage Analytics Tool      (BigQuery slot/query data)
    └── Documentation Search      (GCP docs)
    │
    ▼
Specific Response (SKU names, gcloud commands, user attribution)
    │
    │  Interaction traces (JSONL)
    ▼
Hermes GEPA Evolution Loop
    ├── Convert traces → ATIF format
    ├── Generate 5 prompt variants
    ├── Evaluate each on test cases
    └── Deploy best instruction → Agent
```

## Project Structure

```
gcp-billing-support/
├── app/
│   ├── agent.py                          # Main agent with 3 tools
│   └── __init__.py
├── hermes/
│   ├── run_evolution.py                  # Main evolution runner
│   ├── adk_evaluator.py                  # Evaluation adapter
│   ├── convert_traces_to_atif.py         # Trace format converter
│   └── hermes_config.yaml               # Hermes configuration
├── tests/
│   └── eval/
│       └── datasets/
│           └── billing-eval-medium.json  # 15-case eval dataset
├── agents-cli-manifest.yaml
└── pyproject.toml
```

## Quick Start

### Requirements
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- [agents-cli](https://google.github.io/agents-cli/): `uv tool install google-agents-cli`
- GCP project with Vertex AI enabled

### Setup

```bash
cd gcp-billing-support
export GOOGLE_CLOUD_PROJECT=your-project-id
uv sync
```

### Run the playground (web UI)

```bash
# Local:
uvx google-agents-cli playground

# Remote VM (expose to browser):
uvx google-agents-cli playground --host 0.0.0.0 --port 8000
# Open http://VM_EXTERNAL_IP:8000/dev-ui/?app=app
```

### Run evaluation

```bash
uvx google-agents-cli eval run
```

### Run Hermes evolution

```bash
uv run python hermes/run_evolution.py
# Output: hermes/output/evolved_instruction_TIMESTAMP.txt
# Copy the evolved instruction into app/agent.py
```

## Demo Questions

1. *"I'm getting 'Exceeded rate limits: too many concurrent queries' when running my BigQuery ETL. What's happening?"*
2. *"Why did my Compute Engine costs jump from $500 to $1500 last week?"*
3. *"We received a budget alert saying we're at 90% of our monthly budget. What should we do?"*

## How Hermes Evolution Works

1. Reads current system instruction from `app/agent.py`
2. Loads 15 evaluation test cases
3. Scores baseline instruction against eval set
4. Generates 5 variant instructions:
   - Iteration 1: Add specificity (SKU names, exact gcloud commands)
   - Iteration 2: Add structure (5-step response protocol)
   - Iteration 3: Add examples (real billing scenarios)
   - Iteration 4: Add constraints (quality gates)
   - Iteration 5: Combine all improvements
5. Evaluates each variant, selects best
6. Saves evolved instruction to `hermes/output/`

> Hermes GEPA is from [Nous Research](https://github.com/NousResearch/hermes-agent-self-evolution) — ICLR 2026 Oral, MIT licensed.

## Productionization Roadmap

- [ ] Replace simulated tools with real GCP Billing API calls
- [ ] Auto-write evolved instruction back to `agent.py` post-evolution
- [ ] Schedule evolution with Cloud Scheduler (weekly cron)
- [ ] Switch to LLM-as-judge scoring (currently keyword-based)
- [ ] Deploy to Cloud Run via `agents-cli deploy`
- [ ] Add Cloud Trace observability

## Tech Stack

- **Google ADK** — agent framework
- **Gemini 3.1 Pro** — reasoning model (Vertex AI global endpoint)
- **agents-cli** — scaffolding + evaluation framework
- **Hermes GEPA** — evolutionary prompt optimization (Nous Research)
