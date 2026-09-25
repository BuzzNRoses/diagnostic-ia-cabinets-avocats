#!/usr/bin/env python3
"""Construit le site statique dans le dossier docs/."""

from __future__ import annotations

from html import escape
import ctypes
import json
import os
from pathlib import Path
import posixpath
import re
import shutil
from string import Template
import sys
import tempfile
from typing import Any
from urllib.parse import unquote_to_bytes, urlparse
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs"
ASSETS = OUTPUT / "assets"
PERSONA_DIR = ROOT / "content" / "personas"
TEMPLATE_DIR = ROOT / "templates"

STYLE_RE = re.compile(r"\s*<style>(.*?)</style>", re.DOTALL)
SCRIPT_RE = re.compile(r"\s*<script>(.*?)</script>", re.DOTALL)

LEGAL_SLUGS = {"avocat-individuel", "associe-dirigeant", "avocat-collaborateur", "avocat-contentieux", "avocat-conseil-transactionnel"}
SUPPORT_SLUGS = {"eleve-avocat-stagiaire", "secretaire-assistant-juridique", "office-manager-assistant-direction", "documentaliste-knowledge-manager", "dpo-conformite"}
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REQUIRED_PERSONA_FIELDS = {
    "slug", "name", "seo_title", "meta_description", "intro", "responsibilities", "frictions", "assist",
    "automate_with_controls", "do_not_automate", "data_and_risks", "pilot", "existing_tools_first",
    "diagnostic_questions", "related_personas", "sources",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_template(name: str) -> Template:
    return Template((TEMPLATE_DIR / name).read_text(encoding="utf-8"))


def require_text(value: Any, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} doit être un texte non vide")


def require_text_list(value: Any, label: str) -> None:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} doit être une liste non vide")
    for index, item in enumerate(value):
        require_text(item, f"{label}[{index}]")


def decode_url_path(value: str, label: str) -> str:
    current = value or "/"
    for _ in range(5):
        if re.search(r"%(?![0-9A-Fa-f]{2})", current):
            raise ValueError(f"{label} contient un encodage invalide")
        try:
            decoded = unquote_to_bytes(current).decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise ValueError(f"{label} contient un encodage invalide") from error
        if decoded == current:
            break
        current = decoded
    else:
        raise ValueError(f"{label} contient trop de niveaux d’encodage")
    if "%" in current or "\\" in current or any(ord(character) < 32 or ord(character) == 127 for character in current):
        raise ValueError(f"{label} contient un chemin interdit")
    return current


