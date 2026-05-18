# VISAI Load Testing — Locust

Simula usuarios reales haciendo análisis, consultando dashboards de barbero
y navegando el leaderboard. Detecta errores, cuellos de botella y crashes.

---

## Setup (1 vez)

```bash
# Desde cualquier carpeta (instala globalmente en el entorno Python)
pip install locust pillow
```

---

## Modos de prueba

### 1. Smoke test — verifica que Railway responde (30 seg, sin UI)

```bash
bash stylescan/tests/load/run.sh smoke https://TU-BACKEND.up.railway.app
```

Usa esto después de cada deploy. Si falla, Railway no arrancó bien.

---

### 2. Test de lectura — seguro en producción

```bash
bash stylescan/tests/load/run.sh read https://TU-BACKEND.up.railway.app
```

50 usuarios leyendo leaderboard, dashboards, resultados.
**No crea registros, no gasta dinero.** Abre `http://localhost:8089` para ver métricas en vivo.

---

### 3. Test de flujo completo (requiere configuración Railway)

**Paso previo:** En Railway, añade la variable de entorno `DEV_SKIP_PAYMENT=True`.
Esto hace que `POST /analysis/initiate` no llame a Stripe y marque el análisis como pagado directamente.

```bash
bash stylescan/tests/load/run.sh flow https://TU-BACKEND.up.railway.app
```

20 usuarios haciendo: quiz → initiate → consent → poll.
**No llama al LLM** (se detiene antes de subir fotos).

---

### 4. Test con fotos y LLM (gasta créditos — úsalo con cuidado)

```bash
bash stylescan/tests/load/run.sh flow-with-photos https://TU-BACKEND.up.railway.app
```

5 usuarios subiendo fotos reales → Claude procesa → resultado.
Cada análisis gasta ~$0.01-0.05 en Claude API.

---

### 5. Stress test — 100 usuarios mixtos

```bash
bash stylescan/tests/load/run.sh stress https://TU-BACKEND.up.railway.app
```

Mezcla de los tres tipos de usuario. Lleva Railway al límite.

---

## Interfaz web de Locust

Cuando el modo tiene UI (todos excepto `smoke` y `headless`), abre:

```
http://localhost:8089
```

Desde ahí puedes:
- Ver requests/seg, latencia, errores en tiempo real
- Ajustar número de usuarios mientras corre
- Descargar CSV con resultados

---

## Qué mirar durante el test

| Métrica | OK | Warning | Crítico |
|---------|-----|---------|---------|
| Tasa de error | < 1% | 1-5% | > 5% |
| Latencia P95 `/initiate` | < 500ms | 500ms-2s | > 2s |
| Latencia P95 `/photos` | < 30s | 30-90s | > 90s (timeout) |
| Latencia P95 `/leaderboard` | < 200ms | 200-500ms | > 500ms |
| Errores 502 | 0 | - | Cualquiera |
| Errores 500 | 0 | - | Cualquiera |
| Errores 429 | Esperado | - | - |

---

## Variables de entorno opcionales

Puedes fijar IDs de registros existentes para que las tareas de lectura
siempre tengan datos:

```bash
# En Windows (PowerShell)
$env:SEED_BARBER_ID   = "el-uuid-del-barbero"
$env:SEED_ANALYSIS_ID = "el-uuid-del-analisis-completado"

# En bash/macOS
export SEED_BARBER_ID="el-uuid-del-barbero"
export SEED_ANALYSIS_ID="el-uuid-del-analisis-completado"

locust -f stylescan/tests/load/locustfile.py --host https://TU-BACKEND.up.railway.app
```

---

## Limpiar datos de test de Railway

Los barberos y análisis creados durante el test quedan en la DB.
Para limpiarlos:

```sql
-- En la consola de Railway → base de datos (si migras a Postgres)
DELETE FROM barber_partners WHERE email LIKE '%loadtest%';
DELETE FROM analyses WHERE created_at > NOW() - INTERVAL '2 hours';
```

Si aún usas SQLite local, simplemente no hay que hacer nada —
los datos de test son inofensivos en desarrollo.

---

## Arquitectura de los tests

```
locustfile.py
│
├── ReadOnlyUser (weight=3)
│   ├── GET /leaderboard        (all_time, week, city)
│   ├── GET /barbers/{id}/dashboard
│   ├── GET /leaderboard/stats/{id}
│   ├── GET /analysis/{id}
│   └── GET /analysis/{id}/visuals
│
├── AnalysisFlowUser (weight=2)
│   ├── POST /analysis/initiate
│   ├── POST /analysis/{id}/consent
│   ├── [POST /analysis/{id}/photos — solo si INCLUDE_PHOTO_UPLOAD=true]
│   └── GET  /analysis/{id}
│
└── BarberUser (weight=1)
    ├── POST /barbers/register
    ├── GET  /barbers/{id}/dashboard
    ├── GET  /leaderboard/stats/{id}
    └── POST /barbers/{id}/sign-contract
```
