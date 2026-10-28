"""Static checks for the catalogue. Standard library only: python3 -m unittest discover tests"""

import ast
import re
import subprocess
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
MAIN_JS = ROOT / "assets" / "main.js"
BUILD_SITE = ROOT / "resources" / "scripts" / "build-site.py"
ID_REFERENCES = ("aria-controls", "aria-labelledby", "aria-describedby", "for")


class SiteParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.id_refs = []
        self.links = []
        self.canonical = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        for name in ID_REFERENCES:
            if attrs.get(name):
                self.id_refs += [(name, ref) for ref in attrs[name].split()]
        for name in ("href", "src"):
            if attrs.get(name):
                self.links.append(attrs[name])
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonical = attrs.get("href")


def is_git_ignored(path):
    # Generated files and large assets are listed in .gitignore and built locally.
    result = subprocess.run(["git", "check-ignore", "-q", path], cwd=ROOT)
    return result.returncode == 0


class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.site = SiteParser()
        cls.site.feed(INDEX.read_text(encoding="utf-8"))
        cls.main_js = MAIN_JS.read_text(encoding="utf-8")

    def test_ids_are_unique(self):
        duplicates = sorted({i for i in self.site.ids if self.site.ids.count(i) > 1})
        self.assertEqual(duplicates, [])

    def test_id_references_exist(self):
        for name, ref in self.site.id_refs:
            with self.subTest(attribute=name, id=ref):
                self.assertIn(ref, self.site.ids)

    def test_ids_used_by_script_exist(self):
        used = set(re.findall(r"(?:byId|setText)\(\s*[\"']([^\"']+)[\"']", self.main_js))
        self.assertTrue(used)
        self.assertEqual(sorted(used - set(self.site.ids)), [])

    def test_local_files_exist_or_are_generated(self):
        references = list(self.site.links)
        for css in (ROOT / "assets").glob("*.css"):
            for url in re.findall(r"url\(\s*['\"]?([^'\")]+)", css.read_text(encoding="utf-8")):
                if not urlsplit(url).scheme:
                    references.append((css.parent / url).resolve().relative_to(ROOT).as_posix())
        for link in references:
            parts = urlsplit(link)
            if parts.scheme or link.startswith("#") or not parts.path:
                continue
            with self.subTest(link=link):
                self.assertTrue(
                    (ROOT / parts.path).is_file() or is_git_ignored(parts.path),
                    f"{link} is neither versioned nor in .gitignore",
                )

    def test_external_links_use_https(self):
        for link in self.site.links:
            if urlsplit(link).scheme not in ("", "https", "mailto"):
                with self.subTest(link=link):
                    self.fail(f"{link} is not https")

    def test_about_files_exist(self):
        paths = set(re.findall(r"[\"'](resources/about/[^\"']+\.md)[\"']", self.main_js))
        self.assertTrue(paths)
        for path in sorted(paths):
            with self.subTest(path=path):
                self.assertTrue((ROOT / path).read_text(encoding="utf-8").strip())

    def test_sitemap_and_robots_match_canonical(self):
        canonical = self.site.canonical
        self.assertTrue(canonical and canonical.startswith("https://"))
        namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        locations = [loc.text for loc in ET.parse(ROOT / "sitemap.xml").findall("s:url/s:loc", namespace)]
        self.assertIn(canonical, locations)
        robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
        self.assertIn(f"Sitemap: {canonical}sitemap.xml", robots)

    def test_readme_lists_the_required_shots(self):
        tree = ast.parse(BUILD_SITE.read_text(encoding="utf-8"))
        shots = next(
            [key.value for key in node.value.keys]
            for node in tree.body
            if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", None) == "SHOT_META"
        )
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        listed = re.findall(r"^(car_\w+)\.png$", readme, re.MULTILINE)
        self.assertEqual(listed, shots)


if __name__ == "__main__":
    unittest.main()
