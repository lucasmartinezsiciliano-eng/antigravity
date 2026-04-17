# AI Perfume Influencer — Sistema de Automatización
> Instrucciones para Claude Code. Lee esto entero antes de escribir una sola línea de código.

---

## Qué es este proyecto

Gestionamos un AI influencer de perfumes de nicho en Instagram y TikTok.
El avatar y las imágenes se generan manualmente en Higgsfield (Soul 2.0 + Nano Banana).
La animación se genera manualmente en Kling AI.
Este sistema automatiza todo lo demás: conceptos, prompts, captions, publicación, outreach y analytics.

---

## La fórmula de contenido (NUNCA modificar esta lógica)

Basada en el análisis exhaustivo del perfil @kczco en Instagram.

### Los 3 modos de post

**Modo A — Invasión física**
Algo mundano y físico destruye/invade el contexto lujoso donde está el frasco.
El frasco siempre perfecto. Ella indiferente. Ej: menta aplastada por toda la barra de mármol.

**Modo B — Colisión de contexto**
El frasco en un entorno donde no debería existir. Los elementos locales interactúan solos.
Ej: frasco de perfume de 300 euros en un mercado de especias en Marrakech.

**Modo C — Declaración de amor**
Sin caos. Solo actitud pura. Devoción absurda al objeto. Humor seco.
Ej: "i love my torino more than summer" escrito en la condensación de un vaso.

### Reglas de oro del contenido

- El frasco: siempre perfecto aunque todo alrededor esté en caos
- Ella: siempre seria, sin sonreír, sin posar, haciendo algo
- El elemento invasor: siempre físico y tangible, nunca abstracto
- La narrativa: siempre conectada con las notas olfativas del perfume (la escena huele al producto)
- El fondo: siempre oscuro o luz natural dura, nunca estudio, nunca blanco
- Caption: 2-4 palabras deadpan, nunca menciona el perfume, tag final: kcz + @marca

### Estructura del carrusel (6-7 frames)

- Frame 1: Hook — situación completa, ella + frasco + el caos
- Frames 2-4: Detalles del daño o del contexto. Close-ups.
- Frame 5-6: Reacciones de terceros (personas, animales, elementos)
- Frame final: Punch line WTF. El detalle más absurdo e inesperado.

---

## Stack técnico

| Herramienta | Uso | Quién lo ejecuta |
|---|---|---|
| Higgsfield Soul 2.0 | Crear y mantener el avatar consistente | Usuario manualmente |
| Higgsfield Nano Banana | Generar las escenas con el avatar | Usuario manualmente |
| Kling AI | Animar el frame principal para Reels/TikTok | Usuario manualmente |
| Claude API (claude-sonnet-4-20250514) | Generar conceptos, prompts, captions, outreach | Automatizado |
| Instagram Graph API | Publicar carruseles | Automatizado (con confirmación) |
| TikTok Content Posting API | Publicar videos | Automatizado (con confirmación) |
| Notion API | Base de datos central del proyecto | Automatizado |
| Gmail API | Outreach a marcas | Automatizado (borrador para revisión) |

---

## Arquitectura del proyecto

```
ai-perfume-influencer/
├── CLAUDE.md
├── .env
├── .env.example
├── package.json
├── run.js                     <- CLI principal
├── engine/
│   ├── concept.js             <- perfume -> concepto completo con frames
│   ├── prompts.js             <- concepto -> prompts para Higgsfield y Kling
│   ├── captions.js            <- concepto -> 5 variantes de caption
│   └── diversify.js           <- genera 10 nuevas ideas de posts
├── publish/
│   ├── instagram.js           <- publica carrusel via Graph API
│   └── tiktok.js              <- publica video via TikTok API
├── outreach/
│   ├── finder.js              <- encuentra marcas de nicho candidatas
│   └── pitch.js               <- genera pitch personalizado por marca
├── analytics/
│   └── tracker.js             <- recoge métricas y las manda a Notion
├── notion/
│   └── sync.js                <- sincroniza todo con las BBDDs de Notion
├── data/
│   ├── perfumes.json          <- base de datos de perfumes trabajados
│   ├── brands.json            <- marcas objetivo con estado de outreach
│   └── posts.json             <- historial de posts generados y publicados
└── logs/                      <- logs con timestamp de todas las operaciones
```

---

## Variables de entorno (.env)

```
ANTHROPIC_API_KEY=
INSTAGRAM_ACCESS_TOKEN=
INSTAGRAM_BUSINESS_ACCOUNT_ID=
TIKTOK_ACCESS_TOKEN=
TIKTOK_OPEN_ID=
NOTION_API_KEY=
NOTION_POSTS_DB_ID=
NOTION_PERFUMES_DB_ID=
NOTION_BRANDS_DB_ID=
NOTION_ANALYTICS_DB_ID=
GMAIL_USER=
GMAIL_APP_PASSWORD=
```

