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
| [branding](branding/) | 1 | `brand/` | By hand, and on the 1st of each month (Opus, the most expensive) |
| [localisation](localisation/) | 2 | `translations/` | By hand, and when the manifesto or language queue changes; three languages per run |
| [research](research/) | 2 | `data/countries/` | By hand, and every Monday; three countries per run, with web search |

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
