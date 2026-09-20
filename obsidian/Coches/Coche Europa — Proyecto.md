---
tags: [coches, importacion, app, mvp]
status: mvp-funcional
updated: 2026-09-20
related:
  - "[[🗺️ MOC — Antigravity]]"
---

# Coche Europa — Buscar e importar coches de Europa

> App para encontrar coche en Alemania, Francia, Italia, etc., saber lo que cuesta
> de verdad traerlo a España y revisarlo paso a paso antes de pagar.
> Código en `coche-europa/` (rama `claude/car-search-app-europe-bpfulw`).

---

## Qué es

Tres problemas en una sola app:

1. **Buscar** — un formulario de filtros que se lanza contra 13 portales de 9 países.
2. **Calcular** — del precio del anuncio al coste real matriculado en España.
3. **Revisar** — 70 puntos guiados, en el orden en que hay que hacerlos.

Stack: Next.js 16 · React 19 · TypeScript · sin base de datos (todo en `localStorage`).

---

## Decisión clave: por qué no hay scraping

Ni AutoScout24, ni mobile.de, ni Leboncoin tienen API pública. Rascar sus webs va
contra sus condiciones y se rompe cada dos semanas. La app hace tres cosas en su
lugar:

| Modo | Estado | Qué hace |
|------|--------|----------|
| Enlaces profundos | Siempre activo | Traduce los filtros a la URL de búsqueda de cada portal |
| Fuentes en vivo | Opcional | eBay Browse API (oficial) + puente propio vía `BRIDGE_URL` |
| Fichas de ejemplo | Solo si no hay fuentes | Coches inventados, siempre etiquetados como EJEMPLO |

**El puente es el hueco para n8n.** `n8n/coche-europa-bridge.json` implementa el
contrato: recibe `{filters, portals}` y devuelve `{listings}`. El nodo
`Fetch Listings From Source` está vacío a propósito — ahí se enchufa la fuente
que tengamos (feed de concesionario, API con credenciales, base propia).

**Detalle que importa:** la app traduce el nombre del modelo a cada mercado.
Buscar "Clase C" manda `C-Klasse` a mobile.de y `Classe C` a Leboncoin. Sin eso,
las búsquedas alemanas vuelven vacías.

Todas las URLs viven en `lib/portals.ts`. Si un portal cambia sus parámetros, se
arregla ahí y en ningún sitio más.

---

## Fiscalidad implementada (`lib/import-cost.ts`)

Revisado a 2026-09. Cuando cambie el BOE, tocar `DATOS_ACTUALIZADOS` y los tramos.

- **Impuesto de matriculación (IEDMT)** por tramo de CO2 WLTP:
  - Península y Baleares: 0 % (<120) · 4,75 % (120-159) · 9,75 % (160-199) · 14,75 % (≥200)
  - Canarias: 0 / 3,75 / 8,75 / 13,75 % · Ceuta y Melilla: exento
  - Sin dato de CO2 se aplica el tramo máximo (es lo que hace Hacienda).
- **IVA 21 %** solo si es *medio de transporte nuevo*: menos de 6 meses o menos
  de 6.000 km. Pilla a mucha gente.
- **ITP** por CCAA, opcional. En compras UE entre particulares es discutido:
  hay comunidades que lo reclaman y gestorías que sostienen que no procede.
  Va activado por defecto para no quedarse corto.
- Transporte (camión o ir a buscarlo con placas temporales), COC, ficha técnica
  reducida, ITV de importación, tasa DGT (~99,77 €), gestoría e informe de VIN.

**Aviso que la app repite:** la base imponible no es lo que pagas, es el valor de
las tablas de precios medios de Hacienda. Hay un estimador por coeficiente de
antigüedad a partir del precio del modelo nuevo.

---

## Revisión guiada (`lib/checklist.ts`)

70 puntos en 8 fases, filtrados al coche concreto:

1. **Antes de coger el avión** — todo por WhatsApp. Si falla aquí, no se viaja.
2. **Papeles** — cambian por país: Teil II alemán, non-gage francés, fermo
   italiano, tenaamstellingscode holandés.
3. **Arranque en frío** — lo primero al llegar, y solo funciona una vez.
4. Chapa y pintura · 5. Interior y electrónica · 6. Motor y fluidos
7. Prueba en carretera · 8. Cerrar la compra

Se adapta solo: un diésel añade DPF y AdBlue, un automático añade DSG, un
eléctrico añade salud de batería, y los documentos son los del país elegido.

Cada punto tiene peso, si es crítico y cuánto cuesta arreglarlo. **Los críticos
no se negocian** (son motivo para irse); el resto suma un importe concreto de
descuento. El informe final da veredicto y precio máximo a pagar:

```
precio máximo = precio en España − sobrecoste de importación − arreglos − 5% margen
```

---

## Estado y siguiente paso

- [x] MVP completo y funcionando: build, lint y tipos limpios
- [x] Verificado en navegador (los 4 flujos, sin errores de consola)
- [ ] Validar en el navegador las URLs de los 13 portales (el contenedor de
      desarrollo los bloquea, no se han podido probar en vivo)
- [ ] Decidir despliegue: Netlify, o contenedor en el Oracle junto al resto
- [ ] Si se quiere búsqueda agregada de verdad: montar el flujo del puente en n8n
- [ ] Sin decidir: si esto es herramienta propia o producto para vender

---

## Notas de negocio

El gancho es real: un alemán de tres años puede costar 4.000 € menos que aquí.
Lo que mata la operación son tres cosas, y la app cubre las tres — kilómetros
maquillados, papeles que no permiten matricular (Teil II en el banco), e
impuesto de matriculación que se come el ahorro entero cuando el CO2 se pasa de
tramo.
