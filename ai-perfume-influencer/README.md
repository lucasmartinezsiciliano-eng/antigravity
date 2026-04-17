# AI Perfume Influencer

Sistema de automatización completo para un AI influencer de perfumes de nicho en Instagram.

---

## Estructura

```
ai-perfume-influencer/
├── engine/
│   ├── concept.js      → perfume → concepto 8-frame completo
│   ├── prompts.js      → concepto → prompts Higgsfield + Kling
│   ├── captions.js     → concepto → 5 variantes de caption deadpan
│   └── diversify.js    → historial → N ideas nuevas sin repetir
├── publish/
│   ├── instagram.js    → publica carrusel vía Instagram Graph API
│   └── tiktok.js       → publica video vía TikTok Content API
├── outreach/
│   ├── finder.js       → encuentra marcas candidatas
│   └── pitch.js        → genera email pitch personalizado
├── analytics/
│   └── tracker.js      → sincroniza métricas + genera informe
├── notion/
│   └── sync.js         → sincroniza todo con Notion
├── data/
│   ├── posts.json      → pipeline de posts (fuente de verdad local)
│   ├── perfumes.json   → catálogo de perfumes
│   └── brands.json     → CRM de marcas / outreach
├── logs/
├── .env.example        → variables de entorno necesarias
├── package.json
└── run.js              → CLI principal
```

---

## Setup

```bash
cd ai-perfume-influencer
npm install
cp .env.example .env
# Edita .env con tus keys
```

**Keys necesarias para empezar (mínimo):**
```
ANTHROPIC_API_KEY=sk-ant-...
```

El resto (Instagram, TikTok, Notion) son opcionales hasta que vayas a publicar.

---

## Flujo de trabajo completo

### 1. Generar concepto
```bash
node run concept \
  --perfume="Torino 21" \
  --brand="Xerjoff" \
  --notes="mint,lemon,basil,thyme,lavender,musk" \
  --price=320 \
  --mode=A \
  --moods="mojito,jardín mediterráneo,verano brutal"
```
→ Devuelve concepto con 8 frames + open-loop + caption seed. Guardado en `data/posts.json` con ID.

### 2. Generar prompts de imagen/video
```bash
node run prompts --id=001
```
→ Prompts listos para copiar en Higgsfield Nano Banana Pro (cada frame) + Kling AI (frame 1 animado).
→ Incluye seed sugerido para consistencia del avatar.

### 3. Generar captions
```bash
node run captions --id=001
```
→ 5 variantes deadpan Instagram + 2 para TikTok. La recomendada está marcada con ⭐.

### 4. [Producción manual]
Con los prompts generados:
- Higgsfield: https://higgsfield.ai → modelo Nano Banana Pro
- Kling AI: https://klingai.com → para el video/reel
- Capcut / Premiere para edición final

### 5. Publicar (Instagram)
```bash
# Las imágenes deben ser URLs públicas (súbelas a Cloudinary/Imgur primero)
node run publish instagram \
  --id=001 \
  --images="https://cdn.../f1.jpg,https://cdn.../f2.jpg,..." \
  --caption="too fresh."
```
→ Crea el carrusel como DRAFT. No publica automáticamente.

```bash
# Cuando estés listo para publicar:
node run publish confirm --id=001 --platform=instagram
```

### 6. Publicar (TikTok)
```bash
node run publish tiktok --id=001 --video="./output/reel_001.mp4"
# Y cuando estés listo:
node run publish confirm --id=001 --platform=tiktok
```

### 7. Métricas (24h después de publicar)
```bash
node run analytics sync      # Descarga métricas de IG
node run analytics report --period=week
```

### 8. Outreach
```bash
node run outreach find --limit=20      # Encuentra nuevas marcas
node run outreach pitch --brand=brand_001
```

### 9. Notion
```bash
node run notion sync      # Sincroniza todo a Notion
node run notion status    # Ver estado de sync
```

---

## Nuevas ideas (anti-repetición)
```bash
node run diversify --count=10
```
Analiza el historial y genera 10 ideas completamente distintas, ordenadas por potencial viral.

---

## Mejoras implementadas vs spec original

| Mejora | Impacto |
|--------|---------|
| **8 frames** (vs 6-7) | Sweet spot algoritmo IG 2026 — más swipe events = más distribución |
| **Open-loop technique** | Pregunta implícita frame 1, respuesta frame 5 → +swipe-through rate |
| **Seed locking** en prompts | Mismo seed en todos los frames → avatar consistente entre posts |
| **Fórmula 6-variable Nano Banana** | Subject+Composition+Action+Location+Style+Constraints |
| **Negative prompts explícitos** | Evita smiling, studio light, CGI por defecto |
| **Saves ponderados x3** | Métrica 2026: saves > comments > likes para engagement real |
| **Captions TikTok separadas** | 2 variantes específicas con más actitud para TikTok |
| **Draft-first siempre** | Nunca publica accidentalmente — confirmación explícita requerida |
| **Contact angle por marca** | Outreach personalizado por el perfil específico de cada casa |
| **Moods de comunidad Fragrantica** | Input opcional que enriquece el concepto con vocabulario real |

---

## Referencia de estilo: @kczco

El avatar sigue la estética de @kczco:
- **Sin sonreír nunca** — ni en concepto ni en prompts
- **Indiferencia total** al caos que la rodea
- **El frasco: siempre perfecto** aunque todo lo demás esté destruido
- **Caption deadpan**: 2-4 palabras, minúsculas, punto final
- **Fondo oscuro** o luz natural dura — nunca estudio, nunca blanco

Ejemplos de captions del estilo:
> "fishing time."
> "wasn't careful."
> "sorry i was hungry."
> "too hot here."

---

## Bases de datos Notion sugeridas

**Posts DB** (kanban por Estado):
`Título | Perfume | Modo | Estado | Dificultad | Caption | Precio | Likes | Saves | Engagement | Fecha publicación | Concepto | Invasor`

**Perfumes DB**:
`Nombre | Marca | Notas top | Notas base | Precio | Posts generados | Posts publicados | Fragrantica`

**Brands DB** (CRM outreach):
`Marca | Instagram | Precio aprox. | Seguidores IG | Estado | AI influencer | Email | Notas`

**Analytics DB**:
Auto-gestionada por `analytics/tracker.js`
