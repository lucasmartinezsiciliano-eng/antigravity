# youtube-intel — Skill de análisis YouTube para Centrum

> Cargada por: `centrum-intel` → sub-rol `youtube-analyst`
> Herramienta base: Hermes built-in `media/youtube-content` + WhisperX local (fallback)
> Coste: €0 ilimitado (vLLM local + youtube-transcript-api + WhisperX en DGX Spark)

---

## Cuándo activas esta skill

- Cron semanal: análisis de competidores YouTube (viernes junto al intel diario)
- Lucas o Mariano pasan una URL de YouTube directamente
- `trend-exploiter` detecta un vídeo relevante en el nicho
- `centrum` pide análisis de un canal concreto

---

## Pipeline de extracción (orden de preferencia)

```
1. youtube-transcript-api (subtítulos oficiales)   → < 5 segundos
2. yt-dlp --write-subs --skip-download              → subtítulos manuales/auto
3. WhisperX local (DGX Spark, puerto 8001 Nano)     → transcripción audio, sin límite
```

Para el paso 3 (WhisperX), el comando en terminal Hermes:
```bash
yt-dlp -x --audio-format wav -o /tmp/centrum-intel-yt/%(id)s.wav "<URL>"
whisperx /tmp/centrum-intel-yt/<id>.wav --model large-v3 --language es --output_dir /tmp/centrum-intel-yt/
```

---

## Análisis por tipo de solicitud

### A) Análisis de vídeo individual (Lucas/Mariano pasan URL)

```
ANÁLISIS YOUTUBE — <título del vídeo>
URL         : <url>
Canal       : <nombre> | <suscriptores>
Duración    : <min>
Visualiz.   : <N>

TRANSCRIPT COMPLETO (o resumen si > 30 min):
[...]

ÁNGULOS DE CONTENIDO DETECTADOS:
- Hook principal: <los primeros 15 segundos, literalmente>
- Estructura: <miedo / promesa / dato / historia / pregunta-respuesta>
- Frases clave del avatar: <citas literales del comentarista, no del presentador>

APLICABILIDAD A CENTRUM:
- ¿Contradice alguna de las 8 estrategias? <sí/no + cuál>
- ¿Ángulo reutilizable para Mariano? <sí/no + cómo>
- Objeciones nuevas detectadas en comentarios: <lista>
```

### B) Análisis de canal competidor (semanal automático)

Canales a monitorizar (actualizar en memoria si cambian):
- Buscar en YouTube: "hipoteca deuda España", "abogado hipoteca", "ejecución hipotecaria"
- Identificar los 3 canales con más crecimiento semanal
- Analizar sus 3 vídeos más recientes

```
INTEL YOUTUBE — semana <N>
─────────────────────────────────────
Canal 1: <nombre>
  Vídeos nuevos    : <N>
  Mejor rendimiento: <título> (<visualizaciones>)
  Ángulo principal : <una línea>
  Diferencial vs Centrum: <gap o amenaza>

Canal 2: [mismo formato]
Canal 3: [mismo formato]

Objeciones nuevas detectadas en comentarios esta semana:
- "<cita literal>" (Canal X, <N> likes)
- "<cita literal>" (Canal Y, <N> likes)

Ángulos sin cubrir por ningún canal (oportunidad para Mariano):
- <tema>
- <tema>
```

### C) Análisis de comentarios YouTube para avatar

Cuando `avatar-researcher` necesita lenguaje real del target:

- Extraer los 50 comentarios con más likes de vídeos sobre hipoteca/desahucio
- Filtrar: solo comentarios de personas con deuda real (no abogados ni asesores)
- Clasificar por emoción: miedo / rabia / confusión / esperanza / vergüenza
- Extraer frases literales para banco de frases Mariano

---

## Límites de esta skill

- **Vídeos privados o con DRM**: no accesibles. Documentar y saltar.
- **Canales sin subtítulos y > 60 min**: usar WhisperX, puede tardar. Priorizar audio corto.
- **Playlist > 20 vídeos**: procesar solo los 5 más recientes salvo instrucción contraria.
- **Nunca almacenar transcripciones completas en `observations/`** — solo el resumen + frases clave.

---

## Entrega a `centrum-intel`

El resultado de cada análisis va a:
```
~/.hermes/profiles/centrum-intel/observations/youtube-<YYYY-MM-DD>.md
```

Si hay frases nuevas del avatar → proponer actualización a `centrum/perfil-deudor` (Mariano confirma).
Si hay ángulo de contenido accionable → incluir en el `INTEL DAILY` con tag `[YOUTUBE]`.
