"""Build the Pass the Baton website into _site/.

Static HTML only: no server, no tracking, no cookies. The content comes from
the repository itself, so whatever the agents add through merged pull requests
(brand artwork, translations, country profiles) appears on the next deploy.

Every language gets a full site: a home page, the manifesto and the countries
page. English lives at the root, other languages under /<code>/. Interface
texts come from translations/<code>/site.json, falling back to English for any
missing key.

  pip install markdown
  python site/build.py
"""

from __future__ import annotations

import datetime
import html
import json
import os
import re
import shutil
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
SITE = Path(__file__).resolve().parent
OUT = ROOT / "_site"
TEMPLATES = SITE / "templates"
REPO_URL = "https://github.com/sven-antonissen/pass-the-baton"
DOMAIN = "pass-the-baton.org"
ORIGIN = f"https://{DOMAIN}"

RTL = {"ar", "he", "fa", "ur"}
LANG_NAMES = {
    "en": "English", "nl": "Nederlands", "es": "Español", "fr": "Français",
    "de": "Deutsch", "pt": "Português", "ar": "العربية", "hi": "हिन्दी",
    "zh": "中文", "ru": "Русский", "sw": "Kiswahili", "id": "Bahasa Indonesia",
    "ja": "日本語", "tr": "Türkçe", "it": "Italiano", "pl": "Polski", "ko": "한국어",
}
LOCALES = {
    "en": "en_GB", "nl": "nl_BE", "es": "es_ES", "fr": "fr_FR", "de": "de_DE", "pt": "pt_BR",
    "ar": "ar_AR", "hi": "hi_IN", "zh": "zh_CN", "ru": "ru_RU", "sw": "sw_KE", "id": "id_ID",
    "ja": "ja_JP", "tr": "tr_TR", "it": "it_IT", "pl": "pl_PL", "ko": "ko_KR",
}
PAGES = {"home": "", "manifesto": "manifesto/", "countries": "countries/", "join": "join/"}
SCALE = 90  # bars run from 0 to 90 years


# ---------- Languages and strings ----------

def languages() -> list[str]:
    folder = ROOT / "translations"
    found = sorted(p.name for p in folder.iterdir() if (p / "MANIFESTO.md").exists()) if folder.is_dir() else []
    return ["en"] + [c for c in found if c != "en"]


def load_strings(lang: str) -> dict:
    def read(code: str) -> dict:
        f = ROOT / "translations" / code / "site.json"
        try:
            return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
        except json.JSONDecodeError:
            return {}
    strings = read("en")
    if lang != "en":
        strings.update({k: v for k, v in read(lang).items() if isinstance(v, str) and v.strip()})
    return strings


def has_own_strings(lang: str) -> bool:
    return lang == "en" or (ROOT / "translations" / lang / "site.json").exists()


def lang_root(lang: str) -> str:
    return "" if lang == "en" else f"{lang}/"


def page_path(lang: str, key: str) -> str:
    return lang_root(lang) + PAGES[key]


def page_url(lang: str, key: str) -> str:
    return f"{ORIGIN}/{page_path(lang, key)}"


# ---------- Rendering ----------

def fill(text: str, strings: dict, **values: str) -> str:
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return re.sub(r"\{\{t:([a-z0-9_]+)\}\}", lambda m: html.escape(strings.get(m.group(1), "")), text)


def render(template: str, strings: dict, **values: str) -> str:
    return fill((TEMPLATES / template).read_text(encoding="utf-8"), strings, **values)


def fmt(s: str, **values) -> str:
    for k, v in values.items():
        s = s.replace("{" + k + "}", str(v))
    return s


def language_detection(lang: str, key: str) -> str:
    """A tiny script: remember the visitor's language choice, and on the English
    pages send first-time visitors to their browser's language if we have it.
    Search engines and visitors without JavaScript simply get the page they asked for."""
    supported = [c for c in languages() if c != "en"]
    targets = {c: "/" + page_path(c, key) for c in supported}
    redirect = ""
    if lang == "en":
        redirect = (
            "var t=" + json.dumps(targets) + ";"
            "if(!s){var ls=navigator.languages||[navigator.language||''];"
            "for(var i=0;i<ls.length;i++){var c=(ls[i]||'').toLowerCase().split('-')[0];"
            "if(c==='en')break;if(t[c]){location.replace(t[c]+location.hash);return;}}}"
        )
    return (
        "<script>(function(){var s=null;try{s=localStorage.getItem('ptb-lang')}catch(e){}"
        + redirect
        + "document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[hreflang]');"
        "if(a){try{localStorage.setItem('ptb-lang',a.getAttribute('hreflang'))}catch(e){}}});"
        "})();</script>"
    )


