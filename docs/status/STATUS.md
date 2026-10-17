# Status, 2026-10-17

## Where we stand

1. **Identity and website:** brand files exist (`BRAND.md`, palette, handover art, three logo proposals, favicon). Designer PRs #35 and #37 are merged; #39 and the web builder's #41 are open. No input says which logo was chosen, or whether the site is live with the translations.
2. **Facts and languages:** done as queued. 45 of 45 queued countries have a profile. All 15 queued languages are translated, plus `en` and `nl`.
3. **Reach:** partner files exist for 10 of the 45 researched countries (ar, at, au, bd, be, br, ca, ch, cl, cn). PR #40 is open and may add more. Media has one draft (2026-10-10). The social agent has PR #38 open. Social publishing runs succeeded on 15 and 16 Oct.
4. **Scale:** volunteers agent not built (needs a sign-up channel). Not started.
5. **Second line:** not started.

## Waiting for a human

Oldest first. I haven't seen the contents of any of them.

- **#38 Social agent: posts for review** (13 Oct). Merge to approve posts. Publishing draws on merged posts only.
- **#39 Designer agent: new visual material** (14 Oct). Review the artwork; merge or close.
- **#40 Partners agent: organisations and draft outreach** (14 Oct). Review the drafts. Nothing is sent without approval.
- **#41 Web builder agent: website design update** (15 Oct). Review the design; merge or close.

## Problems

- **Localisation agent failed in 5 runs in a row:** 15 Oct 11:19, 16 Oct 04:21, 11:14, 16:32 and 20:58 UTC. The run on 17 Oct 04:13 shows no result. I can't see the cause.
- **Possible contradiction:** every queued language is already in `translations/`, yet the orchestrator keeps starting the localisation agent. Each start counts against the daily run budget. I can't tell why it starts.
- **Queues look exhausted:** research (45 of 45) and localisation (15 of 15) have nothing left unless entries are added.
- **No result shown** for the media, localisation and coordinator runs of 17 Oct 04:13. They may still be running.
- **`translations/nl`** is still not in `agents/localisation/languages.md`. Its origin is unknown.
- The last partner PR merged on 13 Oct. Media has no draft after 10 Oct, though it should run weekly. No media PR is open; I can't see why.

## Next steps

1. Maintainer: review #38 to #41, oldest first.
2. Maintainer: read the log of a failed localisation run. If the queue is truly done, set localisation to `"auto": false` in `orchestrator.json`, or add new languages.
3. Maintainer: add countries to `agents/research/countries.md` if research should continue.
4. Partners agent: continues on the 35 researched countries without a partner file, once #40 is reviewed.
5. Maintainer: check why the media agent has produced nothing since 10 Oct.

## Decisions needed

- Which logo (1, 2 or 3) is the one to use? No decision is recorded.
- Which languages and countries come next, now that both queues are done?
- Is `nl` meant to be a supported language? If so, add it to the queue file.
- Who are the approvers for partner and media drafts? The architecture requires two for sensitive messages.
