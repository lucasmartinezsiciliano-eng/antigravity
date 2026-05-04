# Analisis Experto — Respuestas de Mariano + Mejoras para Lucas
**Para construir en OpenClaw | Abril 2026**
**Analizado por Claude en base al Briefing completo + AGENTES.pdf de Lucas**

---

## Como leer este documento

- **VALIDADO** — La respuesta de Mariano es suficiente y correcta tal cual
- **MEJORAR** — La respuesta existe pero esta incompleta o poco precisa para construir el agente
- **REDEFINIR** — El agente tiene una premisa erronea que hay que corregir antes de construir
- **VACIO** — No hay respuesta; aqui propongo la definicion basada en el contexto del proyecto
- **LUCAS** — Observaciones del AGENTES.pdf de Lucas que afectan a este agente

---

# BLOQUE 0 — Inteligencia Externa

---

## market-watcher

**REDEFINIR — el enfoque del agente esta mal orientado**

El agente original monitorea Euribor, tipos de interes y precios de vivienda. La respuesta de Mariano lo deja claro: *"No me interesa si sube el Euribor, eso es para el cliente que esta pagando. Mi cliente debe 3 o mas cuotas y a ese no le importa si le sube un euro la hipoteca."*

**Definicion corregida:**
Este agente debe monitorear exclusivamente:
1. Numero de nuevos procedimientos judiciales de ejecucion hipotecaria (INE, Banco de Espana, CGPJ)
2. Estadisticas de impago hipotecario publicadas por Banco de Espana
3. Morosidad hipotecaria por provincia (especialmente Cataluna y Tarragona)
4. Volumen de subastas programadas en Cataluna (portal subastas BOE)

**Salida:** Informe semanal de "termometro del mercado Centrum" — cuantas familias nuevas entran en problemas esta semana en nuestra zona.

---

## law-tracker

**VALIDADO con ampliacion importante**

Mariano dice: *"SI ESO ME INTERESA"* y detalla las 8 estrategias legales que el sistema debe conocer:

1. Quedarse el maximo tiempo posible en la vivienda
2. Entregar posesion del inmueble a cambio de un pago unico + derecho de explotacion al inversor
3. Negociar una quita + vender el piso y sacar un pequeno rendimiento
4. Negociar una quita + familiar obtiene hipoteca nueva para comprar el piso
5. Denunciar clausulas abusivas y quedarse mientras dura el procedimiento judicial
6. Defender al cliente contestando la demanda
7. Contrato de alquiler inscrito en registro con opcion a compra y derecho a subalquilar
8. Etc. (combinaciones segun cada caso)

**Estas 8 estrategias deben estar codificadas en law-tracker Y en solution-matcher como las soluciones que Centrum puede ofrecer.**

No quiere que el sistema defina estrategias legales — solo que genere un resumen juridico del procedimiento para pasarselo al abogado. El abogado define la estrategia segun lo que quiere el cliente.

Tiene abogado de confianza. No quiere que el sistema le alerte directamente al abogado.

---

## competitor-spy

**REDEFINIR — el mercado es un espacio vacio, no una competencia a vigilar**

Hallazgo critico de Mariano: *"Este servicio de ayuda al deudor de un grupo de profesionales con conciencia social (abogados, brokers hipotecarios y agentes de la propiedad inmobiliaria) NO vi ninguna web. Todo lo que veo es separado."*

El mercado fragmentado ES la oportunidad de Centrum. No hay nadie ofreciendo el servicio triple integrado.

**Redefinicion del agente:**
- En vez de "vigilar competencia", este agente monitorea el mercado fragmentado para confirmar que Centrum sigue siendo el unico servicio integrado
- Alerta si aparece algun nuevo competidor con propuesta similar
- Monitorea abogados, gestoras y brokers por separado para detectar si alguno intenta integrar servicios
- Diferenciador a proteger: "Conciencia social + abanico completo de opciones juridicas Y financieras"

---

## avatar-researcher

**VALIDADO — perfil de cliente definido con claridad**

Perfil del cliente Centrum segun Mariano:
- Pareja con hijos, entre 30 y 60 anos
- Problemas economicos por perdida de trabajo o proyecto personal fallido
- No pueden pagar la cuota hipotecaria ni otros prestamos
- Miedo principal: perder la vivienda, quedar con deuda despues de la subasta, quedarse en la calle, verguenza familiar
- Cuando llaman por primera vez ya llevan tiempo con el miedo acumulado
- Lo que no cuentan en la primera llamada: aun no lo sabe (proyecto nuevo, hay que documentarlo)

**Este perfil debe ser el ancla de todo el contenido y comunicacion de Centrum.**

---

## trend-exploiter

**VALIDADO con regla clara**

Mariano quiere revisar el contenido antes de publicarlo aunque pierda rapidez. Prioridad = control sobre velocidad.

Cuando haya un tema caliente: sistema genera propuesta de angulo → Mariano aprueba → se publica.

---

# BLOQUE 1 — Produccion de Contenido

---

## content-director