---

## Módulos — especificación completa

### engine/concept.js

Input:
```json
{
  "perfume": "Torino 21",
  "brand": "Xerjoff",
  "notes": ["mint", "citrus", "mojito", "green", "fresh"],
  "price": 320,
  "mode": "A"
}
```

Proceso:
Llama a Claude API con el sistema de contenido completo.
Genera un concepto donde el elemento invasor está directamente inspirado en las notas olfativas.
La escena tiene que oler al perfume — eso es lo que la hace única.

Output:
```json
{
  "id": "001",
  "perfume": "Torino 21",
  "brand": "Xerjoff",
  "mode": "A",
  "title": "too fresh.",
  "concept_summary": "Descripción de la idea en 2-3 frases",
  "frames": [
    { "number": 1, "description": "descripción detallada del frame" },
    { "number": 2, "description": "..." }
  ],
  "caption_seed": "too fresh.",
  "created_at": "timestamp"
}
```

Guarda en data/posts.json y sincroniza con Notion Posts DB.

---

### engine/prompts.js

Input: concept_id

Proceso:
Por cada frame genera un prompt para Higgsfield Nano Banana.
Para el frame 1 genera también el prompt para Kling AI.

Los prompts de Higgsfield deben incluir siempre:
- Estilo fotorrealista, no CGI, film grain
- Iluminación nocturna o luz natural dura
- Descripción exacta de la posición del frasco
- Actitud del personaje: seria, mirada directa a cámara, indiferente al caos
- El elemento invasor y cómo interactúa con el espacio
- Mood: oscuro, contrastes fuertes, fotografía de moda editorial

Los prompts de Kling AI deben incluir:
- Movimiento sutil y específico del elemento invasor
- Duración sugerida: 15-30 segundos
- Cámara: estática o movimiento muy lento cinematográfico
- Sin audio (se añade en edición)

Output:
```json
{
  "concept_id": "001",
  "higgsfield_prompts": [
    { "frame": 1, "prompt": "prompt completo listo para pegar" },
    { "frame": 2, "prompt": "..." }
  ],
  "kling_prompt": {
    "frame": 1,
    "prompt": "prompt completo para animar este frame"
  }
}
```

Imprime todos los prompts en consola de forma clara y numerada para que el usuario los copie.

---

### engine/captions.js

Input: concept_id

Genera 5 variantes de caption con estas reglas estrictas:
- 2-4 palabras máximo
- Deadpan — nunca explica, nunca exagera
- No menciona el perfume nunca
- Siempre en minúsculas con punto al final
- Estilo: "fishing time." / "i love my chickens." / "sorry i was hungry." / "too hot here."
- Tag fijo al final: kcz + @[instagram_marca]

Output:
```json
{
  "concept_id": "001",
  "captions": [
    "too fresh.\nkcz + @xerjoff",
    "mint accident.\nkcz + @xerjoff",
    "wasn't careful.\nkcz + @xerjoff",
    "it happens.\nkcz + @xerjoff",
    "smells better now.\nkcz + @xerjoff"
  ]
}
```

---

### engine/diversify.js

Input: historial de posts (posts.json)

Analiza qué perfumes, modos, localizaciones y elementos invasores ya se han usado.
Genera 10 nuevas ideas completamente distintas evitando repetir combinaciones.
Perfumes de distintas casas, distintos modos, distintas partes del mundo.

Output por idea:
- Perfume sugerido + casa + notas principales
- Modo (A, B o C)
- Localización
- Elemento invasor
- Por qué conecta con el perfume
- Nivel de dificultad visual (fácil/medio/difícil)

---

### publish/instagram.js

Input:
```json
{
  "concept_id": "001",
  "images": ["path/frame1.jpg", "path/frame2.jpg"],
  "caption": "too fresh.\nkcz + @xerjoff",
  "draft": true
}
```

- Si draft: true — guarda en Notion con estado "listo para publicar", NO publica
- Si draft: false — pide confirmación en CLI, luego publica via Instagram Graph API
- Guarda post_id, permalink y timestamp en posts.json y Notion
- NUNCA publicar sin confirmación explícita del usuario

---

### publish/tiktok.js

Input:
```json
{
  "concept_id": "001",
  "video": "path/video.mp4",
  "caption": "too fresh. #perfume #xerjoff #niche",
  "draft": true
}
```

Mismo comportamiento que instagram.js — draft por defecto, confirmación obligatoria.

---

### outreach/finder.js

Busca marcas de perfumes de nicho.
Criterios: precio mayor de 100 euros, estética premium, presencia en Instagram.