def page(lang: str, key: str, title: str, description: str, body: str, jsonld: str = "") -> str:
    strings = load_strings(lang)
    depth = page_path(lang, key).count("/")
    up = "../" * depth
    base = up + lang_root(lang)
    langs = languages()
    alternates = "\n".join(
        f'<link rel="alternate" hreflang="{code}" href="{page_url(code, key)}">' for code in langs
    ) + f'\n<link rel="alternate" hreflang="x-default" href="{page_url("en", key)}">'
    switcher = "".join(
        f'<li><a href="{up}{page_path(code, key)}" lang="{code}" hreflang="{code}"'
        + (' aria-current="page"' if code == lang else "")
        + f">{LANG_NAMES.get(code, code)}</a></li>"
        for code in langs
    )
    return render(
        "base.html", strings,
        lang=lang,
        dir="rtl" if lang in RTL else "ltr",
        title=html.escape(title),
        description=html.escape(description),
        canonical=page_url(lang, key),
        alternates=alternates,
        locale=LOCALES.get(lang, lang),
        og_image=f"{ORIGIN}/og.png",
        jsonld=jsonld,
        langdetect=language_detection(lang, key),
        up=up,
        base=base,
        repo=REPO_URL,
        lang_name=LANG_NAMES.get(lang, lang),
        switcher=switcher,
        body=fill(body, strings, up=up, base=base, repo=REPO_URL),
    )


def md_to_html(text: str) -> str:
    return markdown.markdown(text, extensions=["tables", "sane_lists"])


def first_heading(text: str, fallback: str) -> str:
    m = re.search(r"^#\s+(.+)$", text, re.M)
    return m.group(1).strip() if m else fallback


# ---------- Country data ----------

def load_countries() -> list[dict]:
    out = []
    folder = ROOT / "data/countries"
    for f in sorted(folder.glob("*.json")) if folder.is_dir() else []:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        d.setdefault("iso2", f.stem.upper())
        out.append(d)
    return sorted(out, key=lambda c: c.get("country", ""))


def age_on(birth: str | None, today: datetime.date) -> int | None:
    try:
        b = datetime.date.fromisoformat(birth or "")
    except ValueError:
        return None
    return today.year - b.year - ((today.month, today.day) < (b.month, b.day))


def country_norm(c: dict) -> float:
    statutory = (c.get("retirement_age") or {}).get("statutory")
    return min(statutory, 67) if isinstance(statutory, (int, float)) else 67


def num(v: float) -> str:
    return f"{v:g}"


def src(url: str | None, label: str) -> str:
    return f'<a href="{html.escape(url)}" rel="nofollow noopener">{html.escape(label)}</a>' if url else ""


def leader_stats(today: datetime.date) -> dict:
    countries = load_countries()
    ages, medians, at_or_above = [], [], 0
    for c in countries:
        norm = country_norm(c)
        m = (c.get("median_age") or {}).get("value")
        if isinstance(m, (int, float)):
            medians.append(m)
        for o in c.get("offices", []):
            a = age_on(o.get("birth_date"), today)
            if a is None:
                continue
            ages.append(a)
            at_or_above += a >= norm
    return {
        "countries": countries,
        "n_countries": len(countries),
        "n_offices": len(ages),
        "avg_leader_age": sum(ages) / len(ages) if ages else None,
        "avg_median_age": sum(medians) / len(medians) if medians else None,
        "n_medians": len(medians),
        "at_or_above": at_or_above,
    }


# ---------- Pages ----------

