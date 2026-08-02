"""Acá van solo los modelos de datos, nada de lógica.

Los separé del resto a propósito: si mañana necesito cambiar cómo se
arma el reporte final, no quiero andar tocando el código que procesa
HTML. Son clases "tontas" a propósito, solo cargan información.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass(frozen=True)
class ImageOutcome:
    """Lo que pasó con una imagen puntual dentro de un HTML.

    La marco como frozen porque una vez que sé si una imagen se pudo
    convertir o no, ese resultado ya no debería cambiar bajo ningún
    escenario que se me ocurra.
    """

    src: str
    resolved_path: Optional[str] = None
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        data = {
            "src": self.src,
            "resolved_path": self.resolved_path,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
        }
        if self.error is not None:
            data["error"] = self.error
        return data


@dataclass
class FileReport:
    """Lo que pasó con UN archivo HTML completo: qué imágenes salieron bien y cuáles no."""

    source_file: str
    output_file: Optional[str] = None
    success: Dict[str, ImageOutcome] = field(default_factory=dict)
    fail: Dict[str, ImageOutcome] = field(default_factory=dict)
    error: Optional[str] = None  # esto solo se llena si el archivo en sí falló (no una imagen puntual)

    def add_success(self, outcome: ImageOutcome) -> None:
        self.success[outcome.src] = outcome

    def add_fail(self, outcome: ImageOutcome) -> None:
        self.fail[outcome.src] = outcome

    def to_dict(self) -> dict:
        return {
            "source_file": self.source_file,
            "output_file": self.output_file,
            "error": self.error,
            "success": {k: v.to_dict() for k, v in self.success.items()},
            "fail": {k: v.to_dict() for k, v in self.fail.items()},
        }


@dataclass
class RunReport:
    """La foto completa de una corrida: puede ser uno o cien archivos HTML."""

    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    files: List[FileReport] = field(default_factory=list)

    def add_file_report(self, report: FileReport) -> None:
        self.files.append(report)

    @property
    def success(self) -> Dict[str, dict]:
        """Junta todas las imágenes exitosas de todos los archivos, agrupadas por archivo."""
        return {
            f.source_file: {src: o.to_dict() for src, o in f.success.items()}
            for f in self.files
        }

    @property
    def fail(self) -> Dict[str, dict]:
        """Lo mismo que arriba pero para las que fallaron."""
        return {
            f.source_file: {src: o.to_dict() for src, o in f.fail.items()}
            for f in self.files
        }

    @property
    def total_success(self) -> int:
        return sum(len(f.success) for f in self.files)

    @property
    def total_fail(self) -> int:
        return sum(len(f.fail) for f in self.files)

    def to_dict(self) -> dict:
        """Esta es la forma exacta que pide el enunciado: {success: {}, fail: {}}.

        Le agregué un nivel extra por archivo antes de llegar al src de
        cada imagen. Lo hice así porque si dos HTML distintos usan una
        imagen con el mismo nombre (por ejemplo "logo.png" en dos
        carpetas), sin ese nivel intermedio una pisaría a la otra en el
        diccionario final. Con el archivo como llave superior, eso no
        puede pasar.
        """
        return {
            "generated_at": self.generated_at,
            "success": self.success,
            "fail": self.fail,
            "summary": {
                "files_processed": len(self.files),
                "files_with_errors": sum(1 for f in self.files if f.error),
                "images_success": self.total_success,
                "images_fail": self.total_fail,
            },
        }