**REDEFINIR — modelo de saturacion progresivo (referencia: Beltran Briones)**

La estrategia de Centrum en contenido organico es el modelo Briones: volumen alto de videos, medir cuales funcionan, repetir los ganadores hasta que dejen de funcionar, y escalar progresivamente abriendo nuevas cuentas.

**La logica del modelo Briones aplicada a Centrum:**
*"Haces 100 videos, 87 son malos y 13 funcionan. Repites esos 13 hasta el agotamiento."*
Objetivo: generar suficiente volumen para que el algoritmo no tenga opcion de no empujar el contenido.
Beltran Briones consiguio 3.000-4.000 consultas por semana de contenido organico en el sector inmobiliario argentino — el mismo funnel que necesita Centrum.

**Arquitectura de cuentas — escalado progresivo:**

| Fase | Cuentas TikTok | Cuentas Instagram | Videos/dia | Videos/mes |
|------|---------------|-------------------|------------|------------|
| Mes 1-2 | 2 | 2 | 2-4 | 60-120 |
| Mes 3-4 | 4 | 4 | 4-8 | 120-240 |
| Mes 5-6 | 6-8 | 6-8 | 8-16 | 240-480 |
| Mes 6+ | 10+ | 10+ | 15-20+ | 450-600+ |

**Reglas para no recibir ban:**
- Cada cuenta tiene email distinto, numero de telefono distinto, dispositivo diferente (o perfil diferente en el mismo dispositivo)
- No subir el mismo video identico a cuentas distintas — pequenas variaciones (corte diferente, subtitulo diferente, musica diferente)
- Cada cuenta tiene su propio ritmo de crecimiento — no arrancar todas el mismo dia
- Contenido 90% educativo / informativo, 10% llamada a accion directa (los algoritmos penalizan el contenido demasiado comercial)
- No poner links en los primeros comentarios (TikTok especialmente lo detecta como spam)

**Sistema de produccion para el agente:**

1. **Generar en batch:** El sistema produce 20-30 guiones a la vez agrupados por tema (semana tematica: "todo sobre clausulas abusivas", "todo sobre quitas", "miedos del deudor", etc.)
2. **Clasificar por formato:** Para cada tema, generar variaciones — gancho de miedo, gancho de promesa, gancho de dato sorprendente, formato historia real, formato pregunta-respuesta
3. **Distribuir entre cuentas:** Cada cuenta recibe un mix de temas y formatos. No se repiten guiones identicos entre cuentas
4. **Medir rendimiento:** Registrar visualizaciones, comentarios, tiempo de visualizacion de cada video. Los que superan X visualizaciones en 48h son "ganadores"
5. **Clonar ganadores:** De cada video ganador, el sistema genera 5 variaciones (mismo concepto, diferente apertura / diferente CTA / diferente historia de ejemplo)
6. **Revision de Mariano:** Solo los primeros videos de cada nueva "familia tematica" necesitan aprobacion. Una vez que el tema esta aprobado, las variaciones se suben automaticamente

**Temas de contenido prioritarios para Centrum (90% educativo):**
- Que opciones tiene alguien que no puede pagar la hipoteca (serie de 10+ videos)
- Diferencia entre deuda hipotecaria y perder la casa (desmontando el mito)
- Como funciona realmente una ejecucion hipotecaria paso a paso
- Que son las clausulas abusivas y por que los bancos no las explican
- Casos reales (anonimizados): como salio esta familia adelante
- Lo que el banco NO te dice cuando llamas para "negociar"
- Cuanto tiempo se puede realmente ganar antes de la subasta
- Que es una quita y como se consigue
- La diferencia entre un abogado solo, un broker solo, y un equipo como Centrum
- Preguntas que la gente tiene verguenza de hacer sobre deuda hipotecaria

**Mensajes que deben aparecer SIEMPRE en todo contenido:**
- "Consulta gratuita" / "Estudio gratuito de tu caso"
- "20 anos de experiencia"
- "Tarragona y Cataluna"
- El CTA final siempre a WhatsApp (chatbot de cualificacion)

**LUCAS puntos 1, 2, 3, 7:** Avatar animado para los videos. Freepik para creatividades. Agente editor para postproduccion. Cuantos mas videos mejor — este modelo lo confirma completamente.

---

## tiktok-scriptwriter

**VALIDADO — voz y tono muy bien definidos**

Tono: formal, directo, profesional, que transmita confianza.

El cliente NO quiere servicios. Quiere: Seguridad, Tiempo, Solucion clara, No sentirse solo.

Frases de Mariano para usar en guiones:
- "Te ayudo a no perder tu casa"
- "¿Tienes miedo en PERDER TU VIVIENDA?"
- "¿Tu banco te dio alguna solucion?"
- "¿Estas en proceso de ejecucion judicial?"
- "Llamanos que podemos ayudarte con soluciones hipotecarias y/o juridicas"
- "No te rindas y pierdas tu casa"

**Sobre el formato:** Probar avatar vs. cara real. Hacer A/B test para ver que convierte mas.
Traje con camisa pero sin corbata: cercano, profesional.

