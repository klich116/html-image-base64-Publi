"""Acá convierto un RunReport en algo que se pueda leer de verdad.

Separé "qué pasó" (que vive en models.py) de "cómo lo muestro" (este
archivo) porque son preocupaciones distintas. Termine dando dos
salidas: un JSON plano con la forma {success: {}, fail: {}} que pide el
enunciado, y un dashboard en HTML que arme yo mismo con CSS y un poco
de gradientes, sin depender de ningún framework externo, para poder
mirar de un vistazo cómo salió la corrida.
"""
from __future__ import annotations

import json
from html import escape
from pathlib import Path

from .models import RunReport


class JsonReportWriter:
    """El writer más simple: vuelco el reporte tal cual a un .json."""

    def write(self, run_report: RunReport, output_path: str) -> None:
        Path(output_path).write_text(
            json.dumps(run_report.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


class HtmlDashboardReportWriter:
    """El writer que sí me tomé mi tiempo en diseñar: un tablero visual del RunReport.

    No quería entregar una tabla plana de toda la vida, pero tampoco el
    típico dashboard oscuro con gradientes morados que se ve en
    cualquier demo generada automáticamente. Terminé inspirándome en
    una ficha de archivo o expediente de laboratorio: fondo claro tipo
    papel, tipografía serif para los títulos, monoespaciada para los
    datos, y bordes sólidos en vez de blur. Todo vive en un solo HTML
    autocontenido, para que se pueda abrir con doble clic sin depender
    de nada más.
    """

    def write(self, run_report: RunReport, output_path: str) -> None:
        Path(output_path).write_text(
            self._render(run_report), encoding="utf-8"
        )

    def _render(self, run: RunReport) -> str:
        total = run.total_success + run.total_fail
        success_pct = round((run.total_success / total) * 100, 1) if total else 0.0

        file_cards = "\n".join(self._render_file_card(f) for f in run.files) or (
            '<p class="empty">No se procesó ningún archivo HTML.</p>'
        )

        run_id = run.generated_at.replace(":", "").replace("-", "")[:14]

        return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Expediente de conversión · html-image-base64</title>
<style>
{_CSS}
</style>
</head>
<body>
<main>
  <header class="masthead">
    <div class="masthead-top">
      <span class="folio">N.º {escape(run_id)}</span>
      <span class="folio">html-image-base64</span>
    </div>
    <h1>Expediente de conversión de imágenes</h1>
    <p class="dek">Cada archivo HTML de entrada, sus imágenes y qué pasó con cada una.</p>
    <p class="timestamp">Registrado el {escape(run.generated_at)} (hora Colombia, UTC-5)</p>
  </header>

  <section class="ledger">
    <div class="ledger-cell">
      <span class="ledger-value">{len(run.files):02d}</span>
      <span class="ledger-label">archivos<br>procesados</span>
    </div>
    <div class="ledger-cell ok">
      <span class="ledger-value">{run.total_success:02d}</span>
      <span class="ledger-label">imágenes<br>convertidas</span>
    </div>
    <div class="ledger-cell bad">
      <span class="ledger-value">{run.total_fail:02d}</span>
      <span class="ledger-label">imágenes<br>con error</span>
    </div>
    <div class="ledger-cell stamp-cell">
      <div class="stamp">
        <span class="stamp-pct">{success_pct}%</span>
        <span class="stamp-caption">tasa de éxito</span>
      </div>
    </div>
  </section>

  <section class="files">
    {file_cards}
  </section>

  <footer>
    <span class="stitch"></span>
    <p>Generado por html_image_base64 &mdash; únicamente librería estándar de Python.</p>
  </footer>
</main>
</body>
</html>"""

    def _render_file_card(self, file_report) -> str:
        # Una ficha por archivo HTML procesado, con una fila por imagen:
        # marca de "ok" si se convirtió, marca de "x" con el motivo si falló.
        # El src puede ser una ruta corta o una URL kilométrica (como una
        # de Wikipedia con todo y su thumbnail). Si meto el src y el
        # texto de estado en la misma línea sin darles su propio
        # espacio, cuando no caben uno al lado del otro terminan
        # aplastándose y el navegador rompe la URL letra por letra para
        # que quepa. Por eso separo cada fila en dos renglones propios
        # (row-src / row-status) en vez de una sola línea rígida.
        rows = []
        for src, outcome in file_report.success.items():
            rows.append(
                f'<li class="row ok">'
                f'<span class="mark">✓</span>'
                f'<div class="row-body">'
                f'<code class="row-src">{escape(src)}</code>'
                f'<span class="row-status">{escape(outcome.mime_type or "")} · '
                f'{_human_size(outcome.size_bytes)}</span>'
                f'</div></li>'
            )
        for src, outcome in file_report.fail.items():
            rows.append(
                f'<li class="row bad">'
                f'<span class="mark">✕</span>'
                f'<div class="row-body">'
                f'<code class="row-src">{escape(src)}</code>'
                f'<span class="row-status">{escape(outcome.error or "error desconocido")}</span>'
                f'</div></li>'
            )

        rows_html = "\n".join(rows) or '<li class="row empty">Sin imágenes detectadas.</li>'
        error_banner = (
            f'<p class="file-error">Nota: {escape(file_report.error)}</p>'
            if file_report.error
            else ""
        )

        return f"""
    <article class="file-card">
      <div class="file-card-header">
        <h2>{escape(Path(file_report.source_file).name)}</h2>
        <span class="tag">{len(file_report.success):02d} ok &middot; {len(file_report.fail):02d} error</span>
      </div>
      <p class="path">{escape(file_report.source_file)}</p>
      {error_banner}
      <ul class="rows">
        {rows_html}
      </ul>
    </article>"""


def _human_size(num_bytes) -> str:
    if not num_bytes:
        return "0 B"
    for unit in ("B", "KB", "MB", "GB"):
        if num_bytes < 1024:
            return f"{num_bytes:.0f} {unit}" if unit == "B" else f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"


_CSS = """
/* Elegí esta paleta pensando en papel y tinta, no en pantallas: fondo
   crudo tipo cartulina, tinta casi negra, y dos acentos que se sienten
   más de sello de archivo que de producto de software: terracota para
   lo que falló, verde botella para lo que salió bien. Nada de morado,
   nada de azul eléctrico. */
:root {
  --paper: #f2ede3;
  --paper-raised: #ffffff;
  --ink: #201c16;
  --ink-soft: #6b6255;
  --line: #d8cfbd;
  --ok: #2f5d43;
  --ok-bg: #e4ecdf;
  --bad: #a5401f;
  --bad-bg: #f3e2d4;
  --mustard: #c98a2c;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  background-color: var(--paper);
  background-image:
    radial-gradient(var(--line) 0.6px, transparent 0.6px);
  background-size: 22px 22px;
  color: var(--ink);
  font-family: 'Iowan Old Style', 'Palatino Linotype', Georgia, 'Times New Roman', serif;
  -webkit-font-smoothing: antialiased;
}

code, .mono {
  font-family: 'JetBrains Mono', 'Courier New', ui-monospace, monospace;
}

main {
  max-width: 880px;
  margin: 0 auto;
  padding: 64px 28px 90px;
}

.masthead {
  border-top: 3px solid var(--ink);
  border-bottom: 1px solid var(--ink);
  padding: 18px 0 26px;
  margin-bottom: 40px;
}
.masthead-top {
  display: flex; justify-content: space-between;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11.5px; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--ink-soft); margin-bottom: 22px;
}
.masthead h1 {
  font-size: clamp(30px, 4.4vw, 46px);
  line-height: 1.08;
  margin: 0 0 10px;
  font-weight: 600;
  letter-spacing: -0.01em;
}
.dek {
  font-size: 16px; color: var(--ink-soft); margin: 0 0 14px; max-width: 46ch;
  font-style: italic;
}
.timestamp {
  font-family: 'JetBrains Mono', monospace; font-size: 11.5px;
  color: var(--ink-soft); margin: 0; text-transform: uppercase; letter-spacing: 0.05em;
}

.ledger {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  border: 1px solid var(--ink);
  margin-bottom: 46px;
}
.ledger-cell {
  padding: 20px 14px;
  text-align: center;
  border-right: 1px solid var(--ink);
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px;
}
.ledger-cell:last-child { border-right: none; }
.ledger-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 34px; font-weight: 700;
}
.ledger-cell.ok .ledger-value { color: var(--ok); }
.ledger-cell.bad .ledger-value { color: var(--bad); }
.ledger-label {
  font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.07em;
  color: var(--ink-soft); line-height: 1.3;
}
.stamp-cell { background: var(--paper-raised); }
.stamp {
  width: 74px; height: 74px; border-radius: 50%;
  border: 2px solid var(--mustard);
  outline: 1px dashed var(--mustard);
  outline-offset: 4px;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  transform: rotate(-6deg);
}
.stamp-pct {
  font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 15px; color: var(--mustard);
}
.stamp-caption {
  font-size: 7.5px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--mustard);
}

