# Esto es lo que permite correr "python -m html_image_base64 ...".
from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
