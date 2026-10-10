# Agents

Each agent is a folder with two files anyone can read:

- `instructions.md`: what the agent does and the rules it follows.
- `config.json`: which model it uses, which files it reads, and the **one folder it may write to**.
- `feedback.md` (optional): what the maintainers want changed. The agent reads it on every run, so reviewing a pull request and writing feedback here is how you steer an agent.

`runner.py` runs an agent. The agent can only write inside its own folder; anything else is refused.

## How an agent run works

1. GitHub Actions starts the agent (on a schedule, or by hand under *Actions*).
2. The agent reads its input files and writes its output.
3. The workflow puts the output on a new branch and opens a **pull request**.
4. A maintainer reviews it. **Merging is approving.** Closing is rejecting.

## Agents

| Agent | Phase | Writes to | Runs |
| --- | --- | --- | --- |
| [branding](branding/) | 1 | `brand/` | By hand only (Opus, the most expensive) |
| [localisation](localisation/) | 2 | `translations/` | Orchestrator, while languages are queued; three per run |
| [research](research/) | 2 | `data/countries/` | Orchestrator, while countries are queued; three per run, with web search |
| [partners](partners/) | 3 | `outreach/partners/` | Orchestrator, while researched countries lack partners; two per run, with web search. Drafts only, never sends |
| [media](media/) | 3 | `outreach/media/` | Orchestrator, once a week; news and draft posts, with web search. Drafts only, never publishes |
| [designer](designer/) | 1 | `design/` | Orchestrator, while design briefs are queued; one piece per run (Opus) |
| [webbuilder](webbuilder/) | 1 | `site/` (style and templates only) | Orchestrator, when new artwork, brand files or feedback arrive; the site must build before a PR opens |
| [coordinator](coordinator/) | all | `docs/status/` | Orchestrator, once a week; status report and next steps |

The volunteers agent from the architecture is not built yet: it needs a channel where volunteers sign up (phase 4).

## The orchestrator

[`orchestrator.py`](orchestrator.py) decides which agents to start. It uses plain rules, no AI model, so it costs nothing to run. It runs every six hours and after every merge.

- An agent never starts while its previous pull request is still open: **your review sets the pace**.
- Queue agents (localisation, research, partners) start while their queue has items.
- Media and coordinator start once a week.
- Branding only runs by hand.
- At most `max_agent_runs_per_day` agent runs per day (default 4), counting every route. For a one-off busier day, add it to `max_runs_on_date`.

Settings live in [`orchestrator.json`](orchestrator.json). Set `"paused": true` to stop everything, change the daily budget, or switch an agent to `"auto": false`. Each orchestrator run shows its decisions under *Actions → Orchestrator*.

The website in [`site/`](../site/) is not an agent: it is built from the repository on every merge and published to pass-the-baton.org.

## Costs

Each pull request shows the tokens the run used. To keep costs low: cheaper models for routine work, small batches per run, and infrequent schedules. Pause any agent under *Actions* by disabling its workflow.

## Running locally

```bash
pip install anthropic
export ANTHROPIC_API_KEY=...        # your own key; never commit it
python agents/runner.py branding --dry-run
python agents/runner.py branding
```

## Adding an agent

Copy `branding/`, rewrite `instructions.md`, set `inputs` and `output_dir` in `config.json`, and add a workflow in `.github/workflows/`. Keep each agent to one clear task and one output folder.