**LUCAS punto 1 y 3:** Crear avatar animado. Buscar agente editor. Integrar con Freepik para imagenes/videos.

---

## tiktok-hook-specialist

**VALIDADO — miedos del cliente mapeados**

Los 4 miedos del cliente (en orden de impacto segun Mariano):
1. Perder la vivienda
2. Quedar con deuda con el banco
3. Quedarse en la calle con la familia
4. Verguenza con los suyos

**Regla critica para ganchos:** Mariano no quiere trasladar mas miedo. La gente ya lo tiene. El gancho debe transmitir que HAY SOLUCIONES, no que la situacion es terrible.
Contraste con lo que les dicen los call centers bancarios: "Perderas todo si no pagas" — eso es lo que NO queremos replicar.

---

## meta-copywriter

**VALIDADO con decision clave**

Anonimo / avatar, NO cara de Mariano.
Mensaje central: *"Salvamos Tu Vivienda — Un grupo de profesionales con conciencia social unidos para defender tu derecho a la vivienda. Soluciones integrales, resultados reales."*
Fundamento legal: Art. 47 Constitucion Espanola.

---

## meta-headline-tester y meta-audience-builder

**MEJORAR — alerta importante sobre cumplimiento de anuncios**

Mariano advierte: *"Meta Ads y Google Ads castigan frases como 'Paramos tu desahucio' o 'Salvamos tu vivienda' en anuncios de pago."* Estas frases son para contenido organico, no para ads pagados.

**Regla para el sistema:**
- Contenido organico (TikTok, posts): puede usar lenguaje emocional directo
- Anuncios pagados (Meta Ads, Google Ads): lenguaje neutral, enfocado en consulta gratuita / estudio del caso

Audiencia inicial: Tarragona provincia + sur de Barcelona. Edad 40-65.
Presupuesto inicial Meta: 500€/mes.

**LUCAS punto 6:** Agente especifico que gestione los ads. Incluir en la definicion del agente.

---

## google-keyword-researcher

**VACIO — Mariano pide que el sistema lo haga**

Mariano dice: *"No hice el estudio todavia, hazlo tu."*

**Propuesta de keywords por urgencia para Centrum:**

Alta urgencia (intent de busqueda activa):
- "me van a quitar el piso" / "van a subastar mi casa"
- "que hacer si no puedo pagar hipoteca" / "cuotas hipoteca sin pagar"
- "ejecucion hipotecaria que hacer" / "demanda banco hipoteca"
- "como parar desahucio" / "plazo antes de subasta hipoteca"

Media urgencia:
- "negociar hipoteca con banco" / "quita hipotecaria"
- "abogado ejecucion hipotecaria Tarragona"
- "clausulas abusivas hipoteca" / "dacion en pago hipoteca"

Informacional:
- "que es ejecucion hipotecaria" / "segunda oportunidad hipoteca"
- "fondo buitre hipoteca que hacer"

Negativas sugeridas (excluir):
- "simulador hipoteca" / "contratar hipoteca" / "hipoteca nueva"
- "calcular cuota hipoteca" / "tipo hipoteca fijo variable"
- Busquedas fuera de Cataluna (hasta escalar)

Budget Google Ads: pendiente de definir (empezar con 300€/mes segun Mariano para el primer mes total).

---

## content-scheduler

**MEJORAR — una regla clara + pendiente de definir**

Regla validada: leads solo dias laborables. El sistema coordina los anuncios para que el volumen llegue de lunes a viernes.

Pendiente: estacionalidad. Mariano no tiene datos todavia. Recomendacion: activar seguimiento desde primer mes para detectar patrones (inicio de mes, enero, septiembre).

**LUCAS punto 7:** Cuantos mas videos y contenido se hagan, mejor. Aumentar cadencia conforme el sistema aprenda que convierte.

---

## content-repurposer

**VALIDADO — contexto importante**

Web de Centrum en construccion. Perfiles de redes sociales en construccion.
El agente empieza a operar cuando la web este activa.

---

# BLOQUE 2 — Conversion Web

---

## form-analyzer

**MEJORAR — Mariano define exactamente que preguntas quiere en el formulario**

Preguntas que Mariano quiere anadir al formulario (marcadas como REVISAR DEFINITIVAMENTE):
1. Con que banco tiene la hipoteca
2. Quienes intervienen en la hipoteca (hay avalistas?)
3. Tu banco te dio alguna solucion?

Las 5 preguntas clave de deteccion rapida que el agente debe evaluar:
1. Cuanto debes al banco?
2. Valor aproximado de la vivienda?
3. Es vivienda habitual?
4. Has recibido demanda judicial?
5. Quieres mantenerla o vender?

Los 4 criterios de viabilidad que el agente debe verificar:
- Hay vivienda con valor? (para venta)
- Hay margen para venta? (deuda < valor)
- Hay posibilidad de negociacion? (banco / fondo buitre accesible)
- Hay familiar que pueda intervenir? (hipoteca nueva de familiar)

---

