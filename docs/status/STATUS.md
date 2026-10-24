# Status, 2026-10-24

## Where we stand

1. **Identity and website:** brand files exist (`BRAND.md`, palette, handover art, baton, three logo proposals, favicon). Designer PRs #35, #37, #39 and web builder PR #41 are merged; designer PR #46 is open. No input says which logo was chosen or whether the site is live with the translations.
2. **Facts and languages:** 45 of 45 queued countries have a profile. All 15 queued languages are translated, plus `en` and `nl`. Both queues are done.
3. **Reach:** partner files exist for 14 of the 45 researched countries (ar to eg, alphabetically); PR #45 is open. Media has two drafts (10 and 17 Oct). Social PR #38 is merged and social publishing succeeded on 22 and 23 Oct. Nothing in my input shows what has been sent or published, or the state of the social queue.
4. **Scale:** volunteers agent not built (needs a sign-up channel). Not started.
5. **Second line:** not started.

## Waiting for a human

Oldest first. I haven't seen the contents of either.

- **#45 Partners agent: organisations and draft outreach** (19 Oct, 5 days). Review the drafts; merge to approve, close to reject. Nothing is sent without approval. The partners agent waits for this PR.
- **#46 Designer agent: new visual material** (20 Oct, 4 days). Review the artwork; merge or close. The designer agent waits for this PR.

## Problems

- **Localisation agent keeps failing.** Every localisation run in the visible log failed: 22 Oct 17:04 and 21:28, 23 Oct 04:36, 11:29, 16:58 and 21:19 UTC. Earlier reports listed failures from 15 Oct on. The 24 Oct 04:26 run shows no result. I can't see the cause.
- **Contradiction:** every queued language is already in `translations/`, yet the orchestrator starts localisation at almost every run. I can't tell why. These starts count against the daily run budget.
- **Queues exhausted:** research (45 of 45) and localisation (15 of 15) have nothing left unless entries are added.
- **No result shown** for the media, localisation and coordinator runs of 24 Oct 04:26. They may still be running.
- **`translations/nl`** is still not in `agents/localisation/languages.md`. Its origin is unknown.
- Open issues: none listed.

## Next steps

1. Maintainer: review #45 and #46, oldest first.
2. Maintainer: read the log of a failed localisation run. If the queue is truly done, set localisation to `"auto": false` in `orchestrator.json`, or add new languages.
3. Maintainer: add countries to `agents/research/countries.md` if research should continue.
4. Partners agent: continues on the 31 researched countries without a partner file, once #45 is reviewed.
5. Maintainer: confirm the website is live and shows all translations and the latest design.

## Decisions needed

- Which logo (1, 2 or 3) is the one to use? No decision is recorded.
- Which languages and countries come next, now that both queues are done?
- Is `nl` meant to be a supported language? If so, add it to the queue file.
- Who are the approvers for partner and media drafts? The architecture requires two for sensitive messages.
