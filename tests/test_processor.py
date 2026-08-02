import base64
import shutil
import tempfile
import unittest
from pathlib import Path

from html_image_base64.processor import HtmlImageProcessor


# Estos son los tests que más me importan, porque prueban el flujo
# completo de punta a punta, tal como lo pide el enunciado.
class HtmlImageProcessorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "img").mkdir()
        (self.tmp / "img" / "logo.png").write_bytes(b"\x89PNG\r\n\x1a\nDATA")
        self.html_path = self.tmp / "page.html"
        self.html_path.write_text(
            '<html><body>'
            '<img src="img/logo.png" alt="ok">'
            '<img src="img/missing.png" alt="fail">'
            '</body></html>'
        )
        self.processor = HtmlImageProcessor()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_creates_new_file_and_preserves_original(self):
        # Reviso que el original no se toque para nada; es un requisito
        # explícito del enunciado y no quería confiarme.
        run_report = self.processor.process([str(self.html_path)])
        file_report = run_report.files[0]

        original_still_has_reference = "img/logo.png" in self.html_path.read_text()
        self.assertTrue(original_still_has_reference)

        output_path = Path(file_report.output_file)
        self.assertTrue(output_path.exists())
        self.assertNotEqual(output_path, self.html_path)

    def test_success_and_fail_are_tracked_per_image(self):
        run_report = self.processor.process([str(self.html_path)])
        file_report = run_report.files[0]

        self.assertIn("img/logo.png", file_report.success)
        self.assertIn("img/missing.png", file_report.fail)
        self.assertEqual(run_report.total_success, 1)
        self.assertEqual(run_report.total_fail, 1)

    def test_output_html_embeds_base64_for_successful_image(self):
        run_report = self.processor.process([str(self.html_path)])
        output_text = Path(run_report.files[0].output_file).read_text()

        expected_b64 = base64.b64encode(b"\x89PNG\r\n\x1a\nDATA").decode("ascii")
        self.assertIn(expected_b64, output_text)
        self.assertIn("img/missing.png", output_text)  # el que falló se deja intacto

    def test_run_report_to_dict_has_required_top_level_shape(self):
        run_report = self.processor.process([str(self.html_path)])
        data = run_report.to_dict()
        self.assertIn("success", data)
        self.assertIn("fail", data)

    def test_processing_directory_recurses_subfolders(self):
        sub = self.tmp / "sub"
        sub.mkdir()
        (sub / "other.html").write_text("<html><body>no images here</body></html>")

        run_report = self.processor.process([str(self.tmp)])
        processed_names = {Path(f.source_file).name for f in run_report.files}
        self.assertEqual(processed_names, {"page.html", "other.html"})


if __name__ == "__main__":
    unittest.main()
