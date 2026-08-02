import base64
import shutil
import tempfile
import unittest
from pathlib import Path

from html_image_base64.resolvers import (
    CompositeImageResolver,
    DataUriImageSource,
    ImageResolutionError,
    LocalFileImageSource,
)


# El caso más común en la prueba es justamente este: imágenes locales.
class LocalFileImageSourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "img.png").write_bytes(b"\x89PNG\r\n\x1a\nfake")
        self.source = LocalFileImageSource()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_can_handle_relative_paths(self):
        self.assertTrue(self.source.can_handle("img.png"))
        self.assertFalse(self.source.can_handle("https://example.com/img.png"))

    def test_resolve_reads_bytes_and_mime(self):
        content, mime = self.source.resolve("img.png", base_dir=self.tmp)
        self.assertTrue(content.startswith(b"\x89PNG"))
        self.assertEqual(mime, "image/png")

    def test_resolve_raises_when_missing(self):
        with self.assertRaises(ImageResolutionError):
            self.source.resolve("no-existe.png", base_dir=self.tmp)

    def test_resolve_strips_query_and_fragment(self):
        content, _ = self.source.resolve("img.png?v=2#frag", base_dir=self.tmp)
        self.assertTrue(content.startswith(b"\x89PNG"))


class DataUriImageSourceTests(unittest.TestCase):
    def test_can_handle_data_uri(self):
        source = DataUriImageSource()
        self.assertTrue(source.can_handle("data:image/png;base64,AAA"))
        self.assertFalse(source.can_handle("a.png"))

    def test_resolve_always_fails_with_clear_message(self):
        source = DataUriImageSource()
        with self.assertRaises(ImageResolutionError):
            source.resolve("data:image/png;base64,AAA", base_dir=Path("."))


class CompositeImageResolverTests(unittest.TestCase):
    def test_picks_local_strategy_by_default(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            (tmp / "x.png").write_bytes(b"\x89PNG123")
            resolver = CompositeImageResolver()
            content, mime = resolver.resolve("x.png", base_dir=tmp)
            self.assertEqual(content, b"\x89PNG123")
            self.assertEqual(mime, "image/png")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_raises_when_no_strategy_matches(self):
        class NothingResolver(CompositeImageResolver):
            def __init__(self):
                super().__init__(sources=[])

        with self.assertRaises(ImageResolutionError):
            NothingResolver().resolve("whatever", base_dir=Path("."))


if __name__ == "__main__":
    unittest.main()
