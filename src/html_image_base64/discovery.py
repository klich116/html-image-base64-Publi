"""Este módulo resuelve algo puntual: qué archivos HTML tengo que procesar.

El enunciado pide aceptar tanto archivos sueltos como carpetas, y que
las carpetas se recorran con todo y subcarpetas. Preferí meter esa
lógica en su propia clase en vez de dejarla mezclada con el resto,
porque es un problema que no tiene nada que ver con leer HTML o
codificar imágenes.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Sequence

HTML_SUFFIXES = {".html", ".htm"}


class HtmlFileDiscoverer:
    """Convierte una lista de rutas (mezcladas, archivos o carpetas) en archivos HTML."""

    def __init__(self, html_suffixes: Iterable[str] = HTML_SUFFIXES) -> None:
        self._suffixes = {s.lower() for s in html_suffixes}

    def discover(self, inputs: Sequence[str | Path]) -> List[Path]:
        """Devuelvo la lista final de HTML, ya sin duplicados y ordenada.

        Para cada ruta que me pasan reviso tres casos: si ya es un
        archivo HTML lo agrego directo, si es una carpeta la recorro
        completa (subcarpetas incluidas), y si no es ninguna de las dos
        cosas simplemente la ignoro. No lancé una excepción ahí a
        propósito, me pareció más útil que el proceso siga con lo que sí
        sirve en vez de detenerse por una ruta suelta que no existe.
        """
        found: set[Path] = set()

        for raw in inputs:
            path = Path(raw).expanduser().resolve()

            if path.is_file() and self._is_html(path):
                found.add(path)
            elif path.is_dir():
                found.update(self._scan_directory(path))

        return sorted(found)

    def _scan_directory(self, directory: Path) -> Iterable[Path]:
        for suffix in self._suffixes:
            yield from directory.rglob(f"*{suffix}")

    def _is_html(self, path: Path) -> bool:
        return path.suffix.lower() in self._suffixes
