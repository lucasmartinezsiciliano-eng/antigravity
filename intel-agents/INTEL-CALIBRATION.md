# INTEL-CALIBRATION.md
# Archivo de calibración compartido — forge + horizon
# Actualizado automáticamente cada DOMINGO por calibrate.py

last_updated: 2026-05-21
version: 1.1-seed
calibrated_weeks: 0
total_signals_logged: 0
total_acted: 0

---

## PESOS DE FUENTES — FORGE

> Calculado como: señales accionadas / señales totales de esa fuente (últimas 4 semanas)
> Semilla inicial basada en conocimiento del ecosistema. Se actualiza con datos reales cada domingo.

| Fuente | Peso inicial | Datos reales | Notas |
|--------|-------------|--------------|-------|
| r/LocalLLaMA | 0.85 | pending | Comunidad técnica real, señales OSS con benchmarks |
| Ollama releases (GitHub) | 0.90 | pending | Impacto directo en stack local |
| Hugging Face trending | 0.85 | pending | Alta densidad de modelos nuevos relevantes |
| GitHub trending | 0.80 | pending | Alta ratio señal útil vs ruido |
| r/AITools | 0.80 | pending | Herramientas nuevas con usuarios reales |
| r/artificial | 0.65 | pending | Mix amplio, filtrar por upvotes y comentarios |
| Hacker News (Show/Ask) | 0.70 | pending | Alta calidad, proyectos con tracción real |
| Twitter/X (cuentas técnicas) | 0.55 | pending | @karpathy, @simonw, @reach_vb — señal antes que en otros sitios |
| TikTok/YouTube meta (Reddit) | 0.50 | pending | Captura viral tech — señal más lenta pero valida adopción masiva |
| Papers With Code | 0.35 | pending | Benchmarks útiles pero pocas releases prácticas inmediatas |
| TechCrunch AI | 0.20 | pending | Noticias tardías, bajo impacto en stack OSS |

---

## PESOS DE FUENTES — HORIZON

| Fuente | Peso inicial | Datos reales | Notas |
|--------|-------------|--------------|-------|
| r/Entrepreneur (con revenue) | 0.85 | pending | "I make €X/month" — validación real |
| r/SideProject + r/AIBusinessIdeas | 0.80 | pending | Proyectos con tracción + discusión de monetización |
| Indie Hackers (con revenue) | 0.85 | pending | Fuente más fiable: ingresos verificados públicamente |
| Hacker News Ask/Show HN | 0.75 | pending | Alta calidad, discusión real con métricas |
| TikTok meta (Reddit) | 0.70 | pending | "how I make money with AI" viral — señal de demanda real |
| YouTube meta (títulos) | 0.65 | pending | "I built AI business €X/month" — valida que es replicable |
| Product Hunt | 0.65 | pending | Lanzamientos reales, tracción inicial visible |
| Twitter/X revenue reports | 0.60 | pending | MRR reports, "$X ARR" — alta señal si hay datos |
| El Confidencial / Expansión | 0.70 | pending | Proptech y fintech español — muy relevante para Centrum/Broker |
| EU-Startups | 0.60 | pending | Contexto europeo, funding = tracción validada |
| TechCrunch | 0.45 | pending | Noticias tardías pero confirma tracción |

---

## PERFIL DE GUSTO DE LUCAS — FORGE

> Semilla inicial desde contexto conocido del proyecto. Se actualiza con feedback real.

### ACTÚA SIEMPRE (peso 1.0)
- **Sustitución OSS de servicio de pago con ahorro > €15/mes** — patrón confirmado múltiples veces: Chatterbox vs ElevenLabs, Pipecat vs Retell, Whisper vs Deepgram
- **Nuevo modelo local que supera al tier actual en benchmark** — Lucas actualiza modelos regularmente
- **CVE crítico en herramienta del stack** — siempre requiere acción, va siempre en informe
- **Workflow o método que multiplica productividad** — Lucas opera solo, cualquier multiplicador es valioso

### ACTÚA CON ALTA PROBABILIDAD (peso 0.75)
- **Nuevo modelo Ollama con mejor rendimiento que el tier actual** para agentes específicos
- **Herramienta que elimina una tarea manual recurrente** (especialmente en e-commerce o broker)
- **Método viral de trabajo con IA** que la comunidad está usando (Reddit/TikTok fuente)
- **Alternativa a Claude API** con calidad similar para reducir coste cloud

### ACTÚA OCASIONALMENTE (peso 0.45)
- **Nueva herramienta de generación de vídeo/imagen** con mejor calidad para contenido
- **Herramienta de infraestructura** (monitoring, logging) no urgente
- **Benchmark de modelo** sin release disponible aún — Lucas lo marca para seguimiento