.files { display: flex; flex-direction: column; gap: 22px; }
.file-card {
  background: var(--paper-raised);
  border: 1px solid var(--line);
  border-left: 4px solid var(--ink);
  padding: 22px 24px;
}
.file-card-header {
  display: flex; justify-content: space-between; align-items: baseline; gap: 12px; flex-wrap: wrap;
}
.file-card-header h2 {
  font-size: 19px; margin: 0; font-weight: 600;
}
.tag {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px; color: var(--ink-soft);
  border: 1px solid var(--line); padding: 3px 9px; white-space: nowrap;
}
.path {
  font-family: 'JetBrains Mono', monospace;
  color: var(--ink-soft); font-size: 11.5px; margin: 5px 0 16px; word-break: break-all;
}
.file-error {
  color: var(--bad); font-size: 13px; margin: 0 0 14px;
  font-style: italic;
}

.rows { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; }
.row {
  display: flex; align-items: flex-start; gap: 10px; font-size: 13px;
  padding: 9px 4px; border-top: 1px dotted var(--line);
}
.row:first-child { border-top: none; }
.mark {
  flex: none; width: 18px; text-align: center; margin-top: 1px;
  font-family: 'JetBrains Mono', monospace; font-weight: 700;
}
.row.ok .mark { color: var(--ok); }
.row.bad .mark { color: var(--bad); }
.row.empty { color: var(--ink-soft); font-style: italic; }

