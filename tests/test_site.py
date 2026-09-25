import json
from html.parser import HTMLParser
import importlib.util
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("site_build", ROOT / "scripts" / "build.py")
site_build = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(site_build)
REQUIRED_PERSONA_FIELDS = {
    "slug",
    "name",
    "seo_title",
    "meta_description",
    "intro",
    "responsibilities",
    "frictions",
    "assist",
    "automate_with_controls",
    "do_not_automate",
    "data_and_risks",
    "pilot",
    "existing_tools_first",
    "diagnostic_questions",
    "related_personas",
    "sources",
}


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.title = ""
        self.description = ""
        self.canonical = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        if tag == "title":
            self._in_title = True
        if tag == "meta" and attrs.get("name") == "description":
            self.description = attrs.get("content", "") or ""
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonical = attrs.get("href", "") or ""

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


class SiteContentTests(unittest.TestCase):
    def test_validation_rejects_path_traversal_slug(self):
        personas = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted((ROOT / "content" / "personas").glob("*.json"))
        ]
        personas[0]["slug"] = "../../../escaped-output"
        with self.assertRaisesRegex(ValueError, "slug"):
            site_build.validate_personas(personas)

    def test_validation_rejects_unsafe_site_urls(self):
        site = json.loads((ROOT / "content" / "site.json").read_text(encoding="utf-8"))
        for field, value in (
            ("base_url", 'https://example.test/\" onload=\"alert(1)'),
            ("base_url", "https://user:secret@example.test/base"),
            ("cta_href", "javascript:alert(1)"),
            ("cta_href", "/diagnostic-ia-cabinets-avocats/../outside/"),
            ("cta_href", "/diagnostic-ia-cabinets-avocats/%2e%2e/outside/"),
            ("cta_href", "/diagnostic-ia-cabinets-avocats/%252e%252e/outside/"),
            ("cta_href", "/diagnostic-ia-cabinets-avocats/%5c../outside/"),
            ("cta_href", "/diagnostic-ia-cabinets-avocats/%00/outside/"),
        ):
            hostile = dict(site)
            hostile[field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, field):
                site_build.validate_site(hostile)

    def test_https_url_validation_handles_root_urls_and_dns_labels(self):
        parsed = site_build.validate_https_url("https://example.test", "url")
        self.assertEqual(parsed.hostname, "example.test")
        for url in (
            "https://good.-bad.example/path",
            "https://good.bad-.example/path",
            "https://bad-.example/path",
            "https://example.test/%zz",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                site_build.validate_https_url(url, "url")

    def test_validation_rejects_malformed_source_and_duplicate_content(self):
        personas = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted((ROOT / "content" / "personas").glob("*.json"))
        ]
        malformed = json.loads(json.dumps(personas, ensure_ascii=False))
        malformed[0]["sources"][0]["url"] = "https:"
        with self.assertRaisesRegex(ValueError, "url"):
            site_build.validate_personas(malformed)
        for field in ("seo_title", "meta_description", "intro"):
            duplicate = json.loads(json.dumps(personas, ensure_ascii=False))
            duplicate[1][field] = duplicate[0][field]
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "dupli"):
                site_build.validate_personas(duplicate)

    def test_atomic_directory_swap_exchanges_complete_trees(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            current, candidate = root / "docs", root / "candidate"
            current.mkdir()
            candidate.mkdir()
            (current / "old.txt").write_text("ancien", encoding="utf-8")
            (candidate / "new.txt").write_text("nouveau", encoding="utf-8")
            site_build.atomic_swap_directories(current, candidate)
            self.assertEqual((current / "new.txt").read_text(encoding="utf-8"), "nouveau")
            self.assertEqual((candidate / "old.txt").read_text(encoding="utf-8"), "ancien")

    def test_404_uses_public_root_paths(self):
        site = json.loads((ROOT / "content" / "site.json").read_text(encoding="utf-8"))
        html = site_build.render_404(site)
        self.assertIn('href="/diagnostic-ia-cabinets-avocats/assets/styles.css"', html)
        self.assertIn('href="/diagnostic-ia-cabinets-avocats/"', html)
        self.assertIn('href="/diagnostic-ia-cabinets-avocats/metiers/"', html)

    def test_failed_build_preserves_previous_public_output(self):
        original_output, original_assets = site_build.OUTPUT, site_build.ASSETS
        try:
            with tempfile.TemporaryDirectory() as temporary:
                site_build.OUTPUT = Path(temporary) / "docs"
                site_build.ASSETS = site_build.OUTPUT / "assets"
                site_build.OUTPUT.mkdir()
                sentinel = site_build.OUTPUT / "sentinel.txt"
                sentinel.write_text("publication précédente", encoding="utf-8")
                with patch.object(site_build, "render_hub", side_effect=RuntimeError("échec simulé")):
                    with self.assertRaisesRegex(RuntimeError, "échec simulé"):
                        site_build.build()
                self.assertEqual(sentinel.read_text(encoding="utf-8"), "publication précédente")
        finally:
            site_build.OUTPUT, site_build.ASSETS = original_output, original_assets

    def test_site_config_defines_public_base_url(self):
        config_path = ROOT / "content" / "site.json"
        self.assertTrue(config_path.exists(), "content/site.json doit exister")
        config = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(
            config["base_url"],
            "https://buzznroses.github.io/diagnostic-ia-cabinets-avocats",
        )

    def test_build_creates_home_page(self):
        build_script = ROOT / "scripts" / "build.py"
        self.assertTrue(build_script.exists(), "scripts/build.py doit exister")
        subprocess.run(["python3", str(build_script)], cwd=ROOT, check=True)
        home = ROOT / "docs" / "index.html"
        self.assertTrue(home.exists(), "Le build doit créer docs/index.html")
        html = home.read_text(encoding="utf-8")
        self.assertIn("Diagnostic IA pour cabinets d’avocats", html)
        self.assertIn('type="application/ld+json"', html)

    def test_build_extracts_shared_assets(self):
        build_script = ROOT / "scripts" / "build.py"
        subprocess.run(["python3", str(build_script)], cwd=ROOT, check=True)
        home = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        self.assertTrue((ROOT / "docs" / "assets" / "styles.css").exists())
        self.assertTrue((ROOT / "docs" / "assets" / "site.js").exists())
        self.assertIn('href="assets/styles.css"', home)
        self.assertIn('src="assets/site.js"', home)
        self.assertNotIn("<style>", home)

    def test_exactly_fifteen_complete_personas(self):
        persona_dir = ROOT / "content" / "personas"
        files = sorted(persona_dir.glob("*.json")) if persona_dir.exists() else []
        self.assertEqual(len(files), 15, "Le site doit contenir exactement 15 personas")
        for path in files:
            persona = json.loads(path.read_text(encoding="utf-8"))
            missing = REQUIRED_PERSONA_FIELDS - persona.keys()
            self.assertFalse(missing, f"{path.name}: champs absents {sorted(missing)}")
            self.assertTrue(persona["sources"], f"{path.name}: au moins une source requise")

    def test_persona_identifiers_and_seo_are_unique(self):
        personas = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted((ROOT / "content" / "personas").glob("*.json"))
        ]
        for field in ("slug", "seo_title", "meta_description"):
            values = [persona[field] for persona in personas]
            self.assertEqual(len(values), len(set(values)), f"Valeurs dupliquées pour {field}")
        slugs = {persona["slug"] for persona in personas}
        for persona in personas:
            self.assertEqual(persona["slug"], Path(f"{persona['slug']}.json").stem)
            self.assertTrue(2 <= len(persona["related_personas"]) <= 4)
            self.assertTrue(set(persona["related_personas"]) <= slugs)
            self.assertNotIn(persona["slug"], persona["related_personas"])

    def test_build_creates_hub_and_fifteen_persona_pages(self):
        subprocess.run(["python3", str(ROOT / "scripts" / "build.py")], cwd=ROOT, check=True)
        hub = ROOT / "docs" / "metiers" / "index.html"
        self.assertTrue(hub.exists())
        hub_html = hub.read_text(encoding="utf-8")
        self.assertIn("BreadcrumbList", hub_html)
        self.assertEqual(hub_html.count("Demander un échange exploratoire"), 1)
        persona_paths = sorted((ROOT / "docs" / "metiers").glob("*/index.html"))
        self.assertEqual(len(persona_paths), 15)
        for path in persona_paths:
            slug = path.parent.name
            self.assertIn(f'href="{slug}/"', hub_html)
            html = path.read_text(encoding="utf-8")
            self.assertIn("BreadcrumbList", html)
            self.assertIn("Demander un échange exploratoire", html)
            self.assertEqual(html.count("Demander un échange exploratoire"), 1)
            self.assertEqual(html.count("<h1"), 1)
            self.assertIn("Comprendre le rôle", html)
            self.assertIn("Encadrer l’usage de l’IA et des données", html)

    def test_role_boundaries_and_conditional_facturation_wording_are_published(self):
        subprocess.run(["python3", str(ROOT / "scripts" / "build.py")], cwd=ROOT, check=True)
        for slug in (
            "associe-dirigeant", "dpo-conformite", "referent-informatique-dsi",
            "office-manager-assistant-direction", "responsable-administratif-financier",
            "ressources-humaines-recrutement",
        ):
            html = (ROOT / "docs" / "metiers" / slug / "index.html").read_text(encoding="utf-8")
            self.assertIn("Où s’arrête ce rôle", html, slug)
        facturation = (ROOT / "docs" / "metiers" / "facturation-recouvrement" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("La facturation dépend des temps saisis", facturation)

    def test_build_creates_sitemap_and_robots(self):
        subprocess.run(["python3", str(ROOT / "scripts" / "build.py")], cwd=ROOT, check=True)
        sitemap = (ROOT / "docs" / "sitemap.xml").read_text(encoding="utf-8")
        robots = (ROOT / "docs" / "robots.txt").read_text(encoding="utf-8")
        self.assertEqual(sitemap.count("<loc>"), 17)
        ET.fromstring(sitemap)
        self.assertIn("/metiers/avocat-individuel/", sitemap)
        self.assertIn("Sitemap: https://buzznroses.github.io/diagnostic-ia-cabinets-avocats/sitemap.xml", robots)

    def test_generated_pages_have_unique_metadata_and_valid_internal_links(self):
        subprocess.run(["python3", str(ROOT / "scripts" / "build.py")], cwd=ROOT, check=True)
        pages = [
            ROOT / "docs" / "index.html",
            ROOT / "docs" / "metiers" / "index.html",
            *sorted((ROOT / "docs" / "metiers").glob("*/index.html")),
        ]
        titles, descriptions, canonicals = [], [], []
        for page in pages:
            parser = PageParser()
            parser.feed(page.read_text(encoding="utf-8"))
            self.assertTrue(parser.title.strip(), page)
            self.assertTrue(parser.description.strip(), page)
            self.assertTrue(parser.canonical.startswith("https://"), page)
            titles.append(parser.title.strip())
            descriptions.append(parser.description.strip())
            canonicals.append(parser.canonical)
            for href in parser.links:
                parsed = urlparse(href)
                if parsed.scheme or href.startswith("#"):
                    continue
                if href.startswith("/diagnostic-ia-cabinets-avocats/"):
                    relative = href.removeprefix("/diagnostic-ia-cabinets-avocats/").split("#", 1)[0]
                    target = ROOT / "docs" / relative
                else:
                    target = (page.parent / href.split("#", 1)[0]).resolve()
                if not href.split("#", 1)[0]:
                    continue
                if target.is_dir():
                    target = target / "index.html"
                self.assertTrue(target.exists(), f"Lien cassé dans {page}: {href}")
        self.assertEqual(len(titles), len(set(titles)))
        self.assertEqual(len(descriptions), len(set(descriptions)))
        self.assertEqual(len(canonicals), len(set(canonicals)))
        script = (ROOT / "docs" / "assets" / "site.js").read_text(encoding="utf-8")
        for forbidden in ("fetch(", "XMLHttpRequest", "sendBeacon"):
            self.assertNotIn(forbidden, script)

    def test_build_check_detects_stale_output(self):
        build_script = ROOT / "scripts" / "build.py"
        subprocess.run(["python3", str(build_script)], cwd=ROOT, check=True)
        home = ROOT / "docs" / "index.html"
        original = home.read_text(encoding="utf-8")
        home.write_text(original + "\n<!-- stale -->\n", encoding="utf-8")
        stale = subprocess.run(["python3", str(build_script), "--check"], cwd=ROOT)
        self.assertNotEqual(stale.returncode, 0)
        subprocess.run(["python3", str(build_script)], cwd=ROOT, check=True)
        fresh = subprocess.run(["python3", str(build_script), "--check"], cwd=ROOT)
        self.assertEqual(fresh.returncode, 0)


if __name__ == "__main__":
    unittest.main()
