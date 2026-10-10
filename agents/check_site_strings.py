"""Check that every translations/<code>/site.json has the same keys and placeholders as English.

Used as the localisation agent's check: a pull request only opens if this passes.
When AGENT_FOCUS lists language codes, only those languages are checked.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLACEHOLDER = re.compile(r"\{[a-z_]+\}")


def main() -> int:
    en = json.loads((ROOT / "translations/en/site.json").read_text(encoding="utf-8"))
    problems = []
    focus = {x.strip() for x in os.environ.get("AGENT_FOCUS", "").split(",") if x.strip()}
    for f in sorted((ROOT / "translations").glob("*/site.json")):
        if f.parent.name == "en" or (focus and f.parent.name not in focus):
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            problems.append(f"{f}: invalid JSON ({e})")
            continue
        missing = sorted(set(en) - set(data))
        if missing:
            problems.append(f"{f}: missing keys {', '.join(missing)}")
        for key, value in en.items():
            want = set(PLACEHOLDER.findall(value))
            have = set(PLACEHOLDER.findall(str(data.get(key, ""))))
            if key in data and want != have:
                problems.append(f"{f}: placeholders in '{key}' should be {sorted(want)}, got {sorted(have)}")
    print("\n".join(problems) or "All site.json files match the English keys and placeholders.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
