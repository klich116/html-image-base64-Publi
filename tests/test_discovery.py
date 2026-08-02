import shutil
import tempfile
import unittest
from pathlib import Path

from html_image_base64.discovery import HtmlFileDiscoverer


# Estos tests cubren los tres casos que me importaban del discoverer:
# que encuentre un archivo suelto, que recorra carpetas completas con
# subcarpetas, y que ignore silenciosamente lo que no es HTML.
class HtmlFileDiscovererTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "a.html").write_text("<html></html>")
        (self.tmp / "b.txt").write_text("no html")
        nested = self.tmp / "nested" / "deep"
        nested.mkdir(parents=True)
        (nested / "c.htm").write_text("<html></html>")
        self.discoverer = HtmlFileDiscoverer()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_discovers_direct_file(self):
        result = self.discoverer.discover([str(self.tmp / "a.html")])
        self.assertEqual(len(result), 1)

    def test_discovers_directory_recursively(self):
        result = self.discoverer.discover([str(self.tmp)])
        names = {p.name for p in result}
        self.assertEqual(names, {"a.html", "c.htm"})

    def test_ignores_non_html_and_missing_paths(self):
        result = self.discoverer.discover([str(self.tmp / "b.txt"), str(self.tmp / "no-existe")])
        self.assertEqual(result, [])

    def test_deduplicates_when_same_file_listed_twice(self):
        p = str(self.tmp / "a.html")
        result = self.discoverer.discover([p, p, str(self.tmp)])
        names = [x.name for x in result]
        self.assertEqual(names.count("a.html"), 1)


if __name__ == "__main__":
    unittest.main()