def validate_https_url(value: str, label: str, *, allow_query: bool = False, allow_fragment: bool = False) -> Any:
    if any(character in value for character in ('"', "'", "<", ">", "\\", "\n", "\r")):
        raise ValueError(f"{label} contient des caractères interdits")
    parsed = urlparse(value)
    try:
        port = parsed.port
    except ValueError as error:
        raise ValueError(f"{label} contient un port invalide") from error
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError(f"{label} doit être une URL HTTPS sans identifiants")
    if port is not None and not 1 <= port <= 65535:
        raise ValueError(f"{label} contient un port invalide")
    if (parsed.query and not allow_query) or (parsed.fragment and not allow_fragment):
        raise ValueError(f"{label} ne doit pas contenir de requête ou fragment")
    hostname = parsed.hostname
    labels = hostname.split(".")
    if len(hostname) > 253 or any(not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", label) for label in labels):
        raise ValueError(f"{label} contient un nom d’hôte invalide")
    decoded_path = decode_url_path(parsed.path, label)
    if any(segment in {".", ".."} for segment in decoded_path.split("/")) or posixpath.normpath(decoded_path) != (decoded_path.rstrip("/") or "/"):
        raise ValueError(f"{label} contient un chemin ambigu")
    return parsed


def validate_site(site: dict[str, Any]) -> None:
    for field in ("site_name", "base_url", "description", "cta_label", "cta_href"):
        require_text(site.get(field), field)
    parsed = validate_https_url(site["base_url"], "base_url")
    if site["base_url"].endswith("/"):
        raise ValueError("base_url doit être une URL HTTPS publique sans requête, fragment ni slash final")
    cta = site["cta_href"]
    base_path = parsed.path.rstrip("/") + "/"
    cta_parsed = urlparse(cta)
    decoded_cta_path = decode_url_path(cta_parsed.path, "cta_href")
    if (
        cta_parsed.scheme or cta_parsed.netloc or cta_parsed.query
        or any(character in cta for character in ('"', "'", "<", ">", "\\", "\n", "\r"))
        or any(segment in {".", ".."} for segment in decoded_cta_path.split("/"))
        or posixpath.normpath(decoded_cta_path) != decoded_cta_path.rstrip("/")
        or not decoded_cta_path.startswith(base_path)
    ):
        raise ValueError("cta_href doit être un chemin interne sûr sous base_url")


def validate_personas(personas: list[dict[str, Any]]) -> None:
    if len(personas) != 15:
        raise ValueError(f"15 personas requises, {len(personas)} trouvées")
    slugs: list[str] = []
    pilots: set[str] = set()
    unique_values = {field: set() for field in ("seo_title", "meta_description", "intro", "responsibilities", "frictions", "assist", "automate_with_controls", "do_not_automate", "data_and_risks")}
    for index, persona in enumerate(personas):
        label = f"persona[{index}]"
        if not isinstance(persona, dict):
            raise ValueError(f"{label} doit être un objet")
        missing = REQUIRED_PERSONA_FIELDS - persona.keys()
        if missing:
            raise ValueError(f"{label}: champs absents {sorted(missing)}")
        slug = persona["slug"]
        if not isinstance(slug, str) or not SLUG_RE.fullmatch(slug):
            raise ValueError(f"{label}.slug est invalide")
        slugs.append(slug)
        for field in ("name", "seo_title", "meta_description", "intro"):
            require_text(persona[field], f"{slug}.{field}")
        for field in ("responsibilities", "frictions", "do_not_automate", "existing_tools_first", "diagnostic_questions", "related_personas"):
            require_text_list(persona[field], f"{slug}.{field}")
        for field, keys in (("assist", {"title", "body"}), ("automate_with_controls", {"title", "body", "control"}), ("data_and_risks", {"title", "body"}), ("sources", {"title", "url", "kind"})):
            items = persona[field]
            if not isinstance(items, list) or not items:
                raise ValueError(f"{slug}.{field} doit être une liste non vide")
            for item_index, item in enumerate(items):
                if not isinstance(item, dict) or not keys <= item.keys():
                    raise ValueError(f"{slug}.{field}[{item_index}] est incomplet")
                for key in keys:
                    require_text(item[key], f"{slug}.{field}[{item_index}].{key}")
                if field == "sources":
                    validate_https_url(item["url"], f"{slug}.sources[{item_index}].url", allow_query=True, allow_fragment=True)
                if field == "sources" and item["kind"] not in {"role", "framework"}:
                    raise ValueError(f"{slug}.sources[{item_index}].kind est invalide")
        pilot = persona["pilot"]
        pilot_keys = {"title", "situation", "scope", "measure", "stop"}
        if not isinstance(pilot, dict) or not pilot_keys <= pilot.keys():
            raise ValueError(f"{slug}.pilot est incomplet")
        for key in pilot_keys:
            require_text(pilot[key], f"{slug}.pilot.{key}")
        pilot_signature = json.dumps({key: pilot[key] for key in sorted(pilot_keys)}, ensure_ascii=False, sort_keys=True)
        if pilot_signature in pilots:
            raise ValueError(f"{slug}.pilot duplique un autre persona")
        pilots.add(pilot_signature)
        for field, seen in unique_values.items():
            signature = json.dumps(persona[field], ensure_ascii=False, sort_keys=True)
            if signature in seen:
                raise ValueError(f"{slug}.{field} duplique un autre persona")
            seen.add(signature)
    if len(slugs) != len(set(slugs)):
        raise ValueError("Les slugs des personas doivent être uniques")
    slug_set = set(slugs)
    for persona in personas:
        related = persona["related_personas"]
        if persona["slug"] in related or not set(related) <= slug_set:
            raise ValueError(f"{persona['slug']}.related_personas contient une référence invalide")


def html_list(items: list[str]) -> str:
    return "".join(f"<li>{escape(item)}</li>" for item in items)


def intro_html(text: str) -> str:
    return "".join(f"<p>{escape(part.strip())}</p>" for part in text.split("\n\n") if part.strip())


def usage_items(items: list[dict[str, str]], with_control: bool = False) -> str:
    rendered = []
    for item in items:
        control = ""
        if with_control:
            control = f'<p class="control"><strong>Contrôle :</strong> {escape(item["control"])}</p>'
        rendered.append('<div class="usage-item">' f'<h4>{escape(item["title"])}</h4>' f'<p>{escape(item["body"])}</p>{control}</div>')
    return "".join(rendered)


def risk_items(items: list[dict[str, str]]) -> str:
    return "".join('<article class="risk-item">' f'<h3>{escape(item["title"])}</h3><p>{escape(item["body"])}</p></article>' for item in items)


def source_items(items: list[dict[str, str]]) -> str:
    return "".join(f'<li><a href="{escape(item["url"], quote=True)}" rel="noopener noreferrer">{escape(item["title"])}</a></li>' for item in items)


def source_groups(items: list[dict[str, str]]) -> tuple[str, str]:
    role_items = [item for item in items if item["kind"] == "role"]
    framework_items = [item for item in items if item["kind"] == "framework"]
    if not role_items:
        raise ValueError("Chaque persona doit comporter au moins une source pour comprendre le rôle")
    if not framework_items:
        raise ValueError("Chaque persona doit comporter au moins une source sur l’IA, les données ou la sécurité")
    return source_items(role_items), source_items(framework_items)


def directory_item(persona: dict[str, Any]) -> str:
    summary = persona["intro"].split("\n\n", 1)[0]
    return f'<a class="directory-item" href="{escape(persona["slug"], quote=True)}/"><strong>{escape(persona["name"])}</strong><span>{escape(summary)}</span></a>'


def render_base(*, title: str, description: str, canonical: str, asset_prefix: str, body: str, jsonld: dict[str, Any]) -> str:
    return load_template("base.html").substitute(
        title=escape(title), description=escape(description, quote=True), canonical=escape(canonical, quote=True), asset_prefix=escape(asset_prefix, quote=True),
        jsonld=json.dumps(jsonld, ensure_ascii=False).replace("</", "<\\/"), body=body,
    )


def build_home(site: dict[str, Any], base_css: str, base_js: str) -> None:
    source_home = (ROOT / "index.html").read_text(encoding="utf-8")
    extended_css = (ROOT / "assets-src" / "extended.css").read_text(encoding="utf-8")
    (ASSETS / "styles.css").write_text(base_css.strip() + "\n" + extended_css.strip() + "\n", encoding="utf-8")
    (ASSETS / "site.js").write_text(base_js.strip() + "\n", encoding="utf-8")
    canonical = site["base_url"] + "/"
    jsonld = json.dumps({"@context": "https://schema.org", "@type": "WebPage", "name": site["site_name"], "url": canonical}, ensure_ascii=False).replace("</", "<\\/")
    public_home = STYLE_RE.sub('\n  <link rel="canonical" href="' + escape(canonical, quote=True) + '">\n  <link rel="stylesheet" href="assets/styles.css">', source_home, count=1)
    public_home = SCRIPT_RE.sub('\n  <script src="assets/site.js" defer></script>', public_home, count=1)
    public_home = public_home.replace("</head>", f'  <script type="application/ld+json">{jsonld}</script>\n</head>', 1)
    public_home = public_home.replace('<nav aria-label="Navigation principale">', '<nav aria-label="Navigation principale"><a href="metiers/">Métiers</a>', 1)
    (OUTPUT / "index.html").write_text(public_home, encoding="utf-8")


def render_hub(site: dict[str, Any], personas: list[dict[str, Any]]) -> str:
    legal = [p for p in personas if p["slug"] in LEGAL_SLUGS]
    support = [p for p in personas if p["slug"] in SUPPORT_SLUGS]
    management = [p for p in personas if p["slug"] not in LEGAL_SLUGS | SUPPORT_SLUGS]
    body = load_template("hub-metiers.html").substitute(
        home_href="../", hub_href="./", cta_href=escape(site["cta_href"], quote=True),
        legal_items="".join(directory_item(p) for p in legal), support_items="".join(directory_item(p) for p in support),
        management_items="".join(directory_item(p) for p in management),
    )
    canonical = site["base_url"] + "/metiers/"
    return render_base(
        title="IA et automatisation selon les métiers du cabinet d’avocats",
        description="Quinze rôles du cabinet d’avocats : tâches, usages prudents de l’IA, automatisations possibles et contrôles humains nécessaires.",
        canonical=canonical, asset_prefix="..", body=body,
        jsonld={"@context": "https://schema.org", "@graph": [
            {"@type": "CollectionPage", "name": "Métiers du cabinet d’avocats et usages de l’IA", "url": canonical},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Accueil", "item": site["base_url"] + "/"},
                {"@type": "ListItem", "position": 2, "name": "Métiers", "item": canonical},
            ]},
        ]},
    )


