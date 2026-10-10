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


TEMPLATES = Path(__file__).resolve().parent / "templates"


def render(template: str, **values: str) -> str:
    """Fill {{name}} placeholders. Unknown placeholders are left as they are."""
    text = (TEMPLATES / template).read_text(encoding="utf-8")
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def page(title: str, body: str, lang: str = "en", depth: int = 0, description: str = "") -> str:
    up = "../" * depth
    return render(
        "base.html",
        lang=lang,
        dir="rtl" if lang in RTL else "ltr",
        title=html.escape(title),
        description=html.escape(description or "What applies to the people should apply to those who lead them."),
        up=up,
        repo=REPO_URL,
        body=body.replace("{{up}}", up),
    )


def md_to_html(text: str) -> str:
    return markdown.markdown(text, extensions=["tables", "sane_lists"])


def first_heading(text: str, fallback: str) -> str:
    m = re.search(r"^#\s+(.+)$", text, re.M)
    return m.group(1).strip() if m else fallback


def languages() -> list[str]:
    folder = ROOT / "translations"
    found = sorted(p.name for p in folder.iterdir() if (p / "MANIFESTO.md").exists()) if folder.is_dir() else []
    return ["en"] + found


def leader_stats(today: datetime.date) -> dict:
    """Aggregate facts for the home page, from the country profiles."""
    countries = load_countries()
    ages, medians, at_or_above, offices = [], [], 0, 0
    for c in countries:
        norm = country_norm(c)
        m = (c.get("median_age") or {}).get("value")
        if isinstance(m, (int, float)):
            medians.append(m)
        for o in c.get("offices", []):
            a = age_on(o.get("birth_date"), today)
            if a is None:
                continue
            offices += 1
            ages.append(a)
            at_or_above += a >= norm
    return {
        "countries": countries,
        "n_countries": len(countries),
        "n_offices": offices,
        "avg_leader_age": sum(ages) / len(ages) if ages else None,
        "avg_median_age": sum(medians) / len(medians) if medians else None,
        "n_medians": len(medians),
        "at_or_above": at_or_above,
    }


def home() -> str:
    today = datetime.date.today()
    st = leader_stats(today)
    langs_list = languages()
    langs = "".join(
        f'<a href="{"manifesto/" if code == "en" else code + "/"}" lang="{code}">{LANG_NAMES.get(code, code)}</a>'
        for code in langs_list
    )
    facts = (
        '<div class="facts"><div class="wrap"><ul>'
        f"<li><strong>{len(langs_list)}</strong>languages</li>"
        f"<li><strong>{st['n_countries']}</strong>countries profiled</li>"
        f"<li><strong>{st['at_or_above']}</strong>of {st['n_offices']} top office holders at or above the norm</li>"
        "</ul></div></div>"
    ) if st["n_countries"] else ""

    gap = ""
    if st["avg_leader_age"] is not None:
        scale = 90
        rows = [
            ("Heads of state and government", f"average age, {st['n_offices']} office holders", st["avg_leader_age"], ""),
        ]
        if st["avg_median_age"] is not None:
            rows.append(("The people they lead", f"average median age, {st['n_medians']} countries", st["avg_median_age"], " people"))
        bars = "".join(
            f'<div class="gap-row"><div class="label">{label}<small>{sub}</small></div>'
            f'<div class="bar{cls}"><i style="width:{min(v / scale * 100, 100):.1f}%"></i><b>{v:.0f}</b></div></div>'
            for label, sub, v, cls in rows
        )
        gap = (
            '<section class="section ink"><div class="wrap">'
            "<h2>Leaders and the people they lead</h2>"
            f'<div class="gap">{bars}</div>'
            f'<p class="gap-note">Calculated on {today.isoformat()} from the sourced profiles on the <a href="countries/">countries page</a>. '
            "Bars run from 0 to 90 years.</p>"
            "</div></section>"
        )

    names = "".join(f"<li>{html.escape(c.get('country', ''))}</li>" for c in st["countries"])
    countries_cloud = (
        f"<h2>{st['n_countries']} countries and counting</h2>"
        "<p>For every country we record who holds the highest offices, their age and the country's statutory retirement age, each with its source.</p>"
        f'<ul class="country-cloud">{names}</ul>'
    ) if st["n_countries"] else "<h2>Countries</h2><p>The first country profiles are being researched.</p>"

    body = render("home.html", facts=facts, gap=gap, countries_cloud=countries_cloud, langs=langs, repo=REPO_URL)
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


