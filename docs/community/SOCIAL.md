# Social media: how it works and how to connect an account

## The flow

1. The **social agent** writes three posts into `social/queue/` as a pull request. It runs when fewer than two approved posts are waiting.
2. A maintainer reviews the pull request. Edit the text directly in the pull request if needed. **Merging is approving.**
3. The **publisher** (`social/publish.py`, workflow *Social - publish*) posts the oldest approved item at 10:13 and 18:43 Brussels time, one item per run, then moves it to `social/posted/` with the links to the published posts.
4. To stop posting: disable the *Social - publish* workflow under *Actions*, or delete the files in `social/queue/`.

Platforms without credentials are skipped, so nothing breaks before an account exists.

## Bluesky

1. Create the account at bsky.app, for example `passthebaton.bsky.social`. Later you can use the domain as handle: `@pass-the-baton.org` (Settings → Account → Handle → "I have my own domain"; it asks for one DNS record).
2. Profile: name *Pass the Baton*, the disc emblem (`brand/logo-2.svg`, exported as PNG) as avatar, the share image as banner, and this bio:
   > What applies to the people applies to those who lead them. Non-violent, non-partisan. Posts drafted with AI, approved by a person. pass-the-baton.org
3. Create an **app password**: Settings → Privacy and security → App passwords. Never use the account password.
4. Add two repository secrets (GitHub → Settings → Secrets and variables → Actions):
   - `BLUESKY_HANDLE`: the handle, without @
   - `BLUESKY_APP_PASSWORD`: the app password

## Mastodon

1. Pick a server whose rules allow advocacy accounts and bots that are marked as such; a general server like mastodon.social, or a European one. Create the account.
2. Profile: same name, avatar, banner and bio. Under Preferences → Profile, tick **"This is an automated account"**, which shows a bot label.
3. Preferences → Development → New application: name *Pass the Baton publisher*, scope **only `write:statuses`**. Save, open it and copy *Your access token*.
4. Add two repository secrets:
   - `MASTODON_INSTANCE`: the server address, for example `https://mastodon.social`
   - `MASTODON_TOKEN`: the access token

## Later: other platforms

LinkedIn, Instagram, Facebook and X need business accounts, app reviews or paid API access. Until then, take the approved posts from `social/posted/` and schedule them by hand, or with a scheduling tool.
