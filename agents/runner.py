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
    import datetime

    parts = [f"Today's date: {datetime.date.today().isoformat()}"]
    for rel in config.get("inputs", []):
        path = ROOT / rel
        if path.is_file():
            parts.append(f'<file path="{rel}">\n{path.read_text(encoding="utf-8")}\n</file>')
        else:
            parts.append(f'<file path="{rel}" missing="true"/>')
    for rel in config.get("list_dirs", []):
        folder = ROOT / rel
        names = sorted(p.name for p in folder.iterdir()) if folder.is_dir() else []
        parts.append(f'<listing path="{rel}">\n' + "\n".join(names) + "\n</listing>")
    focus = os.environ.get("AGENT_FOCUS", "").strip()
    # Extra inputs per focus item, e.g. "translations/{item}/site.json" for each language code in the focus.
    pattern = config.get("focus_inputs")
    if focus and pattern:
        for item in [x.strip() for x in focus.split(",") if x.strip()]:
            rel = pattern.replace("{item}", item)
            path = ROOT / rel
            if path.is_file():
                parts.append(f'<file path="{rel}">\n{path.read_text(encoding="utf-8")}\n</file>')
    if focus:
        parts.append(f"Focus for this run (overrides the queue order): {focus}")
    parts.append("Do your task now and return all files in one write_files call.")
    return "\n\n".join(parts)


def safe_path(rel: str, output_dir: str) -> Path:
    """Resolve a path and refuse anything outside the agent's output folder."""
    allowed = (ROOT / output_dir).resolve()
    target = (ROOT / rel).resolve()
    if target != allowed and allowed not in target.parents:
        raise ValueError(f"Refused to write outside {output_dir}/: {rel}")
    return target


def check_content(rel: str, content: str) -> None:
    """Refuse output that would break the site: SVG files must be valid XML."""
    if rel.endswith(".svg"):
        import xml.dom.minidom

        try:
            xml.dom.minidom.parseString(content.encode("utf-8"))
        except Exception as e:  # noqa: BLE001 - any parse error means a broken file
            raise ValueError(f"{rel} is not valid SVG: {e}") from e
    if rel.endswith(".json"):
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"{rel} is not valid JSON: {e}") from e


def write_outputs(result: dict, output_dir: str, protect: list[str] | None = None) -> list[str]:
    protected = {(ROOT / p).resolve() for p in (protect or [])}
    written = []
    for item in result.get("files", []):
        check_content(item["path"], item["content"])
        target = safe_path(item["path"], output_dir)
        if target in protected:
            raise ValueError(f"Refused to change a protected file: {item['path']}")
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

    tools = [WRITE_FILES_TOOL]
    search = config.get("web_search")
    if search:
        # Server-side web search; type is in config.json so it can be updated without code changes.
        tools.append({
            "type": search.get("type", "web_search_20250305"),
            "name": "web_search",
            "max_uses": search.get("max_uses", 5),
        })

    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": message}]
    tokens_in = tokens_out = 0
    for _ in range(5):  # a long search turn may pause; continue it a few times at most
        try:
            with client.messages.stream(
                model=config["model"],
                max_tokens=config["max_tokens"],
                system=instructions,
                tools=tools,
                messages=messages,
            ) as stream:
                response = stream.get_final_message()
        except anthropic.APIStatusError as e:
            fail(f"Claude API error {e.status_code}: {e.message}")
        except anthropic.APIConnectionError as e:
            fail(f"Could not reach the Claude API: {e}")
        tokens_in += response.usage.input_tokens
        tokens_out += response.usage.output_tokens
        if response.stop_reason != "pause_turn":
            break
        messages = [messages[0], {"role": "assistant", "content": response.content}]

    if response.stop_reason == "max_tokens":
        fail("The agent ran out of output space; raise max_tokens in config.json.")
    calls = [b for b in response.content if b.type == "tool_use" and b.name == "write_files"]
    if not calls:
        fail("The agent returned no files.")

    result = calls[0].input
    try:
        written = write_outputs(result, config["output_dir"], config.get("protect"))
    except (ValueError, KeyError, TypeError) as e:
        fail(f"Could not write the agent's files: {e}")

    check = config.get("check")
    if check:
        import subprocess

        done = subprocess.run(check, shell=True, cwd=ROOT, capture_output=True, text=True)
        if done.returncode != 0:
            fail(f"The check '{check}' failed after the agent's changes:\n{(done.stdout + done.stderr)[-1500:]}")

    summary = result.get("summary", "").strip()
    body = (
        f"{summary}\n\n**Files**\n" + "\n".join(f"- `{p}`" for p in written)
        + f"\n\n_Agent: {args.agent} · model: {config['model']} · "
        f"tokens in/out: {tokens_in}/{tokens_out}_\n\n"
        "Review before merging: merging this pull request is the human approval."
    )
    (ROOT / ".agent-pr-body.md").write_text(body, encoding="utf-8")
    print(body)


if __name__ == "__main__":
    main()
