# inbox/

Esta es la carpeta que reviso automáticamente. La idea es simple: dejas
acá tus archivos `.html` (y sus imágenes, respetando las rutas
relativas que uses en el `src` de cada `<img>`), le haces push a
`main`, y GitHub Actions corre el conversor por ti. No hace falta que
toques nada más.

## Cómo usarla

1. Crea una subcarpeta con el nombre que quieras dentro de `inbox/`
   (por ejemplo `inbox/prueba-1/`) y mete ahí tu(s) HTML y las
   imágenes que referencian.
2. Haz commit y push a `main` (o edítalo directo desde la web de
   GitHub con "Add file" → "Upload files").
3. Entra a la pestaña **Actions** del repo: vas a ver correr el
   workflow "procesar inbox".
4. Cuando termine (toma un par de minutos), revisa la carpeta
   `inbox_output/`, con la misma subcarpeta que creaste pero ya con
   los HTML convertidos, el `report.json` y el `dashboard.html` de esa
   corrida.

No borro ni modifico nada de lo que subas en `inbox/`; todo lo nuevo
se escribe en `inbox_output/`, aparte.
