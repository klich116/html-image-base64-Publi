"""La puerta de entrada por terminal.

La dejé como una capa bien delgada encima de HtmlImageProcessor: acá
solo interpreto argumentos y decido qué archivos escribir, nada de
lógica de negocio. Un ejemplo de uso:

    python -m html_image_base64 sample_data/index.html --out demo_output
    python -m html_image_base64 sample_data/ --out demo_output --report demo_output/report.json
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .processor import HtmlImageProcessor
from .report import HtmlDashboardReportWriter, JsonReportWriter


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="html_image_base64",
        description=(
            "Recorre archivos y/o directorios HTML, convierte sus imágenes "
            "<img src=...> a Base64 embebido y genera un nuevo archivo por cada HTML."
        ),
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        help="Uno o más archivos .html o directorios (se recorren recursivamente).",
    )
    parser.add_argument(
        "--out",
        dest="output_dir",
        default=None,
        help="Directorio donde escribir los HTML resultantes (por defecto: junto al original).",
    )
    parser.add_argument(
        "--report",
        dest="report_path",
        default=None,
        help="Ruta del reporte JSON {success, fail} a generar.",
    )
    parser.add_argument(
        "--dashboard",
        dest="dashboard_path",
        default=None,
        help="Ruta del dashboard HTML visual a generar.",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Activa logging detallado (DEBUG)."
    )
    return parser


def main(argv=None) -> int:
    args = build_arg_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    processor = HtmlImageProcessor()
    run_report = processor.process(args.inputs, output_dir=args.output_dir)

    if args.report_path:
        Path(args.report_path).parent.mkdir(parents=True, exist_ok=True)
        JsonReportWriter().write(run_report, args.report_path)
        print(f"Reporte JSON escrito en: {args.report_path}")

    if args.dashboard_path:
        Path(args.dashboard_path).parent.mkdir(parents=True, exist_ok=True)
        HtmlDashboardReportWriter().write(run_report, args.dashboard_path)
        print(f"Dashboard HTML escrito en: {args.dashboard_path}")

    print(
        f"Archivos procesados: {len(run_report.files)} | "
        f"Imágenes OK: {run_report.total_success} | "
        f"Imágenes con error: {run_report.total_fail}"
    )
    # Devuelvo 1 si algo falló para que se pueda usar este comando en un
    # pipeline de CI y se note si hubo imágenes que no se pudieron convertir.
    return 0 if run_report.total_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
