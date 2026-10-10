"""Decide which agents to start now. No AI model, no API cost: plain rules.

The orchestrator workflow runs this every few hours and after every merge. It
prints the agents to start, one per line; the workflow starts them.

Rules (settings in agents/orchestrator.json):
  - Nothing starts while "paused" is true.
  - An agent never starts while it already has an open pull request or a run
    in progress: its previous work must be reviewed first. Merging stays the
    human approval.
  - "queue" agents start while their queue still has items.
  - "every_days" agents start when their folder has had no new file for N days.
  - Agents with "auto": false (branding, the most expensive) only run by hand.
  - At most max_agent_runs_per_day agent runs per UTC day, counting runs
    already started today by any route (schedule, hand, orchestrator).

  python agents/orchestrator.py prs.json runs.json
"""

from __future__ import annotations

import datetime
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import queue_status  # noqa: E402


def workflow_name(agent: str) -> str:
    return f"Agent - {agent}"


def last_commit_age_days(folder: str, today: datetime.date) -> float | None:
    """Days since the last commit touching folder, or None if never."""
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", folder],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    if not out:
        return None
    return (today - datetime.date.fromisoformat(out)).days


def queue_left(agent: str) -> int:
    funcs = {
        "localisation": queue_status.remaining_localisation,
        "research": queue_status.remaining_research,
        "partners": queue_status.remaining_partners,
    }
    return len(funcs[agent]()) if agent in funcs else 0


def decide(settings: dict, prs: list[dict], runs: list[dict], today: datetime.date) -> tuple[list[str], list[str]]:
    """Return (agents to start, reasons log)."""
    log: list[str] = []
    if settings.get("paused"):
        return [], ["Paused in agents/orchestrator.json; nothing started."]

    open_branches = [p.get("headRefName", "") for p in prs]
    agent_workflows = {workflow_name(a) for a in settings["agents"]}
    runs_today = [
        r for r in runs
        if r.get("workflowName") in agent_workflows and str(r.get("createdAt", ""))[:10] == today.isoformat()
    ]
    busy = {r.get("workflowName") for r in runs if r.get("status") in {"queued", "in_progress", "waiting", "pending"}}
    budget = settings.get("max_agent_runs_per_day", 4) - len(runs_today)
    log.append(f"Agent runs today: {len(runs_today)}; budget left: {max(budget, 0)}.")

    start: list[str] = []
    for agent in settings.get("priority", []):
        cfg = settings["agents"].get(agent, {})
        if not cfg.get("auto"):
            log.append(f"{agent}: manual only.")
            continue
        if any(b.startswith(f"agent/{agent}-") for b in open_branches):
            log.append(f"{agent}: waiting for its open pull request to be reviewed.")
            continue
        if workflow_name(agent) in busy:
            log.append(f"{agent}: already running.")
            continue

        rule = cfg.get("rule")
        if rule == "queue":
            left = queue_left(agent)
            if left == 0:
                log.append(f"{agent}: queue done.")
                continue
            reason = f"{left} items left in its queue"
        elif rule == "every_days":
            age = last_commit_age_days(cfg["folder"], today)
            if age is not None and age < cfg.get("days", 7):
                log.append(f"{agent}: last output {age} days ago; next after {cfg.get('days', 7)} days.")
                continue
            reason = "no output yet" if age is None else f"last output {age} days ago"
        else:
            log.append(f"{agent}: unknown rule '{rule}'.")
            continue

        if budget <= 0:
            log.append(f"{agent}: would start ({reason}), but today's run budget is used up.")
            continue
        start.append(agent)
        budget -= 1
        log.append(f"{agent}: START ({reason}).")
    return start, log


def main() -> None:
    settings = json.loads((ROOT / "agents/orchestrator.json").read_text(encoding="utf-8"))
    prs = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")) if len(sys.argv) > 1 else []
    runs = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8")) if len(sys.argv) > 2 else []
    start, log = decide(settings, prs, runs, datetime.datetime.now(datetime.timezone.utc).date())
    print("\n".join(log), file=sys.stderr)
    print("\n".join(start))


if __name__ == "__main__":
    main()
