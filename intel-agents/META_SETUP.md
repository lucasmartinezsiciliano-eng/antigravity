# META_SETUP.md — Configurar Meta Graph API para Intel Agents

Con esto los agentes pueden leer hashtags de Instagram en tiempo real y acceder a datos de cuentas business. Sin esto, usan scrapers + búsquedas web (funcional pero con menos detalle).

---

## Qué consigues con la API oficial

| Sin API (ahora) | Con Meta Graph API |
|---|---|
| Scrapers de terceros (picuki, imginn) — pueden fallar | Datos directos de Instagram — siempre disponible |
| 5-10 posts por búsqueda | Hasta 50 posts recientes por hashtag |
| Solo texto visible | Engagement real: likes, comentarios, tipo de media |
| Búsquedas cruzadas aproximadas | Búsqueda de hashtags: #iatools, #negocioIA, etc. |
| Sin trending | Top media de hashtag por engagement |

---

## Tiempo de setup: ~30 minutos

---

## Paso 1 — Preparar tu cuenta Instagram

Tu cuenta de Instagram debe ser **Business** o **Creator** (no personal).

1. Abre Instagram → Ajustes → Cuenta → Cambiar a cuenta profesional
2. Elige "Creador" o "Empresa"
3. Conecta con una página de Facebook (si no tienes una, créala en facebook.com/pages/create)

---

## Paso 2 — Crear la App de Meta Developer

1. Ve a https://developers.facebook.com/
2. Inicia sesión con tu cuenta de Facebook
3. Clic en **"Crear app"**
4. Tipo: **"Empresa"** (Business)
5. Nombre: `Intel-Agents` (o cualquier nombre)
6. Correo: lucas.martinez.siciliano@gmail.com
7. Clic en **Crear app**

---

## Paso 3 — Añadir el producto Instagram

1. En el panel de la app → **"Añadir productos"**
2. Busca **"Instagram Graph API"** → clic en **Configurar**
3. Ve a **Instagram → Configuración API**

---

## Paso 4 — Conectar tu cuenta Instagram

1. En **"Instagram → API con token de usuario de Instagram"**
2. Clic en **"Agregar cuenta de Instagram"**
3. Inicia sesión con tu Instagram
4. Concede los permisos solicitados

---

## Paso 5 — Generar token de larga duración

El token por defecto dura 1 hora. Necesitas un token de 60 días.

```bash
# Reemplaza los valores con los tuyos:
APP_ID="TU_APP_ID"           # En: Panel app → Configuración básica → ID de la app
APP_SECRET="TU_APP_SECRET"   # En: Panel app → Configuración básica → Secreto de app
SHORT_TOKEN="EL_TOKEN_CORTO" # El que aparece en el panel después de conectar tu cuenta

# Generar token de larga duración (60 días):
curl "https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id=${APP_ID}&client_secret=${APP_SECRET}&fb_exchange_token=${SHORT_TOKEN}"
```

La respuesta incluirá un `access_token` de 60 días.

---

## Paso 6 — Obtener tu User ID de Instagram

```bash
ACCESS_TOKEN="EL_TOKEN_DE_60_DIAS"
curl "https://graph.facebook.com/v21.0/me/accounts?access_token=${ACCESS_TOKEN}"
```

De la respuesta, busca tu página de Facebook → luego:

```bash
PAGE_ID="ID_DE_TU_PAGINA"
curl "https://graph.facebook.com/v21.0/${PAGE_ID}?fields=instagram_business_account&access_token=${ACCESS_TOKEN}"
```

Esto te da el `instagram_business_account.id` — ese es tu **META_USER_ID**.

---

## Paso 7 — Guardar en el sistema

Opción A — Variables de entorno en Ubuntu (`~/.intel-env`):
```bash
export META_GRAPH_TOKEN="EL_TOKEN_DE_60_DIAS"
export META_USER_ID="TU_IG_BUSINESS_ACCOUNT_ID"
```

Opción B — Archivos locales (para agentes CCR en cloud):
```bash
echo "EL_TOKEN_DE_60_DIAS" > intel-agents/shared/meta_token.txt
echo "TU_IG_BUSINESS_ACCOUNT_ID" > intel-agents/shared/meta_user_id.txt
```

> [!warning] NO commitear estos archivos al repo. Añadir a .gitignore:
> ```
> intel-agents/shared/meta_token.txt
> intel-agents/shared/meta_user_id.txt
> ```

---

## Paso 8 — Renovar el token cada 60 días

El token expira a los 60 días. Para renovar automáticamente:

```bash
# Añadir a crontab (ubuntu): renovación mensual
0 8 1 * * source ~/.intel-env && curl -s "https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id=${META_APP_ID}&client_secret=${META_APP_SECRET}&fb_exchange_token=${META_GRAPH_TOKEN}" | python3 -c "import sys,json; d=json.load(sys.stdin); open(os.path.expanduser('~/.meta_token'), 'w').write(d['access_token'])"
```

O simplemente repetir el Paso 5 cuando el token expire.

---

## Verificar que funciona

```python
# Desde intel-agents/
import sys; sys.path.insert(0, '.')
from shared.instagram import meta_search_hashtag
print(meta_search_hashtag("inteligenciaartificial"))
```

Si devuelve posts con caption + likes + comentarios → está funcionando.

---

## Qué pueden hacer los agentes con esto

**Forge:**
- Monitorizar `#herramientasIA`, `#locallm`, `#openweights` en tiempo real
- Ver engagement de posts sobre tools nuevas (cuáles son realmente virales)
- Detectar cuando @javiniguezoficial o @dotcsv publican sobre un tool específico

**Horizon:**
- Monitorizar `#negocioIA`, `#solopreneur`, `#aibusiness`
- Ver posts de emprendedores con datos de revenue en Instagram
- Detectar tendencias en `#tiktokshop` para e-commerce
- Monitorizar `#proptech` para Centrum

---

## Limitaciones de la API

| Límite | Detalle |
|--------|---------|
| Hashtag search | Solo top 50 posts por hashtag (pero son los más relevantes) |
| Rate limits | 200 peticiones/hora — más que suficiente |
| Perfil privado | No accede a cuentas privadas |
| Datos propios | Con tu Business account también ves insights de tu propio IG |
| Histórico | Solo posts recientes (últimos ~7 días para recent_media) |
