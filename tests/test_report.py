import json
import shutil
import tempfile
import unittest
from pathlib import Path

from html_image_base64.models import FileReport, ImageOutcome, RunReport
from html_image_base64.report import HtmlDashboardReportWriter, JsonReportWriter


# Nada muy elaborado acá, solo confirmo que cada writer produce algo
# con la forma que espero.
class ReportWritersTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        run = RunReport()
        fr = FileReport(source_file="a.html", output_file="a.base64.html")
        fr.add_success(ImageOutcome(src="x.png", mime_type="image/png", size_bytes=10))
        fr.add_fail(ImageOutcome(src="y.png", error="no encontrado"))
        run.add_file_report(fr)
        self.run = run

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_json_report_has_expected_shape(self):
        out = self.tmp / "report.json"
        JsonReportWriter().write(self.run, str(out))
        data = json.loads(out.read_text())
        self.assertIn("x.png", data["success"]["a.html"])
        self.assertIn("y.png", data["fail"]["a.html"])

    def test_html_dashboard_is_valid_and_contains_key_data(self):
        out = self.tmp / "dashboard.html"
        HtmlDashboardReportWriter().write(self.run, str(out))
        content = out.read_text()
        self.assertIn("<!DOCTYPE html>", content)
        self.assertIn("x.png", content)
        self.assertIn("no encontrado", content)


if __name__ == "__main__":
    unittest.main()