def render_persona(site: dict[str, Any], persona: dict[str, Any], by_slug: dict[str, dict[str, Any]]) -> str:
    related = "".join(f'<a href="../{escape(slug, quote=True)}/">{escape(by_slug[slug]["name"])}</a>' for slug in persona["related_personas"])
    role_sources, framework_sources = source_groups(persona["sources"])
    role_boundary = ""
    if persona.get("role_boundary"):
        role_boundary = f'<section class="role-boundary"><div class="wrap"><h2>Où s’arrête ce rôle&nbsp;?</h2><p>{escape(persona["role_boundary"])}</p></div></section>'
    body = load_template("persona.html").substitute(
        home_href="../../", hub_href="../", cta_href=escape(site["cta_href"], quote=True), name=escape(persona["name"]), heading=escape(persona["seo_title"].split(":", 1)[0]),
        intro=intro_html(persona["intro"]), responsibilities=html_list(persona["responsibilities"]), frictions=html_list(persona["frictions"]),
        assist=usage_items(persona["assist"]), automate=usage_items(persona["automate_with_controls"], with_control=True), do_not_automate=html_list(persona["do_not_automate"]),
        data_and_risks=risk_items(persona["data_and_risks"]), pilot_title=escape(persona["pilot"]["title"]), pilot_situation=escape(persona["pilot"]["situation"]),
        pilot_scope=escape(persona["pilot"]["scope"]), pilot_measure=escape(persona["pilot"]["measure"]), pilot_stop=escape(persona["pilot"]["stop"]),
        existing_tools=html_list(persona["existing_tools_first"]), diagnostic_questions=html_list(persona["diagnostic_questions"]), role_boundary=role_boundary,
        related_links=related, role_sources=role_sources, framework_sources=framework_sources,
    )
    canonical = f'{site["base_url"]}/metiers/{persona["slug"]}/'
    jsonld = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebPage", "name": persona["seo_title"], "url": canonical},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Accueil", "item": site["base_url"] + "/"},
            {"@type": "ListItem", "position": 2, "name": "Métiers", "item": site["base_url"] + "/metiers/"},
            {"@type": "ListItem", "position": 3, "name": persona["name"], "item": canonical},
        ]},
    ]}
    return render_base(title=persona["seo_title"], description=persona["meta_description"], canonical=canonical, asset_prefix="../..", body=body, jsonld=jsonld)