def home(lang: str) -> str:
    s = load_strings(lang)
    today = datetime.date.today()
    st = leader_stats(today)
    langs = "".join(
        f'<a href="{{{{up}}}}{page_path(code, "home")}" lang="{code}" hreflang="{code}">{LANG_NAMES.get(code, code)}</a>'
        for code in languages()
    )
    facts = (
        '<div class="facts"><div class="wrap"><ul>'
        f"<li><strong>{len(languages())}</strong>{html.escape(s['fact_languages'])}</li>"
        f"<li><strong>{st['n_countries']}</strong>{html.escape(s['fact_countries'])}</li>"
        f"<li><strong>{st['at_or_above']}</strong>{html.escape(fmt(s['fact_offices'], total=st['n_offices']))}</li>"
        "</ul></div></div>"
    ) if st["n_countries"] else ""

    gap = ""
    if st["avg_leader_age"] is not None:
        rows = [(s["gap_leaders"], fmt(s["gap_leaders_sub"], n=st["n_offices"]), st["avg_leader_age"], "")]
        if st["avg_median_age"] is not None:
            rows.append((s["gap_people"], fmt(s["gap_people_sub"], n=st["n_medians"]), st["avg_median_age"], " people"))
        bars = "".join(
            f'<div class="gap-row"><div class="label">{html.escape(label)}<small>{html.escape(sub)}</small></div>'
            f'<div class="bar{cls}"><i style="width:{min(v / SCALE * 100, 100):.1f}%"></i><b>{v:.0f}</b></div></div>'
            for label, sub, v, cls in rows
        )
        gap = (
            '<section class="section ink"><div class="wrap">'
            f"<h2>{html.escape(s['gap_title'])}</h2>"
            f'<div class="gap">{bars}</div>'
            f'<p class="gap-note"><a href="{{{{base}}}}countries/">{html.escape(fmt(s["gap_note"], date=today.isoformat()))}</a></p>'
            "</div></section>"
        )

    names = "".join(
        f'<li><a href="{{{{base}}}}countries/#{c["iso2"].lower()}">{html.escape(c.get("country", ""))}</a></li>'
        for c in st["countries"]
    )
    countries_cloud = (
        f"<h2>{html.escape(fmt(s['countries_title'], n=st['n_countries']))}</h2>"
        f"<p>{html.escape(s['countries_text'])}</p>"
        f'<ul class="country-cloud">{names}</ul>'
    ) if st["n_countries"] else f"<h2>{html.escape(s['cp_title'])}</h2><p>{html.escape(s['countries_empty'])}</p>"

    jsonld = (
        '<script type="application/ld+json">'
        + json.dumps({
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "Pass the Baton",
            "url": ORIGIN + "/",
            "logo": f"{ORIGIN}/brand/favicon.svg",
            "slogan": s["hero_title"],
            "description": s["meta_description"],
            "sameAs": [REPO_URL],
        }, ensure_ascii=False)
        + "</script>"
    )
    body = render("home.html", s, facts=facts, gap=gap, countries_cloud=countries_cloud, langs=langs)
    return page(lang, "home", s["site_title"], s["meta_description"], body, jsonld)


def manifesto(lang: str) -> str:
    s = load_strings(lang)
    md_file = ROOT / "MANIFESTO.md" if lang == "en" else ROOT / "translations" / lang / "MANIFESTO.md"
    text = md_file.read_text(encoding="utf-8")
    title = first_heading(text, "Pass the Baton")
    body = f'<article class="doc" lang="{lang}">{md_to_html(text)}</article>'
    return page(lang, "manifesto", title, s["meta_description"], body)


