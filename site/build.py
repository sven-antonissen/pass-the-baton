"""Build the Pass the Baton website into _site/.

Static HTML only: no server, no tracking, no cookies. The content comes from
the repository itself, so whatever the agents add through merged pull requests
(brand artwork, translations) appears on the next deploy.

  pip install markdown
  python site/build.py
"""

from __future__ import annotations

import datetime
import html
import json
import re
import shutil
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_site"
REPO_URL = "https://github.com/sven-antonissen/pass-the-baton"
DOMAIN = "pass-the-baton.org"

RTL = {"ar", "he", "fa", "ur"}
LANG_NAMES = {
    "en": "English", "nl": "Nederlands", "es": "Español", "fr": "Français",
    "de": "Deutsch", "pt": "Português", "ar": "العربية", "hi": "हिन्दी",
    "zh": "中文", "ru": "Русский", "sw": "Kiswahili", "id": "Bahasa Indonesia",
    "ja": "日本語", "tr": "Türkçe", "it": "Italiano", "pl": "Polski", "ko": "한국어",
}

CSS = """
:root{--ink:#111318;--paper:#F6F3EC;--amber:#F5A623;--glint:#FFF4DC;--shadow:#6B3B04;--muted:#4A4F5C;
--head:'Archivo Black','Arial Black',system-ui,sans-serif;--body:Inter,'Noto Sans',system-ui,sans-serif}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);font:400 18px/1.55 var(--body)}
a{color:var(--shadow)}a:hover{color:var(--ink)}
.wrap{max-width:1080px;margin:0 auto;padding:0 20px}
header.top{background:var(--ink);color:var(--paper)}
header.top .wrap{display:flex;align-items:center;justify-content:space-between;gap:16px;min-height:64px;flex-wrap:wrap}
.brand{display:flex;align-items:center;gap:10px;color:var(--paper);text-decoration:none;font:400 20px var(--head);letter-spacing:-.01em}
.brand img{width:34px;height:34px}
nav a{color:var(--paper);text-decoration:none;font-weight:600;font-size:15px;margin-left:18px;opacity:.85}nav a:hover{opacity:1;color:var(--amber)}
.hero{background:var(--ink);color:var(--paper);padding:24px 0 56px}
.hero .art{width:100%;border-radius:16px;display:block;aspect-ratio:16/9;object-fit:cover}
.hero h1{font:400 clamp(36px,7vw,72px)/1.02 var(--head);letter-spacing:-.01em;margin:32px 0 16px;max-width:15ch}
.hero p.lead{font-size:clamp(18px,2.4vw,22px);max-width:60ch;margin:0 0 28px;opacity:.92}
.btn{display:inline-block;padding:14px 22px;border-radius:999px;font-weight:600;text-decoration:none;margin:0 10px 10px 0}
.btn.primary{background:var(--amber);color:var(--ink)}.btn.primary:hover{background:var(--glint);color:var(--ink)}
.btn.ghost{border:2px solid var(--paper);color:var(--paper)}.btn.ghost:hover{background:var(--paper);color:var(--ink)}
section{padding:64px 0}
h2{font:400 clamp(28px,4vw,36px)/1.1 var(--head);margin:0 0 24px}
h3{font:400 22px/1.2 var(--head);margin:0 0 8px}
.demand{background:var(--glint);border-left:8px solid var(--amber);padding:24px 28px;border-radius:0 12px 12px 0;font-size:clamp(20px,2.6vw,26px);font-weight:600;max-width:46ch}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:20px}
.card{background:#fff;border-radius:16px;padding:24px;border:1px solid #e6e0d2}
.card p{margin:0;color:var(--muted)}
.baton-band{background:var(--ink);color:var(--paper)}
.baton-band img{width:100%;display:block;border-radius:16px}
.langs a{display:inline-block;margin:0 8px 10px 0;padding:8px 14px;border-radius:999px;background:#fff;border:1px solid #e6e0d2;text-decoration:none;color:var(--ink);font-weight:600}
.langs a:hover{border-color:var(--amber)}
article.doc{max-width:760px;margin:0 auto;padding:48px 20px 72px}
article.doc h1{font:400 clamp(32px,5vw,52px)/1.05 var(--head);margin:0 0 24px}
article.doc h2{margin-top:48px}
article.doc table{border-collapse:collapse;width:100%;font-size:16px;margin:16px 0;display:block;overflow-x:auto}
article.doc th,article.doc td{border-bottom:1px solid #ddd5c4;padding:10px 12px;text-align:start;vertical-align:top}
article.doc th{background:var(--glint)}
article.doc.wide{max-width:1080px}
.tag{display:inline-block;padding:2px 10px;border-radius:999px;background:#e9e4d8;font-size:14px;font-weight:600;white-space:nowrap}
.tag.on{background:var(--amber);color:var(--ink)}
small{color:var(--muted)}
footer{background:var(--ink);color:var(--paper);padding:32px 0;font-size:15px}
footer a{color:var(--amber)}
@media (max-width:600px){nav a{margin:0 14px 0 0}body{font-size:17px}section{padding:48px 0}}
"""

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Archivo+Black&family=Inter:wght@400;600&display=swap" rel="stylesheet">')


