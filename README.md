# html-image-base64

Ver el dashboard de resultados en vivo (GitHub Pages, una vez activado en Settings → Pages): **https://klich116.github.io/html-image-base64-Publi/**

Convierte las imágenes referenciadas dentro de archivos HTML (`<img src="...">`) a **Base64** embebido (data URI), generando un **archivo nuevo** por cada HTML procesado y dejando siempre el original intacto.

Resuelve el ejercicio *"Procesamiento de archivos HTML en Python"* de la prueba de Ingeniería de Datos. Solo usa la **librería estándar de Python** (3.9+): `html.parser`, `base64`, `pathlib`, `mimetypes`, `urllib`, `argparse`, `dataclasses`, `unittest`, `json`, `re`, `logging`.

## Demo rápida

```bash
python3 -m venv .venv && source .venv/bin/activate   # opcional, no hay dependencias externas
export PYTHONPATH=src

python3 -m html_image_base64 sample_data \
  --out demo_output/converted \
  --report demo_output/report.json \
  --dashboard demo_output/dashboard.html -v
```

Esto procesa `sample_data/` (incluye un subdirectorio, imágenes PNG/JPG/SVG reales y una referencia rota a propósito) y genera:

- `demo_output/converted/*.base64.html` — los HTML nuevos, con imágenes embebidas.
- `demo_output/report.json` — el objeto `{success, fail}` pedido en el enunciado.
- `demo_output/dashboard.html` — **reporte visual** (abrir en el navegador) con el resumen de la corrida.

También hay un `Makefile`: `make test` y `make demo`.

## Uso como CLI

```
python3 -m html_image_base64 <archivo_o_directorio> [<otro> ...] \
    [--out DIR] [--report report.json] [--dashboard dashboard.html] [-v]
```

- Acepta **mezclar** archivos `.html`/`.htm` y directorios; los directorios se recorren recursivamente (incluye subdirectorios), según lo pedido en el enunciado.
- `--out` controla dónde se escriben los HTML resultantes. Si se omite, cada archivo nuevo se escribe junto al original con sufijo `.base64` (p. ej. `index.html` → `index.base64.html`), **nunca se sobreescribe el original**.

## Uso como librería

```python
from html_image_base64 import HtmlImageProcessor

processor = HtmlImageProcessor()
run_report = processor.process(["carpeta_con_html/", "otro_archivo.html"])

data = run_report.to_dict()
# {
#   "success": {"archivo.html": {"img/logo.png": {...}}},
#   "fail":    {"archivo.html": {"img/roto.png": {"error": "..."}}},
#   "summary": {...}
# }
```

## Arquitectura y decisiones de diseño

El paquete `src/html_image_base64/` está dividido por responsabilidad (SRP), cada pieza inyectable y sustituible (DIP), pensado para que agregar un nuevo tipo de origen de imagen o un nuevo formato de reporte **no requiera tocar el resto del código** (OCP):

| Módulo | Responsabilidad |
|---|---|
| `discovery.py` | `HtmlFileDiscoverer`: resuelve una lista mixta de archivos/directorios a la lista final de archivos HTML (recursivo, deduplicado). |
| `html_scanner.py` | `ImgTagScanner`: usa `html.parser.HTMLParser` (no regex "a ciegas") para localizar cada `<img>` y su **offset exacto** en el texto original, vía `get_starttag_text()` + `getpos()`. Esto permite reconstruir el HTML reemplazando *solo* el atributo `src`, preservando indentación, comillas, atributos y formato del resto del archivo byte a byte. |
| `resolvers.py` | Patrón *Strategy*: `ImageSource` (interfaz) con implementaciones `LocalFileImageSource`, `RemoteHttpImageSource` (URLs `http(s)` vía `urllib`, sin dependencias externas) y `DataUriImageSource` (detecta imágenes ya embebidas y las deja igual). `CompositeImageResolver` elige la estrategia adecuada según el `src`. |
| `encoder.py` | `Base64ImageEncoder`: envuelve `base64.b64encode` en un data URI válido. |
| `models.py` | `ImageOutcome`, `FileReport`, `RunReport`: dataclasses inmutables/serializables. `RunReport.to_dict()` produce exactamente la forma `{success: {}, fail: {}}` pedida, agrupada por archivo para evitar colisiones cuando el mismo nombre de imagen se repite en distintos HTML. |
| `processor.py` | `HtmlImageProcessor`: orquesta discovery → scanner → resolver → encoder por archivo, reemplaza de atrás hacia adelante (por offset descendente) para no invertir los índices ya calculados, y escribe el archivo nuevo sin tocar el original. |
| `report.py` | `JsonReportWriter` y `HtmlDashboardReportWriter`: separan el *qué pasó* (el modelo) de *cómo se muestra* (JSON plano vs. tablero visual). |
| `cli.py` | Interfaz de línea de comandos (`argparse`), capa fina sobre `HtmlImageProcessor`. |

