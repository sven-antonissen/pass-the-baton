# Discord AutoMod setup for the Pass the Baton server

Discord's AutoMod is set up in the app, not with a file. Go to **Server Settings → Safety Setup → AutoMod** and create the rules below. For each rule, choose the response shown; "Send alert" goes to a private `#mod-log` channel that only moderators can see. Create that channel first.

Set **exempt roles** on every rule to `Moderator` (and later `Approver`), so moderators can quote problems while handling them.

## Built-in rules (turn on)

| Rule | Settings | Response |
| --- | --- | --- |
| **Block mention spam** | More than 5 unique mentions per message; turn on raid protection | Block message, send alert, timeout 10 minutes |
| **Block suspected spam content** | On | Block message, send alert |
| **Block commonly flagged words** | All three lists (profanity, sexual content, slurs) | Block message, send alert |

## Custom keyword rules (create)

Discord allows up to six custom rules, each with keywords and regular expressions. Wildcards: `*` at the start or end of a keyword matches partial words.

### 1. Calls for violence

- **Regex** (one per line):
  ```
  \b(kill|shoot|hang|lynch|assassinate|execute)\s+(him|her|them|the\s+(president|king|queen|leader|pm|prime\s+minister))\b
  \b(should|must|deserves?\s+to)\s+(die|be\s+killed)\b
  ```
- **Response:** block message, send alert, timeout 1 hour.
- **Custom message to the member:** "Pass the Baton is non-violent. Your message was blocked and the moderators were alerted."

### 2. Mocking age or health

- **Keywords:** `senile`, `dementia`, `demented`, `geriatric`, `old fart`, `half dead`, `deathbed`, `fossil*`, `dinosaur*`
- **Response:** block message, send alert.
- **Custom message:** "We talk about handing over, not about age as a flaw. Please rephrase."

### 3. Personal data (doxxing protection)

- **Regex:**
  ```
  \+?\d[\d\s().-]{8,}\d
  [\w.+-]+@[\w-]+\.[\w.-]+
  ```
- **Allow list:** `pass-the-baton.org`
- **Response:** block message, send alert.
- **Custom message:** "Please don't share phone numbers or e-mail addresses in public channels. Moderators can help you privately."

### 4. Link shorteners

- **Keywords:** `bit.ly*`, `tinyurl*`, `t.co/*`, `goo.gl*`, `ow.ly*`, `is.gd*`, `cutt.ly*`, `shorturl.at*`
- **Response:** block message.
- **Custom message:** "Please post the full link so everyone can see where it goes."

### 5. Party campaigning

- **Regex:**
  ```
  \b(vote\s+(for|against)|don't\s+vote\s+for|join\s+(the\s+)?party)\b
  ```
- **Response:** send alert only (don't block: it can be legitimate discussion).

### 6. Scam and invite spam

- **Keywords:** `free nitro`, `nitro gift*`, `steamcommunity.ru*`, `discord.gift*`, `airdrop*`, `crypto giveaway*`
- **Regex:** `discord(\.gg|app\.com/invite|\.com/invite)/(?!PASSTHEBATON)\w+` (replace `PASSTHEBATON` with the code of our own invite once it exists)
- **Response:** block message, send alert, timeout 1 day.

## Also set

- **Verification level** (Server Settings → Safety Setup): *Medium*, members must have a verified e-mail and be registered on Discord for longer than 5 minutes.
- **Explicit media content filter:** *Filter messages from all members*.
- **Rules screening / onboarding:** members accept the rules (see below) before they can post.

## Server rules (paste into Onboarding → Rules)

1. **Non-violent, always.** No threats, no calls for harm, no glorifying violence.
2. **Ideas, not people.** Criticise policies and principles, never attack individuals, including leaders.
3. **Respect every generation.** This is about handing over, not about age as a flaw.
4. **Non-partisan.** No campaigning for or against parties or candidates.
5. **Protect each other.** No personal data in public channels. In countries where activism is risky, use a nickname.
6. **No spam or self-promotion.** Share relevant links in the right channel.
7. **Moderators decide.** Follow their guidance; appeal privately if you disagree.
