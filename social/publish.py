"""Publish the oldest approved post from social/queue/ to Bluesky and Mastodon.

A post is in social/queue/ on main only after a maintainer merged it, so
everything here has been approved. Each run posts at most ONE item, so posts
are spread over the day. After posting, the item is moved to social/posted/
with the links to the published posts.

Platforms without credentials are skipped, so this is safe to run before the
accounts exist. Credentials come from repository secrets:

  BLUESKY_HANDLE          e.g. passthebaton.bsky.social
  BLUESKY_APP_PASSWORD    an app password (Settings > Privacy and security > App passwords)
  MASTODON_INSTANCE       e.g. https://mastodon.social
  MASTODON_TOKEN          an access token with the write:statuses scope

  python social/publish.py            # post one item
  python social/publish.py --dry-run  # show what would be posted
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import shutil
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUEUE = ROOT / "social/queue"
POSTED = ROOT / "social/posted"
sys.path.insert(0, str(ROOT / "social"))

import validate  # noqa: E402

BSKY = os.environ.get("BLUESKY_PDS", "https://bsky.social")


def http_json(url: str, payload: dict | None = None, headers: dict | None = None, method: str | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method or ("POST" if data else "GET"))
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "pass-the-baton-publisher/1.0 (+https://pass-the-baton.org)")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode("utf-8")
        return json.loads(body) if body else {}


def full_text(post: dict) -> str:
    text = post["text"].strip()
    link = post.get("link")
    if link and link not in text:
        text = f"{text}\n{link}"
    return text


# ---------- Bluesky ----------

def bluesky_facets(text: str) -> list[dict]:
    """Make links and hashtags clickable. Bluesky counts positions in UTF-8 bytes."""
    facets = []

    def span(m: re.Match) -> dict:
        start = len(text[: m.start()].encode("utf-8"))
        return {"byteStart": start, "byteEnd": start + len(m.group(0).encode("utf-8"))}

    for m in re.finditer(r"https?://[^\s)]+", text):
        facets.append({"index": span(m), "features": [{"$type": "app.bsky.richtext.facet#link", "uri": m.group(0)}]})
    for m in re.finditer(r"(?<![\w#])#(\w+)", text):
        facets.append({"index": span(m), "features": [{"$type": "app.bsky.richtext.facet#tag", "tag": m.group(1)}]})
    return facets


def bluesky_record(post: dict, now: str) -> dict:
    text = full_text(post)
    record = {"$type": "app.bsky.feed.post", "text": text, "createdAt": now, "langs": ["en"]}
    facets = bluesky_facets(text)
    if facets:
        record["facets"] = facets
    if post.get("link"):
        record["embed"] = {
            "$type": "app.bsky.embed.external",
            "external": {
                "uri": post["link"],
                "title": post.get("link_title") or "Pass the Baton",
                "description": post.get("link_description") or "",
            },
        }
    return record


def post_bluesky(post: dict) -> str:
    handle, password = os.environ["BLUESKY_HANDLE"], os.environ["BLUESKY_APP_PASSWORD"]
    session = http_json(f"{BSKY}/xrpc/com.atproto.server.createSession", {"identifier": handle, "password": password})
    now = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    res = http_json(
        f"{BSKY}/xrpc/com.atproto.repo.createRecord",
        {"repo": session["did"], "collection": "app.bsky.feed.post", "record": bluesky_record(post, now)},
        {"Authorization": f"Bearer {session['accessJwt']}"},
    )
    rkey = res["uri"].rsplit("/", 1)[-1]
    return f"https://bsky.app/profile/{handle}/post/{rkey}"


# ---------- Mastodon ----------

def post_mastodon(post: dict, key: str) -> str:
    instance = os.environ["MASTODON_INSTANCE"].rstrip("/")
    res = http_json(
        f"{instance}/api/v1/statuses",
        {"status": full_text(post), "visibility": "public", "language": "en"},
        {"Authorization": f"Bearer {os.environ['MASTODON_TOKEN']}", "Idempotency-Key": key},
    )
    return res.get("url", "")


PUBLISHERS = {
    "bluesky": (("BLUESKY_HANDLE", "BLUESKY_APP_PASSWORD"), lambda p, k: post_bluesky(p)),
    "mastodon": (("MASTODON_INSTANCE", "MASTODON_TOKEN"), post_mastodon),
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    items = sorted(QUEUE.glob("*.json")) if QUEUE.is_dir() else []
    if not items:
        print("Nothing in the queue.")
        return 0
    path = items[0]
    problems = validate.problems_in(path)
    if problems:
        print("Not posting an invalid item:\n" + "\n".join(problems))
        return 1
    post = json.loads(path.read_text(encoding="utf-8"))
    print(f"Next post: {path.name}\n---\n{full_text(post)}\n---")

    results, configured = {}, []
    for platform in post.get("platforms", []):
        needed, publish = PUBLISHERS[platform]
        if not all(os.environ.get(n) for n in needed):
            print(f"{platform}: skipped, no credentials ({', '.join(needed)})")
            continue
        configured.append(platform)
        if args.dry_run:
            print(f"{platform}: would post")
            continue
        try:
            results[platform] = publish(post, path.stem)
            print(f"{platform}: posted {results[platform]}")
        except Exception as e:  # noqa: BLE001 - report and keep the item for the next run
            results[platform] = f"error: {e}"
            print(f"{platform}: FAILED {e}")

    if args.dry_run or not configured:
        return 0
    if all(str(v).startswith("error") for v in results.values()):
        return 1  # nothing went out; keep the item in the queue for the next run

    POSTED.mkdir(parents=True, exist_ok=True)
    post["posted"] = {"at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "links": results}
    (POSTED / path.name).write_text(json.dumps(post, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    path.unlink()
    return 0


if __name__ == "__main__":
    sys.exit(main())