### IGNORA CONSISTENTEMENTE (peso 0.05 — no incluir)
- Papers académicos sin release o demo funcional
- Herramientas enterprise > €200/mes
- Tecnología que no tiene soporte en hardware de Lucas y no tiene alternativa cloud asequible
- Updates de patch version sin cambio de funcionalidad relevante
- Hype sin datos (cualquier "revolucionario" sin demo o benchmarks)

---

## PERFIL DE GUSTO DE LUCAS — HORIZON

### ACTÚA SIEMPRE (peso 1.0)
- **Negocio IA de 1 persona con revenue confirmado (€2k+/mes) y modelo replicable** — el patrón más valioso
- **Oportunidad directa para Centrum** con modelo de negocio claro y urgencia
- **Competidor directo de Centrum** con tracción real — siempre incluir con flag AMENAZA
- **Estrategia de captación que otro broker/proptech está usando con éxito demostrado**

### ACTÚA CON ALTA PROBABILIDAD (peso 0.75)
- **Modelo de negocio AI-native** que Lucas puede montar en ≤4 semanas con sus capacidades
- **Nueva categoría TikTok Shop** con demanda creciente que encaja con proveedor DDP
- **Servicio IA para pymes españolas** donde Lucas tiene ventaja por su stack
- **Proptech/fintech español** que valide o amenace el mercado de Centrum o Broker

### ACTÚA OCASIONALMENTE (peso 0.45)
- **Mercados nuevos** que requieran <€1.000 y 1 semana de validación
- **Modelos de afiliación** en sectores con acceso natural (hipotecas, seguros)
- **Tendencias de contenido** que cambien la estrategia de distribución

### IGNORA CONSISTENTEMENTE (peso 0.05 — no incluir)
- Ideas sin ningún dato de validación (ni revenue, ni usuarios, ni crecimiento)
- Negocios que requieran equipo > 2 personas para operar
- Mercados fuera de España/Europa para negocios no-digitales
- B2B enterprise con ciclos > 3 meses sin cashflow temprano
- Oportunidades con capex inicial > €5.000 sin fase de validación previa

---

## ANTI-PATRONES CONFIRMADOS

> Señales que han sido ignoradas consistentemente. Actualiza cada domingo.
> Formato: [semana] [agente]: tipo de señal → razón del descarte

```
[semana 0 — seed]
- forge: papers sin release → Lucas no actúa en investigación sin producto
- forge: herramientas enterprise caras → fuera del rango de precio aceptable
- horizon: negocios USA-only → Lucas foca en España/Europa
- horizon: ideas sin datos → no hay validación que justifique tiempo de análisis
```

---

## SINERGIAS FORGE ↔ HORIZON

> Horizon debe leer la salida de forge antes de ejecutar.
> Patrones detectados donde una señal técnica habilita una oportunidad de negocio.

```
PATRONES SEED (conocimiento previo):
- Nuevo TTS local gratuito (forge) → habilita clonar voces para servicios de contenido IA (horizon)
- Modelo local que iguala Claude Haiku (forge) → reduce coste de agentes → mejora margen de SaaS IA (horizon)
- Herramienta de scraping más potente (forge) → permite lead gen hipotecario automatizado (horizon: Centrum)
- Modelo multimodal nuevo gratuito (forge) → habilita análisis facial VISAI más barato (horizon)
- Framework de agentes nuevo (forge) → puede habilitar nuevo producto de "agentes IA para pymes" (horizon)

PATRONES APRENDIDOS: [vacío — se rellenará con datos reales]
```

---

## CONTEXTO FIJO DEL NEGOCIO (no cambia con calibración)

```
Prioridades de negocio de Lucas (orden de importancia para filtrar):
1. Centrum de la Vivienda — el proyecto más grande y más urgente
2. E-commerce TikTok Shop — ingresos activos, escalar sin carga operativa
3. Broker Firmax — digitalización y captación de leads
4. Nuevas oportunidades — siempre bienvenidas si son ejecutables con stack actual

Stack que cuesta dinero y es objetivo prioritario de sustitución OSS:
1. ElevenLabs (TTS) — objetivo prioritario
2. Retell AI (call IA) — en evaluación activa
3. Creatomate (render vídeo) — objetivo secundario
4. Claude API en agentes no críticos — reducir donde haiku sea suficiente
```

---

## HISTORIAL DE CALIBRACIÓN

| Semana | Fecha | Forge actuadas/total | Horizon actuadas/total | Ratio global | Cambios clave |
|--------|-------|---------------------|----------------------|-------------|---------------|
| seed | 2026-05-21 | 0/0 | 0/0 | — | Valores iniciales + scope ampliado (Reddit/TikTok/nuevos modelos negocio IA) |