def country_norm(c: dict) -> int:
    statutory = (c.get("retirement_age") or {}).get("statutory")
    return min(statutory, 67) if isinstance(statutory, (int, float)) else 67


def countries_page() -> str:
    today = datetime.date.today()
    scale = 90
    cards = []
    for c in load_countries():
        ra = c.get("retirement_age") or {}
        norm = country_norm(c)
        groups = ra.get("by_group") or {}
        ra_text = (", ".join(f"{k.replace('_', ' ')} {v}" for k, v in groups.items()) if groups
                   else (str(ra.get("statutory")) if ra.get("statutory") is not None else "unknown"))
        norm_pos = f"{norm / scale * 100:.1f}%"
        rows = []
        for o in c.get("offices", []):
            age = age_on(o.get("birth_date"), today)
            on = age is not None and age >= norm
            width = f"{min(age / scale * 100, 100):.1f}%" if age is not None else "0%"
            rows.append(
                '<div class="office">'
                f'<div class="who"><b>{html.escape(o.get("holder") or "unknown")}</b>'
                f'{html.escape(o.get("title") or o.get("office", ""))} {src(o.get("source"))}</div>'
                f'<div class="age{" on" if on else ""}">{age if age is not None else "?"}</div>'
                f'<div class="track" role="img" aria-label="Age {age if age is not None else "unknown"}, norm {norm}">'
                f'<i style="width:{width}"></i><u style="left:{norm_pos}"></u></div>'
                "</div>"
            )
        med = c.get("median_age") or {}
        if isinstance(med.get("value"), (int, float)):
            rows.append(
                '<div class="office">'
                f'<div class="who"><b>The people</b>median age{f", {med.get("year")}" if med.get("year") else ""} {src(med.get("source"))}</div>'
                f'<div class="age">{med["value"]:.0f}</div>'
                f'<div class="track people"><i style="width:{min(med["value"] / scale * 100, 100):.1f}%"></i><u style="left:{norm_pos}"></u></div>'
                "</div>"
            )
        cards.append(
            '<section class="country">'
            f'<header><h3>{html.escape(c.get("country", ""))}</h3>'
            f'<span class="norm">norm for a new term <b>{norm}</b></span></header>'
            + "".join(rows)
            + f'<p class="meta">Statutory retirement age: {html.escape(ra_text)} {src(ra.get("source"))}'
            + (f' · {html.escape(c.get("political_system"))}' if c.get("political_system") else "")
            + f' · checked {html.escape(c.get("checked_on", ""))}</p>'
            "</section>"
        )
    listing = f'<div class="country-list">{"".join(cards)}</div>' if cards else "<p>The first country profiles are being researched.</p>"
    body = f"""
<article class="doc wide">
<h1>Countries</h1>
<p class="countries-intro">For each country: who holds the highest offices, their age, and the country's statutory retirement age. The norm for a new term is that retirement age, at the latest 67. This page states facts; it does not judge anyone. Every value links to its source.</p>
<p class="countries-intro">Kings and queens are included too. They have no terms, but the same principle applies: what holds for the people holds for those who lead them.</p>
<div class="legend"><span>age of the office holder</span><span class="p">median age of the population</span><span class="n">the norm for a new term</span></div>
{listing}
<p><small>Ages calculated on {today.isoformat()}. Bars run from 0 to 90 years. Profiles are researched by an AI agent with web search, reviewed by a person before publication, and refreshed regularly. Spotted an error? <a href="{REPO_URL}/issues">Tell us</a>.</small></p>
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

    shutil.copy(Path(__file__).resolve().parent / "style.css", OUT / "style.css")
    if (ROOT / "design").is_dir():
        shutil.copytree(ROOT / "design", OUT / "design", ignore=shutil.ignore_patterns("*.md"))

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