def render_404(site: dict[str, Any]) -> str:
    public_root = urlparse(site["base_url"]).path.rstrip("/")
    body = load_template("404.html").substitute(home_href=public_root + "/", hub_href=public_root + "/metiers/")
    return render_base(title="Page introuvable — Diagnostic IA pour cabinets d’avocats", description="La page demandée n’existe pas.", canonical=site["base_url"] + "/404.html", asset_prefix=public_root, body=body, jsonld={"@context": "https://schema.org", "@type": "WebPage", "name": "Page introuvable"})


def write_indexing_files(site: dict[str, Any], personas: list[dict[str, Any]]) -> None:
    urls = [site["base_url"] + "/", site["base_url"] + "/metiers/"]
    urls.extend(f'{site["base_url"]}/metiers/{persona["slug"]}/' for persona in personas)
    sitemap = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    sitemap.extend(f"  <url><loc>{xml_escape(url)}</loc></url>" for url in urls)
    sitemap.append("</urlset>")
    (OUTPUT / "sitemap.xml").write_text("\n".join(sitemap) + "\n", encoding="utf-8")
    (OUTPUT / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n"
        f'Sitemap: {site["base_url"]}/sitemap.xml\n',
        encoding="utf-8",
    )


def generate_output() -> None:
    site = load_json(ROOT / "content" / "site.json")
    personas = [load_json(path) for path in sorted(PERSONA_DIR.glob("*.json"))]
    validate_site(site)
    validate_personas(personas)
    by_slug = {persona["slug"]: persona for persona in personas}
    ASSETS.mkdir(parents=True)
    source_home = (ROOT / "index.html").read_text(encoding="utf-8")
    style_match = STYLE_RE.search(source_home)
    script_match = SCRIPT_RE.search(source_home)
    if not style_match or not script_match:
        raise ValueError("La page source doit contenir un bloc style et un script")
    build_home(site, style_match.group(1), script_match.group(1))
    hub_dir = OUTPUT / "metiers"
    hub_dir.mkdir()
    (hub_dir / "index.html").write_text(render_hub(site, personas), encoding="utf-8")
    for persona in personas:
        target = hub_dir / persona["slug"]
        target.mkdir()
        (target / "index.html").write_text(render_persona(site, persona, by_slug), encoding="utf-8")
    (OUTPUT / "404.html").write_text(render_404(site), encoding="utf-8")
    write_indexing_files(site, personas)
    (OUTPUT / ".nojekyll").write_text("", encoding="utf-8")


