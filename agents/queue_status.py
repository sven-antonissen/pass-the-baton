"""Print how many items are still waiting in an agent's queue.

Used by the chain workflow: when a maintainer merges an agent's pull request,
the next batch starts only if this prints a number above 0.

  python agents/queue_status.py localisation
  python agents/queue_status.py research
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def queue_items(path: Path) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"^- (.+)$", path.read_text(encoding="utf-8"), re.M)]


def remaining_localisation() -> list[str]:
    codes = [item.split(":", 1)[0].strip() for item in queue_items(ROOT / "agents/localisation/languages.md")]
    done = {p.name for p in (ROOT / "translations").iterdir() if (p / "MANIFESTO.md").exists()}
    return [c for c in codes if c not in done]


def remaining_research() -> list[str]:
    names = queue_items(ROOT / "agents/research/countries.md")
    done = set()
    for f in (ROOT / "data/countries").glob("*.json"):
        try:
            done.add(json.loads(f.read_text(encoding="utf-8")).get("country", "").casefold())
        except json.JSONDecodeError:
            pass
    return [n for n in names if n.casefold() not in done]


def remaining_partners() -> list[str]:
    profiles = {f.stem for f in (ROOT / "data/countries").glob("*.json")}
    folder = ROOT / "outreach/partners"
    done = {f.stem for f in folder.glob("*.md")} if folder.is_dir() else set()
    return sorted(profiles - done)


def main() -> None:
    agent = sys.argv[1] if len(sys.argv) > 1 else ""
    funcs = {
        "localisation": remaining_localisation,
        "research": remaining_research,
        "partners": remaining_partners,
    }
    if agent not in funcs:
        print(0)
        return
    left = funcs[agent]()
    print(len(left))
    print("Remaining: " + ", ".join(left), file=sys.stderr)


if __name__ == "__main__":
    main()
