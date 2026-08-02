"""Este es el que amarra todo: recibe rutas, entrega el reporte final.

Preferí armarlo como una fachada delgada en vez de meter toda la lógica
acá dentro. Cada colaborador (discoverer, scanner, resolver, encoder) se
lo puedo pasar por constructor, y si no le paso nada usa los de
siempre. Eso me sirvió muchísimo a la hora de escribir los tests: pude
probar cada pieza por separado sin necesitar que las demás existieran.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional, Sequence

from .discovery import HtmlFileDiscoverer
from .encoder import Base64ImageEncoder
from .html_scanner import ImgTagScanner
from .models import FileReport, ImageOutcome, RunReport
from .resolvers import CompositeImageResolver, ImageResolutionError

logger = logging.getLogger("html_image_base64")


class HtmlImageProcessor:
    """El punto de entrada de toda la librería."""

    def __init__(
        self,
        discoverer: Optional[HtmlFileDiscoverer] = None,
        scanner: Optional[ImgTagScanner] = None,
        resolver: Optional[CompositeImageResolver] = None,
        encoder: Optional[Base64ImageEncoder] = None,
        output_suffix: str = ".base64",
    ) -> None:
        self._discoverer = discoverer or HtmlFileDiscoverer()
        self._scanner = scanner or ImgTagScanner()
        self._resolver = resolver or CompositeImageResolver()
        self._encoder = encoder or Base64ImageEncoder()
        self._output_suffix = output_suffix

    def process(
        self,
        inputs: Sequence[str],
        output_dir: Optional[str] = None,
    ) -> RunReport:
        """Recibo archivos y/o carpetas mezclados y devuelvo el reporte de toda la corrida.

        Nada me impide que `inputs` traiga a la vez un .html suelto y una
        carpeta llena de subcarpetas; el discoverer se encarga de
        aplanar todo eso antes de que yo empiece a procesar.
        """
        html_files = self._discoverer.discover(inputs)
        run_report = RunReport()

        if not html_files:
            logger.warning("No se encontraron archivos HTML en las rutas dadas: %s", inputs)

        for html_file in html_files:
            file_report = self._process_single_file(html_file, output_dir)
            run_report.add_file_report(file_report)

        return run_report

    def _process_single_file(self, html_file: Path, output_dir: Optional[str]) -> FileReport:
        report = FileReport(source_file=str(html_file))

        try:
            original_text = html_file.read_text(encoding="utf-8", errors="strict")
        except (OSError, UnicodeDecodeError) as exc:
            report.error = f"No se pudo leer el archivo: {exc}"
            logger.error("Error leyendo %s: %s", html_file, exc)
            return report

        occurrences = self._scanner.scan(original_text)
        base_dir = html_file.parent
        new_text = original_text

        # Voy reemplazando de atrás hacia adelante. Si lo hiciera de
        # adelante hacia atrás, el primer reemplazo cambiaría la longitud
        # del texto y dejaría inválidos todos los offsets que ya había
        # calculado para las ocurrencias siguientes.
        for occurrence in sorted(occurrences, key=lambda o: o.start_offset, reverse=True):
            outcome, replacement_tag = self._process_occurrence(occurrence, base_dir)
            if outcome.error is None:
                report.add_success(outcome)
                new_text = (
                    new_text[: occurrence.start_offset]
                    + replacement_tag
                    + new_text[occurrence.end_offset :]
                )
            else:
                # Si una imagen puntual falla, no boto todo el archivo:
                # dejo su tag original tal cual estaba y sigo con las demás.
                report.add_fail(outcome)

        output_path = self._build_output_path(html_file, output_dir)
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(new_text, encoding="utf-8")
            report.output_file = str(output_path)
        except OSError as exc:
            report.error = f"No se pudo escribir el archivo de salida: {exc}"
            logger.error("Error escribiendo %s: %s", output_path, exc)

        return report

    def _process_occurrence(self, occurrence, base_dir: Path):
        try:
            content, mime_type = self._resolver.resolve(occurrence.src, base_dir=base_dir)
            data_uri = self._encoder.encode(content, mime_type)
            outcome = ImageOutcome(
                src=occurrence.src,
                resolved_path=str((base_dir / occurrence.src).resolve())
                if not occurrence.src.lower().startswith(("http://", "https://", "data:"))
                else occurrence.src,
                mime_type=mime_type,
                size_bytes=len(content),
            )
            return outcome, occurrence.rebuilt_tag(data_uri)
        except ImageResolutionError as exc:
            outcome = ImageOutcome(src=occurrence.src, error=str(exc))
            return outcome, occurrence.original_tag_text

    def _build_output_path(self, html_file: Path, output_dir: Optional[str]) -> Path:
        # Nunca toco el archivo original: siempre genero uno nuevo con
        # sufijo .base64 antes de la extensión, ya sea al lado del
        # original o en el directorio de salida que me hayan indicado.
        new_name = f"{html_file.stem}{self._output_suffix}{html_file.suffix}"
        if output_dir:
            return Path(output_dir) / new_name
        return html_file.with_name(new_name)
