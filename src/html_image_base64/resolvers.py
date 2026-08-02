"""Este módulo se encarga de conseguir los bytes reales de cada imagen.

Un src de <img> puede apuntar a cosas muy distintas: un archivo local,
una URL, o incluso ya venir como data URI. En vez de meter un montón de
ifs en un solo método, preferí darle a cada caso su propia clase
pequeña y dejar que una compuesta decida cuál usar. Si mañana me piden
soportar, no sé, imágenes en un bucket S3, agrego una clase más y no
toco nada de lo que ya funciona.
"""
from __future__ import annotations

import mimetypes
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Tuple


class ImageResolutionError(Exception):
    """La uso cuando no logré convertir un src en bytes, sea cual sea el motivo."""


class ImageSource(ABC):
    """El contrato que cumple cada estrategia de resolución de imágenes."""

    @abstractmethod
    def can_handle(self, src: str) -> bool:
        ...

    @abstractmethod
    def resolve(self, src: str, *, base_dir: Path) -> Tuple[bytes, str]:
        """Debe devolver (contenido_binario, mime_type)."""


class DataUriImageSource(ImageSource):
    """Cuando el src ya es un data URI, no hay nada que convertir; ya está embebido."""

    def can_handle(self, src: str) -> bool:
        return src.strip().lower().startswith("data:")

    def resolve(self, src: str, *, base_dir: Path) -> Tuple[bytes, str]:
        raise ImageResolutionError(
            "La imagen ya está embebida como data URI; no requiere conversión."
        )


class LocalFileImageSource(ImageSource):
    """El caso más común en la prueba: una ruta relativa o absoluta en disco."""

    def can_handle(self, src: str) -> bool:
        lowered = src.strip().lower()
        return not (lowered.startswith("http://") or lowered.startswith("https://"))

    def resolve(self, src: str, *, base_dir: Path) -> Tuple[bytes, str]:
        # Le quito query string y ancla si las trae, porque en el
        # filesystem esos caracteres no forman parte del nombre real.
        clean_src = src.split("#", 1)[0].split("?", 1)[0]
        candidate = Path(clean_src)
        full_path = candidate if candidate.is_absolute() else (base_dir / candidate)
        full_path = full_path.resolve()

        if not full_path.is_file():
            raise ImageResolutionError(f"Archivo de imagen no encontrado: {full_path}")

        mime_type, _ = mimetypes.guess_type(str(full_path))
        if mime_type is None or not mime_type.startswith("image/"):
            mime_type = "application/octet-stream"

        try:
            content = full_path.read_bytes()
        except OSError as exc:
            raise ImageResolutionError(f"No se pudo leer '{full_path}': {exc}") from exc

        return content, mime_type


class RemoteHttpImageSource(ImageSource):
    """La agregué como extra: si alguien referencia una imagen por URL, también la resuelvo.

    Uso urllib porque sigue siendo librería estándar; no necesito requests
    ni nada externo para esto.
    """

    def __init__(self, timeout_seconds: float = 10.0) -> None:
        self._timeout = timeout_seconds

    def can_handle(self, src: str) -> bool:
        return src.strip().lower().startswith(("http://", "https://"))

    def resolve(self, src: str, *, base_dir: Path) -> Tuple[bytes, str]:
        try:
            with urllib.request.urlopen(src, timeout=self._timeout) as response:
                content = response.read()
                mime_type = response.headers.get_content_type() or "application/octet-stream"
        except (urllib.error.URLError, ValueError, TimeoutError) as exc:
            raise ImageResolutionError(f"No se pudo descargar '{src}': {exc}") from exc

        if not mime_type.startswith("image/"):
            guessed, _ = mimetypes.guess_type(src)
            mime_type = guessed or mime_type

        return content, mime_type


class CompositeImageResolver:
    """El punto de entrada: prueba cada estrategia en orden y usa la primera que aplique."""

    def __init__(self, sources: Optional[List[ImageSource]] = None) -> None:
        self._sources = sources or [
            DataUriImageSource(),
            RemoteHttpImageSource(),
            LocalFileImageSource(),
        ]

    def resolve(self, src: str, *, base_dir: Path) -> Tuple[bytes, str]:
        for source in self._sources:
            if source.can_handle(src):
                return source.resolve(src, base_dir=base_dir)
        raise ImageResolutionError(f"Ninguna estrategia pudo manejar el src: {src}")
