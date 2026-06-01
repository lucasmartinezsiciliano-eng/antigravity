---
name: centrum-objetivo-cliente
description: Cómo Ana (call-vendedor) y el dm-qualifier sacan EL dato que más define la estrategia: qué quiere realmente el cliente (quedarse, salir limpio de deuda, ganar tiempo o conseguir liquidez). Conecta el objetivo con las 8 estrategias y los evaluadores de bloque-6. Se activa en llamada IA y DM, una vez hay confianza. No promete soluciones.
version: 1
---

# El objetivo del cliente — el dato que decide la estrategia

> De todos los datos, **el que más cambia la recomendación** no es la deuda ni el banco: es **qué quiere conseguir el cliente.** Dos casos idénticos en cifras necesitan estrategias opuestas según si el cliente quiere quedarse en su casa o salir limpio de deuda. Por eso este dato vale por diez.
>
> `solution-matcher` y todos los evaluadores de bloque-6 arrancan de aquí.

---

## Las 4 grandes intenciones (no excluyentes)

| Intención | Cómo suena | Estrategias que abre (ver `8-estrategias`) |
|---|---|---|
| **Quedarse en la vivienda** a toda costa | "No quiero perder mi casa", "tengo a los niños aquí" | Estrategia 1 (ganar tiempo en la vivienda), negociación/refinanciación |
| **Salir limpio de deuda** (aunque suelte la casa) | "Solo quiero quitarme esto de encima", "no quiero deber nada más" | Dación, entrega a inversor con quita, venta |
| **Ganar tiempo** (aún no decide / necesita aire) | "Necesito unos meses", "no sé qué hacer todavía" | Estrategia de tiempo (Regla 2: 2-10 años en la vivienda), carencia |
| **Conseguir liquidez** | "Necesito algo de dinero para empezar de nuevo" | Entrega a inversor + pago único + alquiler |

> Muchas veces el cliente **no lo tiene claro**. No pasa nada: que Ana capte la inclinación dominante y la matice. Mariano cierra la decisión.

---

## Cómo lo saca Ana (sin presionar)

- **Momento:** después de validar la emoción y recoger lo crítico, cuando ya hay confianza. Nunca de entrada.
- **Pregunta abierta, no de menú:**
  - "¿Qué es lo que más te gustaría conseguir con todo esto?"
  - "Si pudieras elegir, ¿te quedarías en la casa o lo que quieres es salir de esto sin deudas?"
- **Escucha lo que hay detrás:** a veces dicen "quedarme" pero lo que pesa es el miedo a la calle; a veces dicen "lo que sea" por agotamiento. Ana acusa la emoción y refleja: "Te entiendo, lo que más te preocupa es {x}".
- **No promete la vía.** Recoge la intención; la viabilidad la dicen el análisis y Mariano.

---

## Qué registra en la ficha

```
objetivo_cliente: "quedarse" | "salir_limpio" | "ganar_tiempo" | "liquidez" | "indeciso"
objetivo_matiz: "texto libre: lo que de verdad pesa, en palabras del cliente"
```

Esto entra en la ficha que lee `call-prep` y orienta a `solution-matcher` y a los evaluadores. Si Ana no lo consigue, va a `datos_pendientes` (es de los primeros que Mariano preguntará).

---

## Conexión con las 3 reglas

- **Regla 2 ("nunca hay caso sin salida"):** aunque el cliente esté hundido, siempre hay al menos la vía de ganar tiempo. Ana puede transmitir esperanza realista **sin prometer** un resultado concreto.
- Nunca se le dice al cliente cuál es "su" estrategia en la llamada: eso lo hace Mariano tras el análisis. Ana solo deja claro que **hay opciones** y que se van a estudiar.
