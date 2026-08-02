"""La parte más simple de todo el ejercicio: pasar bytes a Base64.

Le di su propia clase de una sola línea de lógica porque, aunque hoy es
trivial, si mañana necesito cambiar el formato del data URI (agregar
metadata, comprimir antes de codificar, lo que sea) quiero tocar solo
este archivo.
"""
from __future__ import annotations

import base64


class Base64ImageEncoder:
    """Envuelve base64.b64encode y arma el data URI listo para meter en el src."""

    def encode(self, content: bytes, mime_type: str) -> str:
        b64_payload = base64.b64encode(content).decode("ascii")
        return f"data:{mime_type};base64,{b64_payload}"
