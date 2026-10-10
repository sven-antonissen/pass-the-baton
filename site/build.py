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
    body = render("home.html", art=art, baton=baton, langs=langs, repo=REPO_URL)
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
<p>Kings and queens are included too. They have no terms, but the same principle applies: what holds for the people holds for those who lead them.</p>
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
