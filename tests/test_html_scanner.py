import unittest

from html_image_base64.html_scanner import ImgTagScanner


# Acá pruebo la parte que más me preocupaba de todo el ejercicio: que
# los offsets que calculo coincidan de verdad con el texto original,
# porque de eso depende no romper el HTML al reemplazar el src.
class ImgTagScannerTests(unittest.TestCase):
    def setUp(self):
        self.scanner = ImgTagScanner()

    def test_finds_single_image(self):
        html = '<html><body><img src="a.png" alt="x"></body></html>'
        occurrences = self.scanner.scan(html)
        self.assertEqual(len(occurrences), 1)
        self.assertEqual(occurrences[0].src, "a.png")

    def test_offsets_allow_exact_slicing(self):
        # Si esto falla, significa que mi cuenta de línea/columna a offset
        # absoluto está mal, y ahí sí se me arruina todo el reemplazo.
        html = '<p>hola</p><img src="a.png">'
        occurrences = self.scanner.scan(html)
        occ = occurrences[0]
        self.assertEqual(html[occ.start_offset:occ.end_offset], occ.original_tag_text)

    def test_handles_single_and_double_quotes(self):
        html = "<img src='a.png'><img src=\"b.png\">"
        occurrences = self.scanner.scan(html)
        srcs = [o.src for o in occurrences]
        self.assertEqual(srcs, ["a.png", "b.png"])

    def test_ignores_img_without_src(self):
        html = '<img alt="sin src">'
        occurrences = self.scanner.scan(html)
        self.assertEqual(occurrences, [])

    def test_rebuilt_tag_replaces_only_src(self):
        html = '<img src="a.png" alt="x" class="y">'
        occ = self.scanner.scan(html)[0]
        rebuilt = occ.rebuilt_tag("data:image/png;base64,XXXX")
        self.assertIn('src="data:image/png;base64,XXXX"', rebuilt)
        self.assertIn('alt="x"', rebuilt)
        self.assertIn('class="y"', rebuilt)

    def test_multiline_and_multiple_images_offsets_are_independent(self):
        html = (
            "<html>\n"
            "  <img src=\"one.png\">\n"
            "  <p>texto</p>\n"
            "  <img src=\"two.png\">\n"
            "</html>"
        )
        occurrences = self.scanner.scan(html)
        self.assertEqual(len(occurrences), 2)
        for occ in occurrences:
            self.assertEqual(html[occ.start_offset:occ.end_offset], occ.original_tag_text)


if __name__ == "__main__":
    unittest.main()