def build() -> None:
    global OUTPUT, ASSETS
    original_output, original_assets = OUTPUT, ASSETS
    with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
        candidate = Path(temporary) / "docs"
        try:
            OUTPUT = candidate
            ASSETS = candidate / "assets"
            generate_output()
        finally:
            OUTPUT, ASSETS = original_output, original_assets
        if original_output.exists():
            atomic_swap_directories(original_output, candidate)
            shutil.rmtree(candidate)
        else:
            candidate.replace(original_output)


def atomic_swap_directories(first: Path, second: Path) -> None:
    """Échange deux répertoires sans état intermédiaire où l’un serait absent."""
    libc = ctypes.CDLL(None, use_errno=True)
    first_bytes, second_bytes = os.fsencode(first), os.fsencode(second)
    if sys.platform == "darwin" and hasattr(libc, "renameatx_np"):
        result = libc.renameatx_np(-2, first_bytes, -2, second_bytes, 0x00000002)
    elif hasattr(libc, "renameat2"):
        result = libc.renameat2(-100, first_bytes, -100, second_bytes, 0x00000002)
    else:
        raise RuntimeError("Le système ne fournit pas d’échange atomique de répertoires")
    if result != 0:
        error_number = ctypes.get_errno()
        raise OSError(error_number, os.strerror(error_number), str(first), str(second))


def tree_snapshot(root: Path) -> dict[str, bytes]:
    if not root.exists():
        return {}
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def check_build() -> bool:
    global OUTPUT, ASSETS
    current = tree_snapshot(OUTPUT)
    original_output, original_assets = OUTPUT, ASSETS
    try:
        with tempfile.TemporaryDirectory() as temporary:
            OUTPUT = Path(temporary) / "docs"
            ASSETS = OUTPUT / "assets"
            build()
            expected = tree_snapshot(OUTPUT)
    finally:
        OUTPUT, ASSETS = original_output, original_assets
    return current == expected


if __name__ == "__main__":
    if "--check" in sys.argv:
        if not check_build():
            print("Le dossier docs/ n’est pas à jour. Exécutez scripts/build.py.", file=sys.stderr)
            raise SystemExit(1)
        print("Le dossier docs/ est à jour.")
    else:
        build()