## lead-classifier

**MEJORAR — falta una categoria de cliente**

Mariano identifica una categoria que el sistema no contempla:
**Categoria E: ENTREGA DE POSESION** — El cliente quiere entregar voluntariamente la posesion del inmueble a cambio de un pago unico. No quiere litigar, no quiere quedarse: quiere salir con algo de dinero.

Clasificacion completa:
- **A) URGENTE** — Subasta o demanda activa. Llamar hoy.
- **B) NORMAL** — Sin demanda, seguimiento en 24h.
- **C) NO CUALIFICADO** — Sin hipoteca, fuera de zona, caso imposible.
- **D) DERIVAR ABOGADO** — Fase judicial avanzada, necesita defensa legal.
- **E) ENTREGA POSESION** — Cliente quiere entregar el inmueble a cambio de un pago. Caso para broker + inversor.

Derivacion de casos a abogado: Mariano envia el informe generado → el abogado llama al cliente.
Tiene red de referidos para casos que no puede atender el.

---

## auto-responder

**MEJORAR — mensaje bien definido, plazo a corregir**

Mariano corrige el plazo: NO "en menos de 24 horas". Usar "a la brevedad".
Firma: "El equipo de Centrum de la Vivienda"
Promesa exacta: *"Estudiaremos su caso para darle la mejor solucion posible"*
Tono: confianza y tranquilizador.

El mensaje NO puede prometer resultados. No puede decir "solucionaremos su caso."

**LUCAS punto 9:** El auto-responder solo funciona por email y WhatsApp. Lucas quiere expandirlo a otras redes sociales (Instagram DM, TikTok comments, Facebook). Habra que estudiar referentes que lo hacen.
Ademas: cuando alguien comenta una palabra clave ("info", "ayuda") en un video, el sistema les escribe por privado para iniciar la captacion.

---

## lead-notifier

**MEJORAR — canal cambiado**

Mariano no quiere notificaciones por WhatsApp personal. Quiere:
- Email cuando se genera el lead
- CRM (panel que el mismo revisa)
- Todos los leads, no solo urgentes

---

# BLOQUE 3 — Primer Contacto

---

## call-prep

**VALIDADO — Mariano define exactamente el formulario de captacion**

Los datos que Mariano quiere tener ANTES de llamar (lista completa):
- a) Nombre completo
- b) Telefono y email
- c) Direccion completa del inmueble (calle, piso, municipio)
- d) Capital pendiente de hipoteca
- e) Situacion de impago: si/no. Si si: cuantas cuotas
- f) Cuota mensual actual en euros
- g) Entidad bancaria de la hipoteca
- h) Numero de titulares
- i) Avales: si/no. Si si: quien? Tiene propiedades el avalista?
- j) Tipo de interes
- k) Tiempo de hipoteca restante
- l) Otras deudas: si/no. Si si: tipo y cantidad, al dia?
- m) Notificacion judicial: si/no. Si si: cuanto hace?

**Formato de entrega:** Panel dentro del CRM, no WhatsApp.

---

## question-suggester

**VALIDADO — Mariano entrega el cuestionario completo de fase 2**

Primera pregunta de toda primera llamada sin excepcion:
"¿Estas en situacion de impago o morosidad? Si/No. Cuantas cuotas?"

Preguntas de fase 2 (para cuando el cliente ya tiene confianza y se define la solucion):

*Estado fisico del inmueble:*
- Ano de construccion y superficie (m2)
- Numero de habitaciones y banos
- Estado de conservacion (reforma reciente / necesita reforma / buen estado)
- Certificados: cedula de habitabilidad, ITE, certificado energetico
- Gastos comunitarios e IBI aproximados
- Deudas con la comunidad y con IBI
- Plaza de garaje o trastero incluidos en hipoteca?

*Valor y precio:*
- Precio aproximado razonable para vender (segun cliente)
- Minimo necesario para cubrir deudas y gastos
- Acceptaria venta directa a inversor (posible descuento) si resuelve rapidamente?

*Proceso y logistica:*
- Disponible para visitas (con cita)?
- Tiene documentacion catastral y nota simple reciente?
- Dispone de escritura y ultima liquidacion de hipoteca?
- Puede aportar ultimas 3 nominas si hace falta negociar?

*Consentimiento RGPD:*
- Permiso para tratar sus datos?
- Canal preferido de contacto?

*Cierre / proximos pasos:*
- Le gustaria que estudiemos una propuesta concreta?
- Mejor fecha/hora para visita o propuesta escrita?

**Nota de diseno:** Estas preguntas de fase 2 son las que definen a que profesional se pasa el lead: abogado, broker hipotecario o inmobiliaria. El agente debe tener esta logica incorporada.

---

## call-transcriber

**MEJORAR — dos fases de implementacion**

Mariano quiere arrancar YA. No quiere retrasar el proyecto por temas tecnicos.

**Fase 1 (lanzamiento):** Mariano escribe manualmente en el CRM lo que averiguo en la llamada.
**Fase 2 (mas adelante):** Grabacion de llamada + IA rellena el CRM automaticamente por campos.

