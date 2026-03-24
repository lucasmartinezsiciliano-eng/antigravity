# HEARTBEAT.md — Vigilancia periódica de Axis

## Qué es el heartbeat
Cada 30 minutos el sistema te despierta automáticamente para que hagas esta revisión rápida. Usa el modelo más barato disponible (Gemini Flash-Lite). No es para ejecutar tareas complejas — es para vigilar y alertar si algo necesita atención urgente.

## Lista de comprobación en cada heartbeat

### Revisar
- ¿Hay mensajes urgentes sin responder en los últimos 30 minutos?
- ¿Ha fallado algún Cron Job? (revisar logs)
- ¿Está el gateway funcionando correctamente?
- ¿Hay algún lead de Firmax marcado como "A" sin contactar en más de 2 horas?

### Alertar a Lucas si:
- Un Cron Job ha fallado 2 o más veces seguidas
- Hay un mensaje con palabras: "urgente", "error", "caído", "fallo", "problema"
- Un lead nivel A lleva más de 2 horas sin contacto
- El gateway presenta errores

### No hacer durante el heartbeat:
- Tareas complejas de análisis
- Redactar contenido
- Buscar tendencias o productos
- Nada que ya esté cubierto por un Cron Job programado
- Gastar tokens innecesariamente

## Respuesta por defecto
Si no hay nada urgente → responder únicamente:
```
HEARTBEAT_OK
```
Sin más texto. Sin explicaciones. El sistema lo descarta automáticamente.

## Horario especial
- De 8:00 a 14:15 (lunes a viernes) → Lucas está en clase. Solo alertar si es verdaderamente crítico.
- De 23:00 a 7:00 → Solo alertar si hay un fallo de sistema grave.
