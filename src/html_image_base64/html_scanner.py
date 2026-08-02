"""Aquí resuelvo la parte más delicada del ejercicio: encontrar los <img> sin dañar el resto del archivo.

Al principio pensé en resolver esto con una regex sobre todo el
documento, pero lo descarté rápido: los atributos pueden venir sin
comillas, en cualquier orden, con mayúsculas mezcladas, con /> de
autocierre... una regex genérica se vuelve frágil muy rápido. Terminé
usando html.parser.HTMLParser, que ya viene en la librería estándar y
tokeniza HTML de verdad. Lo interesante es que expone
get_starttag_text(), que me da el texto EXACTO del tag tal cual está
escrito en el archivo. Guardando en qué posición aparece cada uno,
puedo reconstruir el documento cambiando solo el src, sin reformatear
ni una coma del resto.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class ImgTagOccurrence:
    """Una aparición concreta de <img> en el HTML, con su posición exacta."""

    start_offset: int
    end_offset: int  # exclusivo
    original_tag_text: str
    src: str

    def rebuilt_tag(self, new_src: str) -> str:
        """Devuelvo el mismo tag pero con el src cambiado, todo lo demás igual."""
        return _replace_src_attribute(self.original_tag_text, new_src)


class ImgTagScanner(HTMLParser):
    """Recorre el HTML y va guardando cada <img> junto con dónde exactamente aparece."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self._occurrences: List[ImgTagOccurrence] = []
        self._line_offsets: List[int] = []

    def scan(self, html_text: str) -> List[ImgTagOccurrence]:
        self._occurrences = []
        self._line_offsets = _compute_line_offsets(html_text)
        self.reset()
        self.feed(html_text)
        self.close()
        return self._occurrences

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if tag.lower() != "img":
            return

        src = next((value for name, value in attrs if name.lower() == "src"), None)
        if not src:
            return  # un <img> sin src no tiene nada que convertir, lo dejo pasar

        # HTMLParser me da línea y columna, no un offset absoluto. Tengo
        # que traducir eso usando los saltos de línea que precalculé.
        tag_text = self.get_starttag_text() or ""
        line, col = self.getpos()
        start_offset = self._line_offsets[line - 1] + col
        end_offset = start_offset + len(tag_text)

        self._occurrences.append(
            ImgTagOccurrence(
                start_offset=start_offset,
                end_offset=end_offset,
                original_tag_text=tag_text,
                src=src,
            )
        )


# Esta regex ya no opera sobre el HTML completo, sino sobre el texto de
# un solo tag que ya aislé arriba. Así evito los problemas típicos de
# usar regex directamente sobre un documento entero.
_SRC_PATTERN = re.compile(
    r"""(?P<prefix>\bsrc\s*=\s*)(?P<quote>['"]?)(?P<value>.*?)(?(quote)(?P=quote)|(?=[\s/>]))""",
    re.IGNORECASE | re.DOTALL,
)


def _replace_src_attribute(tag_text: str, new_src: str) -> str:
    def _sub(match: re.Match) -> str:
        quote = match.group("quote") or '"'
        return f"{match.group('prefix')}{quote}{new_src}{quote}"

    new_text, count = _SRC_PATTERN.subn(_sub, tag_text, count=1)
    if count == 0:
        # No debería llegar acá nunca, porque ya validé que el src existe
        # antes de crear la ocurrencia. Lo dejo como salvavidas por si algún
        # HTML raro se me escapa en el futuro.
        return tag_text
    return new_text


def _compute_line_offsets(text: str) -> List[int]:
    """Para cada línea guardo en qué posición absoluta del texto empieza.

    Lo necesito porque getpos() de HTMLParser trabaja con (línea, columna)
    y yo quiero un solo número: la posición absoluta dentro del string.
    """
    offsets = [0]
    for line in text.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line))
    return offsets