Lo primero que anota siempre: URGENCIAS DEL CLIENTE.

**LUCAS punto 10:** Hay una IA china gratuita que clona voces con pocos audios. Estudiar si vale la pena clonar la voz de Mariano para comunicaciones automaticas. Alternativa: usar voz femenina que genere confianza. Puede usarse cuando faltan documentos o hay informacion incorrecta y el sistema necesita "llamar" al cliente.

---

## missing-data-detector

**VALIDADO — 3 datos criticos identificados**

Los 3 datos sin los que NO se puede avanzar ningun caso:
1. Cuantas cuotas debe + con que banco
2. Quienes intervienen en la hipoteca (titulares y avalistas)
3. El banco le dio alguna solucion? (indica si hay negociacion abierta)

---

## ficha-saver

**MEJORAR — herramienta y acceso**

Mariano no usa Notion actualmente pero esta abierto a usarlo si es la mejor opcion.
Hay otras personas que necesitan acceso a las fichas: al menos el abogado de confianza.

**Recomendacion para Lucas:** CRM como hub central. Abogado tiene acceso restringido a sus expedientes via CRM (solo los que le corresponden). Al principio: PDF por email. Despues: acceso directo al CRM.

---

# BLOQUE 4 — Documentacion

---

## doc-director

**MEJORAR — timing correcto del proceso**

La documentacion solo se pide DESPUES de que el cliente ha dicho lo que quiere Y hay viabilidad de caso. No antes.

Proceso correcto:
1. Lead llega → calificacion → primera llamada
2. En la llamada: el cliente define lo que quiere
3. Si hay viabilidad: se genera el informe preliminar
4. Solo entonces se solicita la documentacion para avanzar

**LUCAS punto 11:** Antes de que el sistema avise al cliente que falta documentacion, debe pedirle confirmacion a Mariano. El envia el aviso solo si Mariano confirma. Logica: evitar mensajes automaticos en casos que Mariano ya gestiona directamente.

---

## doc-checklist-generator

**VALIDADO — documentos minimos definidos**

Siempre, sin excepcion:
- Escritura de hipoteca Y escritura de compraventa
- DNI de todos los titulares y avalistas

Segun el caso:
- Venta: nota simple del registro, extracto bancario, certificado de comunidad, certificado energetico
- Negociacion: cartas del banco, demanda judicial si existe, ultimas nominas/declaracion renta
- Defensa legal: todo lo anterior mas correspondencia con el banco

Problema mas comun: cliente no tiene la escritura de hipoteca (hay que ir al notario donde se firmo a pedir copia simple).

---

## doc-validator

**VALIDADO**

Problema mas frecuente: fotocopias ilegibles.
La IA puede verificar automaticamente si los documentos son validos (fechas, caducidades, titulares).

---

# BLOQUE 5 — Analisis del Caso

---

## debt-analyzer

**VALIDADO — insight muy importante para el agente**

Mariano dice: *"CASI SIEMPRE en muchos casos"* los intereses de demora o comisiones han inflado la deuda de forma que el banco no podria defender en juicio.

Este dato es crucial: el agente debe buscar activamente esta inflacion en TODOS los casos, no solo cuando se sospecha.

Insight clave sobre ratio deuda/valor: *"No hay un punto de no retorno. Siempre hay alguna posibilidad de ayuda. Lo unico que a veces solo es estirar tiempo para que el propietario pueda ahorrar y luego de la subasta intentar comprar otra vivienda limpio de deudas con ayuda del broker."*

**Esta filosofia debe estar en el prompt del agente:** nunca concluir que un caso no tiene salida sin explorar todas las opciones, incluyendo ganar tiempo.

---

## legal-risk-assessor

**VALIDADO — timing critico documentado**

Punto de no retorno: cuando hay FECHA DE SUBASTA (muy complicado pero no imposible).
Momento ideal para intervenir: ANTES de que este inscrito en el Registro de la Propiedad el procedimiento judicial, o dentro del primer ano de inicio del procedimiento.
Duracion tipica demanda → subasta: varios anos (depende del juzgado).

---

## property-valuator

**VALIDADO — herramienta ya existente**

Mariano ya tiene suscripcion a Casafari para valoraciones aproximadas.
Complementa con Idealista/Fotocasa/Catastro.
Tiene red de inmobiliarias de confianza que pueden hacer valoraciones rapidas.
El agente puede contactar automaticamente a esa red para obtener valoracion rapida.

---

## bank-behavior-analyst

**VALIDADO — logica de negociacion documentada**

Los bancos varian mucho en disposicion a negociar.
Cuando la deuda la tiene un fondo buitre: depende del fondo, del despacho juridico que lo gestiona, y de los objetivos del fondo en ese periodo (tienen targets anuales de recuperacion).

Contactos directos con bancos: Mariano o el abogado segun el estado de la negociacion.
El sistema NO gestiona esa comunicacion — la facilita pero la ejecuta Mariano.

---

## clause-detector

**VALIDADO — muy relevante para pre-2010**

