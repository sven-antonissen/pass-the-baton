"""Check every post in social/queue/ before it can be reviewed.

Used as the social agent's check, and by the publisher before posting.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUEUE = ROOT / "social/queue"
PLATFORMS = {"bluesky", "mastodon"}
MAX_CHARS = 280  # Bluesky allows 300 graphemes; keep a margin for the link


def post_length(post: dict) -> int:
    text = post.get("text", "")
    link = post.get("link")
    return len(text) + (0 if not link or link in text else len(link) + 1)


def problems_in(path: Path) -> list[str]:
    try:
        post = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"{path.name}: invalid JSON ({e})"]
    out = []
    if not isinstance(post.get("text"), str) or not post["text"].strip():
        out.append(f"{path.name}: missing text")
    elif post_length(post) > MAX_CHARS:
        out.append(f"{path.name}: {post_length(post)} characters with the link, limit {MAX_CHARS}")
    platforms = post.get("platforms") or []
    if not platforms or not set(platforms) <= PLATFORMS:
        out.append(f"{path.name}: platforms must be a non-empty subset of {sorted(PLATFORMS)}")
    link = post.get("link")
    if link is not None and not str(link).startswith("https://"):
        out.append(f"{path.name}: link must start with https://")
    if not isinstance(post.get("sources", []), list):
        out.append(f"{path.name}: sources must be a list")
    return out


def main() -> int:
    problems = []
    for path in sorted(QUEUE.glob("*.json")) if QUEUE.is_dir() else []:
        problems += problems_in(path)
    print("\n".join(problems) or "All queued posts are valid.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
