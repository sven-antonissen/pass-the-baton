"""Run one Pass the Baton agent.

Each agent lives in agents/<name>/ with:
  instructions.md  the system prompt, in plain language anyone can read
  config.json      model, max_tokens, input files and the one folder it may write to

The agent can only write files inside its own output folder. Its work is
committed on a branch and opened as a pull request by the workflow; nothing
goes live until a human merges it.

Usage:
  python agents/runner.py branding            # call the API and write files
  python agents/runner.py branding --dry-run  # show what would be sent, no API call
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

WRITE_FILES_TOOL = {
    "name": "write_files",
    "description": "Write the agent's output files. Paths are relative to the repository root.",
    "input_schema": {
        "type": "object",
        "properties": {
            "files": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["path", "content"],
                },
            },
            "summary": {
                "type": "string",
                "description": "A short summary of the choices made, used as the pull request description.",
            },
        },
        "required": ["files", "summary"],
    },
}


def fail(msg: str) -> None:
    """Stop with an error that also shows up as an annotation on GitHub Actions."""
    if os.environ.get("GITHUB_ACTIONS"):
        print(f"::error title=Agent failed::{msg}")
    sys.exit(msg)


def load_agent(name: str) -> tuple[str, dict]:
    folder = ROOT / "agents" / name
    if not folder.is_dir():
        sys.exit(f"Unknown agent: {name}")
    instructions = (folder / "instructions.md").read_text(encoding="utf-8")
    config = json.loads((folder / "config.json").read_text(encoding="utf-8"))
    return instructions, config


def build_message(config: dict) -> str:
    parts = []
    for rel in config.get("inputs", []):
        path = ROOT / rel
        if path.is_file():
            parts.append(f'<file path="{rel}">\n{path.read_text(encoding="utf-8")}\n</file>')
        else:
            parts.append(f'<file path="{rel}" missing="true"/>')
    parts.append("Do your task now and return all files in one write_files call.")
    return "\n\n".join(parts)


def safe_path(rel: str, output_dir: str) -> Path:
    """Resolve a path and refuse anything outside the agent's output folder."""
    allowed = (ROOT / output_dir).resolve()
    target = (ROOT / rel).resolve()
    if target != allowed and allowed not in target.parents:
        raise ValueError(f"Refused to write outside {output_dir}/: {rel}")
    return target


def write_outputs(result: dict, output_dir: str) -> list[str]:
    written = []
    for item in result.get("files", []):
        target = safe_path(item["path"], output_dir)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(item["content"], encoding="utf-8")
        written.append(str(target.relative_to(ROOT)))
    return written


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("agent")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    instructions, config = load_agent(args.agent)
    message = build_message(config)

    if args.dry_run:
        print(f"Agent: {args.agent}\nModel: {config['model']}\nWrites to: {config['output_dir']}/")
        print(f"Prompt: {len(instructions)} chars, input: {len(message)} chars")
        return

    import anthropic  # imported here so --dry-run works without the package

    if not os.environ.get("ANTHROPIC_API_KEY"):
        fail("ANTHROPIC_API_KEY is not set. Add it as a repository secret (Settings > Secrets and variables > Actions).")

    client = anthropic.Anthropic()
    try:
        with client.messages.stream(
            model=config["model"],
            max_tokens=config["max_tokens"],
            system=instructions,
            tools=[WRITE_FILES_TOOL],
            messages=[{"role": "user", "content": message}],
        ) as stream:
            response = stream.get_final_message()
    except anthropic.APIStatusError as e:
        fail(f"Claude API error {e.status_code}: {e.message}")
    except anthropic.APIConnectionError as e:
        fail(f"Could not reach the Claude API: {e}")

    if response.stop_reason == "max_tokens":
        fail("The agent ran out of output space; raise max_tokens in config.json.")
    calls = [b for b in response.content if b.type == "tool_use" and b.name == "write_files"]
    if not calls:
        fail("The agent returned no files.")

    result = calls[0].input
    try:
        written = write_outputs(result, config["output_dir"])
    except (ValueError, KeyError, TypeError) as e:
        fail(f"Could not write the agent's files: {e}")

    summary = result.get("summary", "").strip()
    usage = response.usage
    body = (
        f"{summary}\n\n**Files**\n" + "\n".join(f"- `{p}`" for p in written)
        + f"\n\n_Agent: {args.agent} · model: {config['model']} · "
        f"tokens in/out: {usage.input_tokens}/{usage.output_tokens}_\n\n"
        "Review before merging: merging this pull request is the human approval."
    )
    (ROOT / ".agent-pr-body.md").write_text(body, encoding="utf-8")
    print(body)


if __name__ == "__main__":
    main()