Muy comun encontrar clausulas abusivas en hipotecas anteriores a 2010.
Ha usado este argumento para negociar con exito.
Flujo: sistema genera informe de clausulas detectadas → abogado confirma cuales son accionables.

---

## case-summarizer

**MEJORAR — orden de prioridad en el resumen**

Lo primero que Mariano busca cuando tiene el analisis completo:
1. Situacion actual de la reclamacion del banco (en que estado esta el procedimiento)
2. Lo que desea el cliente (dependiendo de su situacion judicial)

El resumen ejecutivo debe estar ordenado en este formato:
[ESTADO DEL PROCEDIMIENTO] → [LO QUE QUIERE EL CLIENTE] → [OPCIONES VIABLES] → [URGENCIA]

**Importante:** El informe de analisis es para Mariano y el abogado — NO para el cliente. El cliente recibe la explicacion verbal de Mariano o del abogado.

---

# BLOQUE 6 — Soluciones

---

## solutions-director

**MEJORAR — division de trabajo muy importante**

Mariano define claramente quien gestiona cada tipo de solucion:
- **Mariano (Mediterranea Firmax) gestiona:** Casos donde la deuda es menor que el valor del inmueble → venta directa, sin necesidad de abogado
- **Abogado gestiona:** Casos en proceso judicial → defensa legal, negociacion con banco via legal, litigio

El informe de opciones se lo da el abogado al cliente en la mayoria de los casos judiciales.
Mariano no quiere duplicar informes.

---

## solution-matcher

**VALIDADO — logica de decision documentada**

Regla principal:
- **Deuda < Valor del inmueble:** Venta del inmueble. Cliente se queda con dinero y queda sin deudas.
- **Deuda > Valor del inmueble:** Negociacion con el acreedor:
  1. Quita para vender
  2. Quita + seguir pagando hipoteca reestructurada
  3. Litigar por clausulas abusivas + negociar quita despues (1-4 anos segun juzgado) + vender
  4. Entrega de posesion a inversor + cobrar derecho de explotacion X anos
  5. Hipoteca nueva de familiar para comprar el inmueble del deudor
  6. Ganar el maximo tiempo posible para que el cliente ahorre sin pagar cuota ni alquiler

Mariano dice: *"SI VARIAS VECES las soluciones que el cliente creia imposibles resultaron viables."*

---

## sale-evaluator

**VALIDADO**

Red de compradores/inversores existente.
Descuento que suelen exigir los inversores: 10%-40% dependiendo del estado y zona del inmueble.

Argumento mas convincente para convencer a quien no quiere vender:
*"Si vendes ahora sales sin deuda y con dinero. Si esperas, subastas el piso, quedas sin el piso Y con deuda."*

Complicaciones frecuentes: segunda carga en el inmueble (Hacienda, Seguridad Social, otro banco) que puede hacer inviable la venta limpia → en ese caso solo queda ir a subasta.

---

## negotiation-evaluator

**VALIDADO**

Mayor quita conseguida: 50% de la deuda.
Hay bancos con los que la negociacion directa es imposible → hay que ir por via legal.
Tiempo de negociacion: depende de muchos factores y del banco (no cuantificable a priori).

---

## time-gain-evaluator

**VALIDADO — insight muy valioso**

Para que sirve ganar tiempo:
- El cliente puede vivir en el inmueble SIN pagar cuota hipotecaria NI alquiler
- Ese dinero ahorrado es lo que le permite reorganizarse y planear el futuro
- Al final del proceso (despues de la subasta, con segunda oportunidad) puede intentar comprar otra vivienda limpio de deudas con ayuda del broker

Tiempo realista que se puede ganar: **2 a 10 anos** dependiendo del caso y del juzgado.

---

## case-improver

**VALIDADO — ejemplo real de solucion creativa**

Caso real documentado por Mariano: El procedimiento de ejecucion NO estaba todavia inscrito en el Registro de la Propiedad. Se estructuro un derecho de explotacion del inmueble a una empresa inversora por X anos, cediendo la posesion. El cliente cobro un unico pago importante y se fue contento.

**Este tipo de solucion creativa es el valor diferencial de Centrum. El agente debe buscar activamente estas "ventanas" antes de cerrar el analisis.**

---

# BLOQUE 7 — Comunicacion con el Cliente

---

## legal-language-checker

**MEJORAR — regla critica de seguridad juridica**

Mariano define con claridad la linea roja:
*"Nunca confirmar nada por mail o WhatsApp. Eso siempre se dara en la reunion con el cliente o en papel. MUCHO CUIDADO CON ESTO."*

**Regla obligatoria para todos los agentes de comunicacion:**
- Por email/WhatsApp: solo confirmaciones de cita, recordatorios de documentacion, actualizaciones de estado, mensajes de cortesia
- Jamas por escrito: estrategias, recomendaciones, porcentajes de exito, plazos judiciales, promesas de resultado
- Cualquier informacion que implique asesoramiento o promesa → solo en persona o en documento firmado

---

## comms-director