/* row-body es la clave: cada fila puede tener un src corto o una URL
   larguísima, así que dejo que el src y el estado se acomoden en su
   propia línea cuando no caben juntos, en vez de forzarlos a
   compartir una sola línea y que el navegador rompa la URL letra por
   letra para que quepa. */
.row-body {
  display: flex; flex-wrap: wrap; align-items: baseline;
  column-gap: 14px; row-gap: 2px; min-width: 0; flex: 1;
}
.row-src {
  color: var(--ink);
  overflow-wrap: anywhere;
  min-width: 0;
  flex: 1 1 220px;
}
.row-status {
  color: var(--ink-soft); font-size: 11px;
  overflow-wrap: anywhere;
  flex: 0 1 auto;
}
.row.bad .row-status { color: var(--bad); }

footer { margin-top: 60px; text-align: center; }
.stitch {
  display: block; height: 1px; margin: 0 auto 18px;
  background-image: repeating-linear-gradient(90deg, var(--ink) 0 6px, transparent 6px 12px);
  max-width: 240px;
}
footer p {
  font-family: 'JetBrains Mono', monospace; font-size: 11px;
  color: var(--ink-soft); letter-spacing: 0.03em;
}

@media (max-width: 640px) {
  .ledger { grid-template-columns: repeat(2, 1fr); }
  .ledger-cell:nth-child(2) { border-right: none; }
  .ledger-cell { border-bottom: 1px solid var(--ink); }
}
"""
