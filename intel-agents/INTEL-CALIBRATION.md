# INTEL-CALIBRATION.md
# Archivo de calibración compartido — forge + horizon
# Actualizado automáticamente cada DOMINGO por los agentes

last_updated: 2026-05-21
version: 1.0-seed
calibrated_weeks: 0
total_signals_logged: 0
total_acted: 0

---

## PESOS DE FUENTES — FORGE

> Calculado como: señales accionadas / señales totales de esa fuente (últimas 4 semanas)
> Semilla inicial basada en conocimiento del ecosistema. Se actualiza con datos reales.

| Fuente | Peso inicial | Datos reales | Notas |
|--------|-------------|--------------|-------|
| Hugging Face trending | 0.85 | pending | Alta densidad de modelos nuevos relevantes |
| GitHub trending | 0.80 | pending | Alta ratio señal útil vs ruido |
| r/LocalLLaMA | 0.75 | pending | Comunidad técnica, mucho contexto de DGX/Ollama |
| Ollama releases | 0.90 | pending | Impacto directo en stack local de Lucas |
| OpenClaw changelog | 0.95 | pending | Impacto directo en motor de agentes |
| Hacker News | 0.55 | pending | Mucho volumen, ratio señal menor |
| Papers With Code | 0.40 | pending | Benchmarks útiles pero pocas releases prácticas |
| Twitter/X | 0.30 | pending | Alto ruido, bajo ratio señal |
| TechCrunch AI | 0.25 | pending | Noticias tarde, pocas OSS |

---

## PESOS DE FUENTES — HORIZON

| Fuente | Peso inicial | Datos reales | Notas |
|--------|-------------|--------------|-------|
| Indie Hackers (con revenue) | 0.85 | pending | Negocios validados con datos reales |
| Product Hunt | 0.70 | pending | Lanzamientos reales, tracción inicial visible |
| Hacker News Ask/Show | 0.75 | pending | Alta calidad, discusión con métricas reales |
| r/Entrepreneur | 0.60 | pending | Mezcla de calidad, filtrar por upvotes |
| EU-Startups | 0.65 | pending | Contexto europeo relevante |
| TechCrunch | 0.50 | pending | Noticias tardías pero valida tracción |
| El Confidencial / Expansión | 0.70 | pending | Proptech y fintech español — muy relevante para Centrum/Broker |
| LinkedIn España | 0.35 | pending | Mucho ruido, pocos datos duros |

---

## PERFIL DE GUSTO DE LUCAS — FORGE

> Lo que Lucas actúa vs lo que ignora. Semilla inicial desde contexto conocido.
> Se actualiza con feedback real semana a semana.

### ACTÚA SIEMPRE (peso 1.0)
- **Sustitución OSS de servicio de pago con ahorro > €20/mes** — patrón confirmado: Chatterbox vs ElevenLabs, Pipecat vs Retell, Whisper vs Deepgram
- **Nuevo modelo Ollama con benchmark mejor que el tier actual** — Lucas actualiza modelos con regularidad
- **Alerta de seguridad crítica (CVE alto)** en cualquier herramienta del stack — siempre requiere acción

### ACTÚA CON ALTA PROBABILIDAD (peso 0.75)
- **Upgrade de OpenClaw con nueva feature** que cambia cómo funcionan los agentes
- **Nuevo MCP útil** para capacidades que los agentes no tienen hoy (especialmente browser, calendar, comms)
- **Modelo que sustituya Claude Sonnet local** con calidad similar — objetivo de reducción de coste cloud
- **Herramienta de vídeo/imagen open source** que mejore pipeline de contenido Centrum

### ACTÚA OCASIONALMENTE (peso 0.45)
- **Benchmark de modelo nuevo** sin release disponible aún — Lucas lo marca para seguimiento
- **Herramienta de infraestructura** (monitoring, logging) que no sea urgente
- **Alternativa a Oracle Cloud** — interesante pero cambio tiene fricción alta

### IGNORA (peso 0.10 — no incluir salvo datos muy sólidos)
- Papers académicos sin release asociado
- Herramientas enterprise > €200/mes
- Tecnología que no corre en DGX 128GB ni en hardware local
- Updates menores (patch versions) sin cambio de funcionalidad