**MEJORAR — que mensajes necesitan aprobacion de Mariano**

Mariano dice que quiere aprobar solo los importantes, pero falta definir cuales.

**Propuesta de clasificacion:**

Aprobacion obligatoria de Mariano:
- El informe de opciones al cliente
- Cualquier mensaje que mencione plazos judiciales
- El informe que va al abogado
- Mensajes de cierre de caso

Automaticos sin aprobacion:
- Confirmacion de recepcion del formulario (auto-responder)
- Recordatorios de documentacion pendiente (previa confirmacion de Mariano segun lucas)
- Actualizaciones de estado: "estamos trabajando en su caso"
- Avisos de cita

---

## tone-checker

**VALIDADO**

Vocabulario de Mariano: normal, sin tecnicismos, sin lenguaje juridico extremo.
Trato: de tu o de usted segun el cliente (el agente debe seguir el patron establecido en el primer contacto del caso).

---

## whatsapp-writer y whatsapp-sender

**VALIDADO**

Numero de Centrum separado del personal de Mariano.
Respuestas al WhatsApp Business van a un panel registrado (no al movil personal).
Canal preferido: primero WhatsApp con chatbot para recoger datos, luego llamada.

---

# BLOQUE 8 — Seguimiento de Casos

---

## client-updater

**VACIO — Mariano no respondio. Propuesta:**

Basado en el contexto del proyecto y perfil del cliente Centrum (personas en situacion de angustia):

**Frecuencia recomendada:**
- Casos urgentes (subasta en menos de 90 dias): contacto cada 3-4 dias
- Casos activos con proceso judicial: contacto semanal
- Casos en espera (documentacion, negociacion larga): contacto cada 2 semanas
- Mensaje cuando no hay novedades: *"Hola [nombre], seguimos trabajando en su caso. En cuanto tengamos novedades le avisamos. Si tiene alguna pregunta, estamos aqui."*

**LUCAS punto 12:** Lucas quiere una solucion (app o sistema) para que cuando el caso pase al abogado, Centrum pueda seguir al tanto sin molestar al abogado constantemente. Propuesta: el abogado tiene acceso al CRM y puede actualizar el estado del caso; el sistema notifica a Mariano cuando hay cambios, sin necesidad de llamar.

---

## case-closer

**VACIO — Mariano no respondio. Propuesta:**

Un caso se cierra cuando:
- Se firma la venta del inmueble
- El banco confirma la quita y se firma el acuerdo
- El tribunal emite sentencia definitiva
- El cliente decide no continuar con el proceso

Casos que "se duermen": crear categoria "EN ESPERA" en el CRM. Reactivar si el cliente contacta o si detectan cambios en el estado del procedimiento judicial.

Cuando el caso cierra negativamente (no se pudo salvar la vivienda): Mariano hace una llamada personal. El sistema prepara el mensaje de seguimiento post-cierre para ver si el cliente necesita ayuda con la segunda oportunidad (nueva vivienda, reorganizacion financiera).

---

## feedback-collector

**VACIO — propuesta:**

Encuesta de 3 preguntas a enviar 5-7 dias despues del cierre:
1. "Del 1 al 10, ¿como valoraria la atencion recibida?"
2. "¿Hay algo que hubiese podido hacerse mejor?"
3. "¿Nos recomendaria a alguien en una situacion similar?" (si: pedir resena Google o referido)

Para testimonios en contenido: siempre con permiso explicito del cliente. Anonimizar datos si el cliente lo prefiere.

---

# BLOQUE 9 — Operaciones y Reporting

---

## ops-director / weekly-reporter

**VALIDADO**

Informe semanal: lunes a las 8 AM.
Incluir en el informe: tareas pendientes que el sistema esta esperando que haga Mariano.

Metricas que el sistema debe trackear desde el primer dia (aunque no haya datos todavia):
- Leads entrantes por canal (Google / Meta / TikTok / referido)
- Tasa de cualificacion (leads totales vs. leads que pasan a llamada)
- Tasa de cierre (llamadas vs. clientes activos)
- Casos cerrados positivos / negativos
- Tiempo medio de cada fase del pipeline

---

## channel-performance

**MEJORAR — budget inicial pequeno, hay que maximizarlo**

Mariano tenia pensado 300€ el primer mes para ads en total.

**Recomendacion para Lucas:** Con 300€ es dificil tener datos estadisticamente significativos. Sugerencia: concentrar todo en un canal (Meta) el primer mes para aprender rapidamente. Dividir entre dos canales diluye el aprendizaje.

---

## revenue-tracker

**MEJORAR — modelo de honorarios**

Modelo habitual: tarifa fija. Varia segun el caso.
Mix de fijo + exito posible dependiendo del caso.

**VACIO — preguntas sin responder que hay que definir antes de construir:**
- Cuanto cobra Mariano por cada tipo de servicio (gestion, exito)?
- Hay honorarios anticipados o todo a resultado?
- Cuando cobran: al firmar, al resultado, por fases?
Estas decisiones de negocio son criticas para que el agente funcione. Mariano debe definirlas.