def countries(lang: str) -> str:
    s = load_strings(lang)
    today = datetime.date.today()
    cards = []
    for c in load_countries():
        code = c["iso2"].lower()
        ra = c.get("retirement_age") or {}
        norm = country_norm(c)
        groups = ra.get("by_group") or {}
        ra_text = (", ".join(f"{k.replace('_', ' ')} {v}" for k, v in groups.items()) if groups
                   else (num(ra["statutory"]) if isinstance(ra.get("statutory"), (int, float)) else s["cp_unknown"]))
        norm_pos = f"{norm / SCALE * 100:.1f}%"
        rows = []
        for o in c.get("offices", []):
            age = age_on(o.get("birth_date"), today)
            on = age is not None and age >= norm
            width = f"{min(age / SCALE * 100, 100):.1f}%" if age is not None else "0%"
            rows.append(
                '<div class="office">'
                f'<div class="who"><b>{html.escape(o.get("holder") or s["cp_unknown"])}</b>'
                f'{html.escape(o.get("title") or o.get("office", ""))} {src(o.get("source"), s["cp_source"])}</div>'
                f'<div class="age{" on" if on else ""}">{age if age is not None else "?"}</div>'
                f'<div class="track" aria-hidden="true"><i style="width:{width}"></i><u style="left:{norm_pos}"></u></div>'
                "</div>"
            )
        med = c.get("median_age") or {}
        if isinstance(med.get("value"), (int, float)):
            year = f", {med['year']}" if med.get("year") else ""
            rows.append(
                '<div class="office">'
                f'<div class="who"><b>{html.escape(s["cp_people"])}</b>{html.escape(s["cp_median"])}{year} {src(med.get("source"), s["cp_source"])}</div>'
                f'<div class="age">{med["value"]:.0f}</div>'
                f'<div class="track people" aria-hidden="true"><i style="width:{min(med["value"] / SCALE * 100, 100):.1f}%"></i><u style="left:{norm_pos}"></u></div>'
                "</div>"
            )
        system = f' · {html.escape(c["political_system"])}' if c.get("political_system") else ""
        cards.append(
            f'<section class="country" id="{code}">'
            f'<header><h3><a href="#{code}" title="{html.escape(s["cp_link"])}">{html.escape(c.get("country", ""))}</a></h3>'
            f'<span class="norm">{html.escape(s["cp_norm"])} <b>{num(norm)}</b></span></header>'
            + "".join(rows)
            + f'<p class="meta">{html.escape(s["cp_retirement"])}: {html.escape(ra_text)} {src(ra.get("source"), s["cp_source"])}'
            + f'{system} · {html.escape(s["cp_checked"])} {html.escape(c.get("checked_on", ""))}</p>'
            "</section>"
        )
    listing = f'<div class="country-list">{"".join(cards)}</div>' if cards else f"<p>{html.escape(s['countries_empty'])}</p>"
    body = f"""
<article class="doc wide">
<h1>{html.escape(s['cp_title'])}</h1>
<p class="countries-intro">{html.escape(s['cp_intro'])}</p>
<p class="countries-intro">{html.escape(s['cp_monarchs'])}</p>
<div class="legend"><span>{html.escape(s['cp_legend_holder'])}</span><span class="p">{html.escape(s['cp_legend_people'])}</span><span class="n">{html.escape(s['cp_legend_norm'])}</span></div>
{listing}
<p><small>{html.escape(fmt(s['cp_footnote'], date=today.isoformat()))} {html.escape(s['cp_error'])} <a href="{REPO_URL}/issues">{html.escape(s['cp_tell'])}</a>.</small></p>
</article>
"""
    return page(lang, "countries", f"{s['cp_title']}: Pass the Baton", s["cp_meta_description"], body)


def load_community() -> dict:
    f = ROOT / "data/community.json"
    try:
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    except json.JSONDecodeError:
        return {}


_MEMBER_CACHE: dict = {}


def community_counts(c: dict) -> dict:
    """Best-effort member counts, fetched once per build. Missing counts are simply not shown."""
    if _MEMBER_CACHE or os.environ.get("PTB_OFFLINE"):
        return _MEMBER_CACHE
    import urllib.request

    def get(url: str) -> dict:
        req = urllib.request.Request(url, headers={"User-Agent": "pass-the-baton-site/1.0 (+https://pass-the-baton.org)"})
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read().decode("utf-8"))

    code = (c.get("discord_invite") or "").rstrip("/").rsplit("/", 1)[-1]
    if code:
        try:
            _MEMBER_CACHE["discord"] = get(f"https://discord.com/api/v10/invites/{code}?with_counts=true").get("approximate_member_count")
        except Exception:  # noqa: BLE001 - counts are optional
            pass
    if c.get("reddit"):
        try:
            _MEMBER_CACHE["reddit"] = get(c["reddit"].rstrip("/") + "/about.json")["data"].get("subscribers")
        except Exception:  # noqa: BLE001
            pass
    _MEMBER_CACHE.setdefault("_done", True)
    return _MEMBER_CACHE