---

## PERFIL DE GUSTO DE LUCAS — HORIZON

### ACTÚA SIEMPRE (peso 1.0)
- **Oportunidad directa para Centrum** con modelo de negocio claro — Lucas está muy enfocado aquí
- **Estrategia de captación digital** que otro broker está usando con éxito demostrado
- **Competidor directo de Centrum** con tracción — necesita saber para calibrar estrategia

### ACTÚA CON ALTA PROBABILIDAD (peso 0.75)
- **Modelo de e-commerce 1-persona con agentes IA** que genera €5k+/mes — transferible directamente
- **Nueva categoría TikTok Shop** que está creciendo y encaja con el proveedor DDP actual
- **Proptech / fintech español** lanzando algo que valide o amenace el mercado Centrum
- **Oportunidad de "IA-as-a-service"** donde Lucas podría vender su expertise en agentes

### ACTÚA OCASIONALMENTE (peso 0.45)
- **Mercados nuevos** que requieran <€1.000 de inversión y 1 semana de validación
- **Modelos de afiliación** en sectores donde Lucas tiene acceso (hipotecas, seguros)
- **Tendencias de contenido** que cambien la estrategia de distribución del broker

### IGNORA (peso 0.10 — no incluir)
- Oportunidades en mercados fuera de España (salvo que sea online puro y escalable)
- Negocios que requieran equipo > 2 personas
- B2B enterprise con ciclos de venta > 6 meses
- Ideas sin ninguna validación de mercado

---

## ANTI-PATRONES CONFIRMADOS

> Señales que se han incluido antes pero que Lucas ignoró consistentemente.
> Actualizar aquí para no repetir el error.

```
[Semana 1+] — A COMPLETAR CON DATOS REALES
Ejemplo de formato:
- [fecha] forge: "Paper sobre nuevo modelo 40B" → ignorado × 3 veces → no incluir papers sin release
- [fecha] horizon: "Startup USA con AI mortgage" → ignorado → Lucas no actúa en mercados USA
```

---

## SINERGIAS FORGE ↔ HORIZON

> Patrones donde una señal técnica de forge habilita una oportunidad de horizon.
> El sistema aprende a conectar ambos streams.

```
PATRÓN SEMILLA (seed knowledge):
- Mejora en TTS local (forge) → habilita clonar voz de asesores financieros (horizon: Centrum)
- Nuevo modelo ligero para tool use (forge) → reduce coste de agentes Centrum (horizon: margen)
- Herramienta de scraping más potente (forge) → permite monitorizar leads hipotecarios online (horizon)

PATRONES APRENDIDOS (se actualizan con datos):
[vacío — se rellenará en semanas siguientes]
```

---

## HISTORIAL DE CALIBRACIÓN

| Semana | Fecha | Forge: actuadas/total | Horizon: actuadas/total | Cambios en pesos |
|--------|-------|----------------------|------------------------|-----------------|
| seed | 2026-05-21 | 0/0 | 0/0 | Valores iniciales |

---

## INSTRUCCIONES PARA LA CALIBRACIÓN DOMINICAL

Cada domingo, el agente que ejecuta primero la calibración debe:

1. Leer INTEL-FEEDBACK-LOG.md completo de la semana
2. Para cada señal de forge: buscar la reacción de Lucas (👍/👎/comentario)
3. Para cada señal de horizon: idem
4. Calcular nuevos pesos por fuente: `señales_actuadas / señales_totales`
5. Actualizar tabla de pesos con datos reales (mantener histórico, no borrar)
6. Si hay ≥3 ignorados del mismo tipo → añadir a ANTI-PATRONES
7. Si hay ≥2 actuados del mismo tipo nuevo → añadir a ACTÚA SIEMPRE / ALTA PROBABILIDAD
8. Actualizar `last_updated`, `calibrated_weeks`, counters
9. Escribir resumen en INTEL-FEEDBACK-LOG.md: "CALIBRACIÓN SEMANA X completada"