---

# PUNTOS DE LUCAS (AGENTES.pdf) — RESUMEN DE ACCIONES

| Punto Lucas | Descripcion | Accion |
|-------------|-------------|--------|
| 1 | Avatar como animacion | Agente de creacion de avatar para TikTok. Probar vs. cara real. |
| 2 | Imagen y video en Freepik | Agente especialista en Freepik para creatividades de anuncios |
| 3 | Agente editor de video | Buscar o construir agente editor para postproduccion |
| 4 | Agente para web ultra profesional | Agente que construya/mantenga la web de Centrum |
| 5 | TOFU-MOFU-BOFU | Mapear el funnel de captacion en 3 fases y asignar agentes a cada una |
| 6 | Agente especifico para ads | Un agente dedicado exclusivamente a gestionar campanas de pago |
| 7 | Cuantos mas videos mejor | Aumentar cadencia de contenido progresivamente |
| 8 | Agente comercial para comentarios de videos | Detectar palabras clave en comentarios → DM automatico para iniciar captacion |
| 9 | Auto-responder a todas las redes | Expandir auto-responder a Instagram DM, TikTok, Facebook (estudiar referentes) |
| 10 | Clonacion de voz de Mariano | Investigar IA de voz gratuita. Usar para comunicaciones cuando faltan docs o hay errores. Alternativa: voz femenina |
| 11 | Confirmacion antes de avisar docs | doc-director pide OK a Mariano antes de enviar aviso de documentacion al cliente |
| 12 | App/sistema de seguimiento post-abogado | CRM compartido con acceso restringido al abogado. Sistema notifica a Mariano cambios sin molestar al abogado |

---

# RESUMEN EJECUTIVO — LO MAS IMPORTANTE PARA LUCAS

## 5 correcciones criticas antes de construir

1. **market-watcher** tiene el enfoque equivocado. No es sobre Euribor. Es sobre nuevos procedimientos de ejecucion hipotecaria. Redefinir completamente.

2. **El formulario web necesita estas preguntas especificas** que Mariano definio: banco, avalistas, solucion del banco, cuantas cuotas. Sin esto el form-analyzer no puede hacer su trabajo.

3. **lead-classifier necesita una 5a categoria**: Entrega de posesion voluntaria a cambio de pago unico. Es un tipo de cliente con logica propia.

4. **legal-language-checker es un agente de seguridad critico**: Nada con contenido de asesoramiento, plazos judiciales o promesas puede salir por WhatsApp ni email. Solo en persona o en papel.

5. **La documentacion se pide DESPUES de la primera llamada y definicion de viabilidad**, no antes. El flujo de doc-director debe reflejar esto.

## 3 insights de negocio que deben estar en la memoria del sistema

1. **La deuda casi siempre esta inflada** por intereses de demora abusivos. Buscar activamente en todos los casos.

2. **Nunca hay un caso sin salida** — en el peor caso, se gana tiempo (2-10 anos), el cliente ahorra sin pagar ni cuota ni alquiler, y luego puede comprar otra vivienda limpio de deudas.

3. **El mercado esta virgen** — no hay ningun competidor ofreciendo el servicio triple integrado (broker + abogado + inmobiliaria). Centrum tiene el espacio libre.

## Bloques mas urgentes de construir (por impacto en captacion)

1. **Bloque 2 (Conversion Web)** — Formulario + clasificador + auto-responder. Sin esto no hay captacion.
2. **Bloque 1 (Contenido)** — Sistema de produccion en batch + gestion de multiples cuentas (modelo Briones). Sin esto no hay trafico.
3. **Bloque 3 (Primer Contacto)** — call-prep + ficha-builder. Sin esto Mariano va a ciegas a las llamadas.
4. **Bloque 5 (Analisis)** — clause-detector + debt-analyzer + property-valuator. El nucleo del valor diferencial de Centrum.
5. **Bloque 6 (Soluciones)** — solution-matcher con las 8 estrategias codificadas. La entrega de valor al cliente.

## Modelo de contenido: estrategia de saturacion (referencia Beltran Briones)

El modelo Briones es el referente. Beltran Briones (inmobiliaria en Buenos Aires) consiguio 3.000-4.000 consultas semanales de contenido organico usando este sistema:
- Subir el maximo de videos posible sin que cancelen las cuentas
- Multiples cuentas (hasta 10+) con variaciones del mismo contenido
- 90% contenido educativo, 10% CTA
- Medir cuales funcionan → repetir variaciones de los ganadores
- Escalar progresivamente abriendo nuevas cuentas

Para Centrum: arrancar con 2 cuentas TikTok + 2 Instagram (4-8 videos/dia), escalar a 10+ cuentas y 15-20 videos/dia en 6 meses. El content-director gestiona la produccion en batch, la distribucion entre cuentas y el tracking de rendimiento.

---

*Documento generado el 09/04/2026 | Analisis experto sobre Briefing de Agentes completo + AGENTES.pdf de Lucas | Uso interno — Confidencial*