def page(title: str, body: str, lang: str = "en", depth: int = 0, description: str = "") -> str:
    up = "../" * depth
    direction = "rtl" if lang in RTL else "ltr"
    favicon = f'<link rel="icon" href="{up}brand/favicon.svg" type="image/svg+xml">' if (ROOT / "brand/favicon.svg").exists() else ""
    logo = f'<img src="{up}brand/favicon.svg" alt="">' if favicon else ""
    desc = html.escape(description or "What applies to the people should apply to those who lead them.")
    return f"""<!doctype html>
<html lang="{lang}" dir="{direction}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{desc}">
{favicon}
{FONTS}
<style>{CSS}</style>
</head>
<body>
<header class="top"><div class="wrap">
<a class="brand" href="{up}index.html">{logo}Pass the Baton</a>
<nav><a href="{up}manifesto/">Manifesto</a><a href="{up}countries/">Countries</a><a href="{up}index.html#languages">Languages</a><a href="{REPO_URL}">Help build it</a></nav>
</div></header>
{body}
<footer><div class="wrap">
Pass the Baton is non-violent, non-partisan and open source. No tracking, no cookies.
Texts under <a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a>, code under <a href="{REPO_URL}/blob/main/LICENSE">AGPL-3.0</a>.
<a href="{REPO_URL}">Source on GitHub</a>.
</div></footer>
</body>
</html>
"""


def md_to_html(text: str) -> str:
    return markdown.markdown(text, extensions=["tables", "sane_lists"])


def first_heading(text: str, fallback: str) -> str:
    m = re.search(r"^#\s+(.+)$", text, re.M)
    return m.group(1).strip() if m else fallback


def languages() -> list[str]:
    folder = ROOT / "translations"
    found = sorted(p.name for p in folder.iterdir() if (p / "MANIFESTO.md").exists()) if folder.is_dir() else []
    return ["en"] + found


def home() -> str:
    has_art = (ROOT / "brand/handover.svg").exists()
    has_baton = (ROOT / "brand/baton.svg").exists()
    art = '<img class="art" src="brand/handover.svg" alt="An older hand passing a lifelike amber relay baton to a younger hand">' if has_art else ""
    baton = (
        '<section class="baton-band"><div class="wrap">'
        '<img src="brand/baton.svg" alt="A lifelike amber relay baton">'
        "</div></section>"
    ) if has_baton else ""
    langs = "".join(
        f'<a href="{"manifesto/" if code == "en" else code + "/"}" lang="{code}">{LANG_NAMES.get(code, code)}</a>'
        for code in languages()
    )
    body = f"""
<div class="hero"><div class="wrap">
{art}
<h1>Passing it on is leadership.</h1>
<p class="lead">All over the world, people hand their work to the next generation at a certain age. We ask leaders to do the same. Not out of distrust of older people, but out of respect for renewal.</p>
<a class="btn primary" href="manifesto/">Read the manifesto</a>
<a class="btn ghost" href="{REPO_URL}">Help build it</a>
</div></div>

<section><div class="wrap">
<h2>The demand</h2>
<p class="demand">Anyone who has reached the statutory retirement age of their own country, and at the latest 67, does not start a new term in one of the highest offices.</p>
<p>It applies worldwide, in every country and under every regime, starting with heads of state, heads of government and ministers. A term already under way may be completed. Ordinary citizens remain free to keep working.</p>
<p><a href="countries/">See how countries compare</a>, with sources for every fact.</p>
</div></section>

<section style="padding-top:0"><div class="wrap">
<h2>Why</h2>
<div class="grid">
<div class="card"><h3>A double standard</h3><p>A nurse, a builder or a teacher hands over their work. Those who decide over millions of lives often stay until the very end.</p></div>
<div class="card"><h3>A short horizon</h3><p>Decisions on climate, debt and pensions mostly affect generations who will bear the consequences themselves.</p></div>
<div class="card"><h3>Renewal is blocked</h3><p>Those who never leave make no room for new ideas, new people and new energy.</p></div>
<div class="card"><h3>Respect for experience</h3><p>Experience stays valuable, as adviser, mentor or ambassador. Passing the baton is an act of leadership, not a defeat.</p></div>
</div>
</div></section>

{baton}

<section id="languages"><div class="wrap">
<h2>Read it in your language</h2>
<div class="langs">{langs}</div>
<p>Missing yours? <a href="{REPO_URL}/blob/main/CONTRIBUTING.md">Help translate it</a>.</p>
</div></section>

<section style="padding-top:0"><div class="wrap">
<h2>Pass it on</h2>
<p>Hand a baton to someone, in real life or online, and share it with <strong>#PassTheBaton</strong>. Non-violent, non-partisan, open to everyone.</p>
<a class="btn primary" href="{REPO_URL}">Join on GitHub</a>
</div></section>
"""
    return page("Pass the Baton: passing it on is leadership", body)