Marcas objetivo ya en data/brands.json:
Xerjoff, Maison Margiela Replica, Initio, Memo Paris, Creed, Byredo,
Kilian Paris, Juliette Has a Gun, Nishane, Morph, Zoologist, Orto Parisi.

Output por marca:
```json
{
  "id": "brand_001",
  "name": "Xerjoff",
  "instagram": "@xerjoff",
  "email": "pr@xerjoff.com",
  "price_range": "200-500",
  "followers_ig": 180000,
  "has_ai_influencer": false,
  "status": "pending",
  "notes": ""
}
```

---

### outreach/pitch.js

Input: brand_id + métricas actuales del perfil

Genera pitch personalizado para esa marca específica.
Menciona posts relacionados con el perfil olfativo de esa marca.
Tono profesional y directo. Máximo 150 palabras.
Genera BORRADOR — nunca envía automáticamente.
Guarda en Notion con estado "borrador" e imprime en consola para revisión.

---

### analytics/tracker.js

Ejecutar cada 24h via cron.
Recoge métricas de cada post: likes, comments, shares, saves, reach, impressions.
Calcula engagement rate: (likes + comments + saves) / reach * 100.
Actualiza Notion Analytics DB.
Genera resumen semanal cada lunes.

Alerta en consola si:
- Post supera 1000 saves: "POST VIRAL: [título] — considera hacer parte 2"
- Engagement rate cae bajo 3% dos semanas seguidas: "Revisar estrategia de contenido"

---

### notion/sync.js

4 bases de datos:

Posts DB: ID, Perfume, Marca, Modo, Concepto, Caption, Estado, Fecha, Likes, Comments, Saves, Reach, Engagement Rate, Link

Perfumes DB: Nombre, Casa, Notas, Precio, Posts generados, Posts publicados, URL afiliado

Brands DB: Marca, Instagram, Email, Price range, Followers, Estado outreach, Fecha contacto, Notas

Analytics DB: Fecha, Total posts, Seguidores IG, Seguidores TikTok, Engagement rate medio, Post top saves, Post top likes

---

## run.js — CLI principal

```bash
# Generar concepto
node run concept --perfume="Torino 21" --brand="Xerjoff" --notes="mint,citrus,mojito" --price=320 --mode=A

# Generar prompts
node run prompts --id=001

# Generar captions
node run captions --id=001

# Generar nuevas ideas
node run diversify --count=10

# Publicar en draft
node run publish instagram --id=001 --images="f1.jpg,f2.jpg,f3.jpg" --caption="too fresh."
node run publish tiktok --id=001 --video="reel.mp4"

# Confirmar publicación
node run publish confirm --id=001 --platform=instagram

# Outreach
node run outreach find --limit=20
node run outreach pitch --brand=brand_001

# Analytics
node run analytics sync
node run analytics report --period=week

# Notion
node run notion sync
node run notion status
```

---

## Reglas de código

1. Guardar estado local antes de cualquier llamada a API externa
2. Draft por defecto en todo lo que publica — nunca publicar sin confirmación
3. Logs en /logs/YYYY-MM-DD.log con timestamp en cada operación
4. API keys solo en .env — nunca en código
5. Cada módulo funciona de forma independiente y como parte del pipeline
6. Errores claros — si falta variable de entorno, decir exactamente cuál
7. data/*.json como fuente de verdad local — Notion es el espejo
8. Node.js con ES modules (type: module en package.json)
9. Dependencias mínimas: anthropic, @notionhq/client, axios, dotenv, commander

---

## Orden de construcción

1. package.json y estructura de carpetas
2. .env.example con todas las variables
3. engine/concept.js
4. engine/prompts.js
5. engine/captions.js
6. run.js con comandos concept, prompts y captions
7. Testear con: node run concept --perfume="Torino 21" --brand="Xerjoff" --notes="mint,citrus,mojito" --price=320 --mode=A
8. notion/sync.js
9. engine/diversify.js
10. publish/instagram.js y publish/tiktok.js
11. outreach/finder.js y outreach/pitch.js
12. analytics/tracker.js con cron diario

No avanzar al siguiente paso hasta que el anterior funcione y esté testeado.

---

## Test de validación final

```bash
node run concept --perfume="Torino 21" --brand="Xerjoff" --notes="mint,citrus,mojito" --price=320 --mode=A
node run prompts --id=001
node run captions --id=001
node run diversify --count=5
node run notion sync
```

Resultado esperado:
- Concepto con 7 frames en data/posts.json y Notion
- 7 prompts de Higgsfield + 1 prompt de Kling AI impresos en consola
- 5 variantes de caption impresas en consola
- 5 nuevas ideas en consola
- Todo sincronizado en Notion
