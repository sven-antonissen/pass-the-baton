# Agents

Each agent is a folder with two files anyone can read:

- `instructions.md`: what the agent does and the rules it follows.
- `config.json`: which model it uses, which files it reads, and the **one folder it may write to**.

`runner.py` runs an agent. The agent can only write inside its own folder; anything else is refused.

## How an agent run works

1. GitHub Actions starts the agent (on a schedule, or by hand under *Actions*).
2. The agent reads its input files and writes its output.
3. The workflow puts the output on a new branch and opens a **pull request**.
4. A maintainer reviews it. **Merging is approving.** Closing is rejecting.

## Agents

| Agent | Phase | Writes to | Runs |
| --- | --- | --- | --- |
| [branding](branding/) | 1 | `brand/` | By hand, and on the 1st of each month |

## Running locally

```bash
pip install anthropic
export ANTHROPIC_API_KEY=...        # your own key; never commit it
python agents/runner.py branding --dry-run
python agents/runner.py branding
```

## Adding an agent

Copy `branding/`, rewrite `instructions.md`, set `inputs` and `output_dir` in `config.json`, and add a workflow in `.github/workflows/`. Keep each agent to one clear task and one output folder.
