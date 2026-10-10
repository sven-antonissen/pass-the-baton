# Status, 2026-10-10

## Where we stand

1. **Identity and website:** brand files exist (`BRAND.md`, palette, typography/handover art, three logo proposals) and PR #2 is merged. The website builds again (last three runs succeeded). No input says which logo was chosen or what is live on the site.
2. **Facts and languages:** 6 country profiles (AR, AU, BE, BR, CA, CN), 15 countries still queued. 10 translation folders (ar, de, es, fr, hi, nl, pt, ru, sw, zh); PR #8 is the next batch. 9 of 15 queued languages are done.
3. **Reach:** `outreach/partners/` and `outreach/media/` are empty. No drafts exist yet. I can't see whether either agent has run.
4. **Scale:** volunteers agent not built (needs a sign-up channel). Not started.
5. **Second line:** not started.

## Waiting for a human

- **PR #8, Localisation agent: new translations** (the only open PR). Needs review: merge to approve, or close to reject. Merging also starts the next batch. I haven't seen its contents.

## Problems

- **Website workflow failed** 3 times today (11:36, 13:42, 13:46 UTC), and 2 runs were cancelled. The three most recent runs (13:51 to 13:55) succeeded. The cause isn't visible to me.
- **Agent runs with no result shown:** coordinator (13:56), research (13:55) and localisation (13:55) have an empty conclusion in the run list. They may still be running; I can't tell.
- **Contradiction:** `translations/nl` exists, but Dutch is not in `agents/localisation/languages.md`. I can't tell where it came from.

## Next steps

1. Maintainer: review and merge or close PR #8.
2. Maintainer: check the earlier Website failures, and confirm the site now shows the manifesto and the translations.
3. Maintainer: confirm whether `translations/nl` is intended. If it is, add it to the language queue.
4. Maintainer: run the partners agent by hand once, since 6 researched countries exist, and review the drafts.
5. Maintainer: run the media agent by hand once. It also runs on Thursdays.

## Decisions needed

- Which logo proposal (1, 2 or 3) is the one to use? No decision is recorded.
- Are there approvers in place for partner and media drafts? The architecture requires two for sensitive messages.
- Is the queue order right? It is G20 first, but it includes Belgium and the Netherlands translation. The file says the order has no special meaning.