def join(lang: str) -> str:
    s = load_strings(lang)
    c = load_community()
    counts = community_counts(c)

    def members(key: str) -> str:
        n = counts.get(key)
        return f'<span class="members">{html.escape(fmt(s["jp_members"], n=n))}</span>' if isinstance(n, int) and n > 0 else ""

    cards = []
    if c.get("discord_invite"):
        cards.append(
            '<div class="channel discord">'
            f'<h2>{html.escape(s["jp_discord_title"])}</h2>{members("discord")}'
            f'<p>{html.escape(s["jp_discord_text"])}</p>'
            f'<a class="btn primary" href="{html.escape(c["discord_invite"])}" rel="noopener">{html.escape(s["jp_discord_cta"])}</a></div>'
        )
    if c.get("reddit"):
        cards.append(
            '<div class="channel reddit">'
            f'<h2>{html.escape(s["jp_reddit_title"])}</h2>{members("reddit")}'
            f'<p>{html.escape(s["jp_reddit_text"])}</p>'
            f'<a class="btn ghost" href="{html.escape(c["reddit"])}" rel="noopener">{html.escape(s["jp_reddit_cta"])}</a></div>'
        )
    ways = "".join(
        f'<li><h3>{html.escape(s[f"jp_way{i}_title"])}</h3><p>{html.escape(s[f"jp_way{i}_text"])}</p></li>'
        for i in (1, 2, 3)
    )
    body = f"""
<section class="join-hero">
  <div class="wrap">
    <h1>{html.escape(s['jp_title'])}</h1>
    <p class="lead">{html.escape(s['jp_intro'])}</p>
    <div class="channels">{''.join(cards)}</div>
  </div>
</section>
<section class="section">
  <div class="wrap">
    <h2>{html.escape(s['jp_ways_title'])}</h2>
    <ol class="ways">{ways}</ol>
  </div>
</section>
<section class="section paper-2">
  <div class="wrap safety">
    <h2>{html.escape(s['jp_safety_title'])}</h2>
    <p>{html.escape(s['jp_safety_text'])}</p>
    <p><small>{html.escape(s['jp_privacy'])}</small></p>
  </div>
</section>
"""
    return page(lang, "join", f"{s['jp_title']}: Pass the Baton", s["jp_meta_description"], body)


def sitemap() -> str:
    today = datetime.date.today().isoformat()
    urls = []
    for code in languages():
        for key in PAGES:
            alts = "".join(
                f'<xhtml:link rel="alternate" hreflang="{c}" href="{page_url(c, key)}"/>' for c in languages()
            )
            urls.append(f"<url><loc>{page_url(code, key)}</loc><lastmod>{today}</lastmod>{alts}</url>")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + "\n".join(urls) + "\n</urlset>\n"
    )


def write(rel: str, content: str) -> None:
    target = OUT / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()

    for folder in ("brand", "design"):
        if (ROOT / folder).is_dir():
            shutil.copytree(ROOT / folder, OUT / folder, ignore=shutil.ignore_patterns("*.md"))
    shutil.copy(SITE / "style.css", OUT / "style.css")
    if (SITE / "og-card.svg").exists():
        shutil.copy(SITE / "og-card.svg", OUT / "og-card.svg")

    for code in languages():
        write(page_path(code, "home") + "index.html", home(code))
        write(page_path(code, "manifesto") + "index.html", manifesto(code))
        write(page_path(code, "countries") + "index.html", countries(code))
        write(page_path(code, "join") + "index.html", join(code))

    write("sitemap.xml", sitemap())
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {ORIGIN}/sitemap.xml\n")
    write("CNAME", DOMAIN + "\n")
    write(".nojekyll", "")
    missing = [c for c in languages() if not has_own_strings(c)]
    print(f"Built {len(languages())} languages x {len(PAGES)} pages."
          + (f" Interface still in English for: {', '.join(missing)}." if missing else ""))


if __name__ == "__main__":
    main()