### Manejo de errores por imagen (no por archivo)

Si una imagen no se puede resolver (ruta rota, permiso denegado, timeout de red, MIME no soportado), se registra en `fail` con el motivo y **el tag original se deja intacto** en el HTML de salida; el resto de imágenes del mismo archivo se procesan con normalidad. Un archivo HTML solo se marca con error global si no se pudo leer o escribir.

### Por qué no usar solo expresiones regulares

Las regex sobre HTML son frágiles ante atributos sin comillas, orden variable de atributos, o `/>` de autocierre. Se usó `HTMLParser` (stdlib) como tokenizador real y una regex **acotada al texto del propio tag** (`_SRC_PATTERN` en `html_scanner.py`) solo para sustituir el valor de `src` dentro de ese fragmento ya aislado — lo mejor de ambos mundos sin salir de la librería estándar.

## Calidad de código

- **PEP 8 / type hints** en toda la base de código, dataclasses para modelos inmutables.
- **SOLID**: SRP (un módulo, una razón para cambiar), OCP (nuevas fuentes de imagen o writers de reporte sin modificar código existente), DIP (`HtmlImageProcessor` recibe sus colaboradores por constructor, con valores por defecto).
- **Sin dependencias externas**: cumple el requisito del ejercicio de usar únicamente la librería estándar.
- **25 pruebas unitarias** (`unittest`, stdlib) cubriendo discovery, scanner, resolvers, procesador end-to-end y generación de reportes. Correr con `make test`.

## Estructura del repositorio

```
html-image-base64/
├── src/html_image_base64/   # librería (paquete instalable)
├── tests/                   # 25 pruebas unitarias (unittest)
├── sample_data/              # HTML + imágenes reales de ejemplo (incluye subdirectorio y un src roto)
├── docs/                     # última corrida procesada, publicada vía GitHub Pages
├── demo_output/               # (generado) salida de la demo — ignorado por git
├── pyproject.toml / setup.cfg
├── Makefile
└── README.md
```

## Cómo cargar tus propios HTML al sistema (sin instalar nada)

Todo esto pasa dentro del repositorio de GitHub, con un Action que hace el trabajo por ti:

1. **Subes tu HTML (y sus imágenes) a la carpeta `inbox/`.** Creas una subcarpeta con el nombre que quieras (por ejemplo `inbox/mi-prueba/`) y metes ahí tu(s) `.html` junto con las imágenes que referencian, respetando las rutas relativas del `src`. Se puede hacer con `git push` o directo desde la web: botón **Add file → Upload files** dentro de `inbox/`, arrastrando la carpeta completa (GitHub conserva la estructura de subcarpetas).
2. **El GitHub Action se dispara solo** en cuanto detecta el cambio dentro de `inbox/`. Se ve corriendo en vivo en la pestaña **Actions** del repo, workflow "procesar inbox".
3. **Espera a que termine** (unos segundos). Va a aparecer un commit automático de `html-image-base64-bot` con el resultado.

### Dónde quedan los archivos convertidos

- **`inbox_output/`** — la salida completa de esa corrida: los HTML nuevos ya con las imágenes en Base64, el `report.json` con el objeto `{success, fail}`, y el `dashboard.html` visual. Queda en el propio repositorio, organizado igual que lo que subiste.
- **`docs/`** — es una copia de ese mismo resultado, pero publicada como página web (GitHub Pages). Cada corrida nueva pisa lo que había antes, así que **https://klich116.github.io/html-image-base64-Publi/** siempre muestra la última prueba, nunca una vieja. La primera vez hay que activarla en Settings → Pages → Branch: `main`, carpeta `/docs` → Save; después queda sola.

Si en cambio corres el CLI en tu propia máquina (ver "Uso como CLI" más abajo), el resultado queda donde tú le digas con `--out`, no en `inbox_output/` ni `docs/` — esas dos carpetas son exclusivas del flujo automático de GitHub. Los detalles de cómo organizar `inbox/` también están en `inbox/README.md`.

## Cómo subirlo a tu propio GitHub

Este proyecto ya viene con un repositorio git local inicializado y su primer commit. Para publicarlo:

```bash
gh repo create html-image-base64 --private --source=. --remote=origin --push
# o, sin gh CLI:
git remote add origin git@github.com:<tu-usuario>/html-image-base64.git
git branch -M main
git push -u origin main
```
