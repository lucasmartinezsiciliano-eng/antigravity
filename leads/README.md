# barber_scraper — Generador de leads de barberías en España

Extrae nombre, ciudad, provincia, teléfono, email, Instagram y web de barberías españolas y los exporta a Excel.

## Instalación

```bash
cd c:/Users/Pc2025/Desktop/ANTIGRAVITY/leads
pip install -r requirements.txt
```

## Uso básico

```bash
# Todos los pasos (OSM + Maps + Instagram + Emails)
python barber_scraper.py --steps 1,2,3,4 --output barberias_espana.xlsx

# Solo OSM (rápido, ~2-3 min, datos legales)
python barber_scraper.py --steps 1 --output barberias_osm.xlsx

# OSM + Instagram, limitado a 500 registros
python barber_scraper.py --steps 1,3 --limit 500 --output leads_500.xlsx

# Continuar desde checkpoint (si se interrumpió)
python barber_scraper.py --steps 3,4 --input checkpoint.csv --output barberias_espana.xlsx
```

## Pasos

| Paso | Fuente | Datos obtenidos | Velocidad | Requiere key |
|------|--------|-----------------|-----------|--------------|
| 1 | OpenStreetMap / Overpass API | Nombre, ciudad, tel, email, web, lat/lon | ~2-3 min | No |
| 2 | Google Maps Places API o Bing/DDG | Nombre, tel, web, dirección | ~20-40 min | Opcional |
| 3 | Búsqueda web (Bing/DDG) | Handle Instagram | ~30-60 min | No |
| 4 | Scraping de webs | Email de contacto | ~20-40 min | No |

## Google Maps API (opcional — mejora drásticamente el paso 2)

```bash
# Windows PowerShell
$env:GOOGLE_MAPS_API_KEY = "tu-api-key-aquí"
python barber_scraper.py --steps 2 --output barberias.xlsx

# O en el mismo comando
set GOOGLE_MAPS_API_KEY=tu-api-key && python barber_scraper.py --steps 2
```

La key gratuita de Google Cloud (300$/mes crédito) es suficiente para 50 ciudades × ~20 queries = ~1000 llamadas.

## Salida Excel

Columnas: `nombre | ciudad | provincia | telefono | email | instagram | web | fuente | lat | lon | fecha`

- Cabecera con color azul oscuro
- Primera fila congelada
- Auto-filtro activado
- Ancho de columnas optimizado

## Checkpoint

El script guarda automáticamente un `checkpoint.csv` cada 100 registros y al final de cada paso. Si el proceso se interrumpe, puedes reanudar con:

```bash
python barber_scraper.py --steps 3,4 --input checkpoint.csv --output barberias.xlsx
```

## Fuentes de datos y legalidad

- **Paso 1 (OSM)**: OpenStreetMap, licencia ODbL. Legal para uso comercial con atribución.
- **Paso 2 (Bing/DDG)**: Scraping de resultados públicos de búsqueda. Sin autenticación.
- **Paso 3 (Instagram)**: Búsqueda de handles en índices de búsqueda públicos (no accede a Instagram directamente).
- **Paso 4 (Webs)**: Scraping de páginas de contacto públicas, estrictamente los campos de email visibles al usuario.

## Rendimiento estimado (sin API key)

- Paso 1: ~5.000-8.000 barberías en España
- Paso 2: +2.000-4.000 adicionales (50 ciudades × fallback)
- Con GOOGLE_MAPS_API_KEY: hasta +10.000 adicionales
- Total realista: 6.000-12.000 registros únicos

## Logs

El script genera `barber_scraper.log` con el detalle de cada operación.
