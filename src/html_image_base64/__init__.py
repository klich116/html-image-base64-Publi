"""Este es el paquete que resuelve el ejercicio de imágenes en HTML.

La idea nació simple: recorro archivos HTML, encuentro sus imágenes y
las dejo embebidas en Base64 dentro de un archivo nuevo, sin tocar el
original. Me impuse una sola restricción de diseño desde el principio:
nada de librerías de terceros, todo con lo que trae Python de fábrica.
"""
from .models import ImageOutcome, FileReport, RunReport
from .processor import HtmlImageProcessor

__all__ = [
    "ImageOutcome",
    "FileReport",
    "RunReport",
    "HtmlImageProcessor",
]

__version__ = "1.0.0"