def doc_page(md_file: Path, lang: str, depth: int) -> str:
    text = md_file.read_text(encoding="utf-8")
    title = first_heading(text, "Pass the Baton")
    body = f'<article class="doc" lang="{lang}">{md_to_html(text)}</article>'
    return page(title, body, lang=lang, depth=depth)


def load_countries() -> list[dict]:
    out = []
    for f in sorted((ROOT / "data/countries").glob("*.json")):
        try:
            out.append(json.loads(f.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    return sorted(out, key=lambda c: c.get("country", ""))


def age_on(birth: str | None, today: datetime.date) -> int | None:
    try:
        b = datetime.date.fromisoformat(birth or "")
    except ValueError:
        return None
    return today.year - b.year - ((today.month, today.day) < (b.month, b.day))


def src(url: str | None, label: str = "source") -> str:
    return f'<a href="{html.escape(url)}" rel="nofollow noopener">{label}</a>' if url else ""


def countries_page() -> str:
    today = datetime.date.today()
    rows = []
    for c in load_countries():
        ra = c.get("retirement_age") or {}
        statutory = ra.get("statutory")
        norm = min(statutory, 67) if isinstance(statutory, int) else 67
        groups = ra.get("by_group") or {}
        ra_text = (", ".join(f"{k} {v}" for k, v in groups.items()) if groups
                   else (str(statutory) if statutory is not None else "unknown"))
        for o in c.get("offices", []):
            age = age_on(o.get("birth_date"), today)
            if age is None:
                status = '<span class="tag">unknown</span>'
            elif age >= norm:
                status = '<span class="tag on">at or above</span>'
            else:
                status = '<span class="tag">below</span>'
            rows.append(
                "<tr>"
                f"<td><strong>{html.escape(c.get('country', ''))}</strong></td>"
                f"<td>{html.escape(o.get('title') or o.get('office', ''))}</td>"
                f"<td>{html.escape(o.get('holder') or 'unknown')} {src(o.get('source'))}</td>"
                f"<td>{age if age is not None else 'unknown'}</td>"
                f"<td>{html.escape(ra_text)} {src(ra.get('source'))}<br><small>norm for a new term: {norm}</small></td>"
                f"<td>{status}</td>"
                "</tr>"
            )
    table = (
        "<table><thead><tr><th>Country</th><th>Office</th><th>Holder</th><th>Age</th>"
        "<th>Statutory retirement age</th><th>Compared with the norm</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    ) if rows else "<p>The first country profiles are being researched.</p>"
    body = f"""
<article class="doc wide">
<h1>Countries</h1>
<p>For each country: who holds the highest offices, their age, and the country's statutory retirement age. The norm for a new term is that retirement age, at the latest 67. This page states facts; it does not judge anyone. Every value links to its source.</p>
{table}
<p><small>Ages calculated on {today.isoformat()}. Profiles are researched by an AI agent with web search, reviewed by a person before publication, and refreshed regularly. Spotted an error? <a href="{REPO_URL}/issues">Tell us</a>.</small></p>
</article>
"""
    return page("Countries: Pass the Baton", body, depth=1,
                description="Leaders of the highest offices compared with their country's retirement age.")


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()

    if (ROOT / "brand").is_dir():
        shutil.copytree(ROOT / "brand", OUT / "brand", ignore=shutil.ignore_patterns("*.md"))

    (OUT / "index.html").write_text(home(), encoding="utf-8")

    (OUT / "manifesto").mkdir()
    (OUT / "manifesto/index.html").write_text(doc_page(ROOT / "MANIFESTO.md", "en", 1), encoding="utf-8")

    for code in languages()[1:]:
        (OUT / code).mkdir()
        (OUT / code / "index.html").write_text(
            doc_page(ROOT / "translations" / code / "MANIFESTO.md", code, 1), encoding="utf-8"
        )

    (OUT / "countries").mkdir()
    (OUT / "countries/index.html").write_text(countries_page(), encoding="utf-8")

    (OUT / "CNAME").write_text(DOMAIN + "\n", encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    print("Built", sorted(str(p.relative_to(OUT)) for p in OUT.rglob("*.html")))


if __name__ == "__main__":
    main()
