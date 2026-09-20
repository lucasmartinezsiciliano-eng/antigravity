/**
 * Revision guiada antes de comprar un coche fuera de Espana.
 *
 * El orden importa y esta pensado para hacerse tal cual. Dos principios:
 *
 *  1. Los fraudes mas caros ocurren ANTES de comprar el billete de avion (la
 *     senal, el transportista falso, la cuenta de un tercero, el coche que no
 *     existe). Por eso la primera fase es antifraude pura y va separada.
 *  2. El arranque en frio es perecedero: solo funciona una vez y solo si el
 *     motor lleva horas parado. Va ANTES que los papeles, porque media hora
 *     leyendo documentacion le da al vendedor tiempo de calentar el motor.
 *
 * - `critical: true`  -> si falla, te levantas y te vas. No se negocia.
 * - `repairCost`      -> lo que cuesta arreglarlo. Alimenta la negociacion.
 * - `weight`          -> peso en la nota final (1 normal, 2 importante, 3 grave).
 *
 * Contenido contrastado en:
 *   obsidian/Coches/Verificación — VIN, Fraude y Fuentes Oficiales.md
 *   obsidian/Coches/Usuarios — Necesidades y Dolor.md
 */

import type { CheckItem, CheckPhase, CountryCode, Dossier, Fuel, Gearbox } from "./types";

/** Paises de origen habituales, para los puntos que aplican a "todos menos uno". */
const UE: CountryCode[] = ["DE", "FR", "IT", "NL", "BE", "AT", "PT", "PL", "LU"];
const SIN_ALEMANIA = UE.filter((c) => c !== "DE");

export const PHASES: CheckPhase[] = [
  {
    id: "antifraude",
    title: "Que el vendedor sea real",
    subtitle:
      "Los timos que mas dinero se llevan ocurren aqui, antes de comprar el billete. Ninguno de estos puntos se negocia.",
    place: "Desde casa, antes de nada",
    items: [
      {
        id: "vin-anuncio",
        label: "Tienes el VIN completo (17 caracteres)",
        detail:
          "Son 17 caracteres y nunca llevan I, O ni Q. Si el vendedor se niega a darlo, ya tienes tu respuesta: no hay ninguna razon honesta para ocultarlo. Aviso: que el digito de control no valide es normal en coches europeos, no lo uses para descartar.",
        critical: true,
        weight: 3,
      },
      {
        id: "titular",
        label: "El vendedor es el titular que figura en los papeles",
        detail:
          "Pide foto del permiso de circulacion y de su documento de identidad, y que coincidan. Si vende 'para un amigo' o es un intermediario sin factura, el riesgo se dispara.",
        critical: true,
        weight: 3,
      },
      {
        id: "anuncio-legitimo",
        label: "El anuncio no tiene las senales del clonado",
        detail:
          "Precio muy por debajo de mercado, vendedor sin telefono que solo escribe por email, prisa artificial, fotos que aparecen en otros anuncios, peticion de reserva. Busca las fotos por imagen inversa: si salen en diez anuncios mas, el coche no existe.",
        weight: 3,
      },
      {
        id: "sin-senal",
        label: "No has pagado ni un euro de senal, y no lo vas a pagar",
        detail:
          "Ni 100 euros 'para reservarlo'. No existe ninguna razon legitima para adelantar dinero a alguien cuyo coche no has visto. Hay redes desarticuladas con cientos de victimas que funcionaban exactamente asi.",
        critical: true,
        weight: 3,
      },
      {
        id: "transportista-propio",
        label: "El transporte lo eliges y lo contratas tu, despues de tener el coche",
        detail:
          "Si el vendedor propone la agencia de transporte, la agencia no existe: es el timo del coche fantasma. Pagas el transporte, el coche nunca sale y el vendedor desaparece.",
        critical: true,
        weight: 3,
      },
      {
        id: "cuenta-titular",
        label: "La cuenta del pago es del titular y del mismo pais del coche",
        detail:
          "Un IBAN de otro pais o a nombre de un tercero es una senal de estafa casi definitiva. Nada de Bizum, cripto ni servicios de custodia que proponga el vendedor.",
        critical: true,
        weight: 3,
      },
      {
        id: "origen-usa",
        label: "El VIN no empieza por 1, 2, 3, 4 ni 5",
        detail:
          "Esos prefijos son de fabricacion para Norteamerica. En un coche que se vende en Europa suele significar que viene de una subasta de aseguradora estadounidense, reparado y revendido. Si es el caso, un informe de VIN con fotos de subasta es obligatorio.",
        critical: true,
        weight: 3,
      },
    ],
  },
  {
    id: "antes",
    title: "Que el coche merezca el viaje",
    subtitle:
      "Todo esto se hace por mensaje desde el sofa. Un billete de avion cuesta menos que un viaje tirado a la basura.",
    place: "Desde casa",
    items: [
      // --- Fuente oficial por pais: la mejor herramienta y casi siempre gratis
      {
        id: "fuente-oficial-nl",
        label: "Consultado el RDW en ovi.rdw.nl con la matricula",
        detail:
          "El mejor registro publico de Europa y es gratis: da kilometros oficiales con marca de 'ilogico', numero de titulares, si esta robado, la APK y hasta el CO2. No necesitas permiso del vendedor, solo la matricula. Mira tambien si el coche ya era importado a Holanda.",
        onlyCountry: ["NL"],
        critical: true,
        weight: 3,
      },
      {
        id: "fuente-oficial-fr",
        label: "Pedido el informe HistoVec completo al vendedor",
        detail:
          "Gratis en histovec.interieur.gouv.fr y lo genera el titular en un minuto. Trae siniestros con peritaje, controles tecnicos e historial de kilometros: mucho mas que el certificat de non-gage. Si se niega a generarlo, pregúntate por que.",
        onlyCountry: ["FR"],
        critical: true,
        weight: 3,
      },
      {
        id: "fuente-oficial-pl",
        label: "Consultado historiapojazdu.gov.pl",
        detail:
          "Gratis y con version en ingles. Necesitas matricula, VIN y la fecha de primera matriculacion: pidele esa fecha al vendedor, sin ella la consulta no funciona.",
        onlyCountry: ["PL"],
        critical: true,
        weight: 3,
      },
      {
        id: "fuente-oficial-be",
        label: "El vendedor te ha dado el Car-Pass",
        detail:
          "Es obligatorio por ley en toda venta en Belgica, tambien entre particulares. Cuesta 11,10 euros, lo saca el vendedor y vale 2 meses. Si no te lo da, esta incumpliendo la ley: es la mejor herramienta antifraude de kilometros de Europa.",
        onlyCountry: ["BE"],
        critical: true,
        weight: 3,
      },
      {
        id: "fuente-oficial-at",
        label: "Consultado kfzgutachten.at",
        detail:
          "Cuesta 0,99 euros y da los defectos y los kilometros anotados en cada revision §57a. Necesitas la fecha de primera matriculacion.",
        onlyCountry: ["AT"],
        weight: 3,
      },
      {
        id: "fuente-oficial-it",
        label: "El vendedor te ha enviado la visura del PRA",
        detail:
          "Cuesta 6 euros pero hace falta identidad digital italiana, asi que tu no puedes sacarla: tienes que exigirsela al vendedor. Es lo que demuestra que no hay fermo amministrativo ni cargas.",
        onlyCountry: ["IT"],
        critical: true,
        weight: 3,
      },
      {
        id: "fuente-oficial-de",
        label: "Tienes los TRES ultimos informes de la HU (TUV, DEKRA)",
        detail:
          "En Alemania no hay registro publico: el del KBA esta cerrado, y la proteccion de datos alemana deja los informes de pago practicamente ciegos. Los informes de la HU llevan el kilometraje anotado y son literalmente la unica prueba de kilometros que existe. Uno solo no vale: pide tres.",
        onlyCountry: ["DE"],
        critical: true,
        weight: 3,
      },
      {
        id: "informe-vin",
        label: "Informe de historial por VIN pedido por ti",
        detail:
          "carVertical, autoDNA o CARFAX, entre 16 y 40 euros. Dos avisos que cambian como se lee: un apartado de danos VACIO significa 'sin datos', no 'sin danos'; y en Alemania salen casi ciegos por proteccion de datos. Donde se gana el dinero es en coches con vida en varios paises o con sospecha de origen estadounidense, porque traen fotos de subasta. Un PDF que te mande el vendedor no vale: circulan falsificaciones.",
        weight: 2,
      },
      {
        id: "km-coherentes",
        label: "Los kilometros cuadran tramo a tramo, no solo de media",
        detail:
          "No basta la media anual: el fraude tipico no baja el total, aplana el ultimo tramo. Necesitas al menos 3 lecturas de 3 anos distintos y mirar los km/ano ENTRE cada par. Una media de 18.000 puede esconder un tramo de 3.000 seguido de otro de 28.000. En ventas transfronterizas se manipula entre el 30% y el 50% de los cuentakilometros, frente al 5-12% en las ventas domesticas.",
        critical: true,
        weight: 3,
      },
      {
        id: "titulares-flota",
        label: "El numero de titulares y el uso anterior cuadran",
        detail:
          "Que no sea un ex-alquiler, taxi, VTC, autoescuela o flota de empresa vendido como 'de particular'. Muchos titulares en pocos anos tambien es mala senal.",
        weight: 2,
      },
      {
        id: "co2-oficial",
        label: "Sabes el CO2 oficial de ESTE coche, no del modelo",
        detail:
          "Esta en el campo V.7 del permiso de circulacion, que existe igual en toda la UE, y en el COC. Pide foto. Decide si pagas 0% o 14,75% de impuesto de matriculacion, y dos versiones del mismo modelo pueden caer en tramos distintos. Puedes contrastarlo con los campos K y D.2 contra la base de emisiones de la Agencia Europea de Medio Ambiente.",
        critical: true,
        weight: 3,
      },
      {
        id: "reformas",
        label: "El coche esta de serie, sin reformas",
        detail:
          "Llantas no originales, suspension, escape, tintados o cambios de potencia. Espana NO convalida las reformas anotadas en el TUV aleman: obligan a homologacion individual (2.500-3.000 euros) y hay reformas que directamente no se pueden homologar aqui, con lo que te quedas con un coche que no puedes matricular. Por eso es un motivo para irse y no un descuento. Pide foto del permiso completo y de cualquier anexo de homologacion. Si aun asi sigues adelante, marca la casilla de coche modificado en la calculadora de costes.",
        critical: true,
        weight: 3,
      },
      {
        id: "coc",
        label: "Tiene COC (certificado de conformidad europeo)",
        detail:
          "Cuesta entre 109 y 250 euros al fabricante y tarda de 1 a 20 dias. Con COC la homologacion en Espana es tramite de horas. Sin COC y sin homologacion europea equivalente, homologacion individual: 400-900 euros y semanas. La ficha tecnica reducida (39-90 euros) hace falta en los dos casos.",
        weight: 3,
        repairCost: 700,
      },
      {
        id: "valor-tablas",
        label: "Has mirado el valor del coche en las tablas de Hacienda",
        detail:
          "La base del impuesto de matriculacion no es lo que pagas, es el valor de las tablas de precios medios. Si el coche vale mas en tabla que lo que te cuesta, pagas impuesto sobre el valor de tabla. Es la sorpresa mas cara y mas repetida.",
        weight: 3,
      },
      {
        id: "precio-mercado",
        label: "Has comparado con el precio del mismo coche en Espana",
        detail:
          "Mismo ano, motor y kilometros en Coches.net y Milanuncios. Traer un coche cuesta entre 2.500 y 3.500 euros: si el ahorro no lo supera con holgura, no compensa el lio ni el riesgo.",
        weight: 2,
      },
      {
        id: "financiacion",
        label: "Tienes el dinero disponible, en efectivo o transferencia",
        detail:
          "Ningun banco espanol financia un coche sin matricula espanola. Si necesitas financiar la compra, la importacion no es para ti: primero pagas, luego matriculas, y solo entonces existe el coche para una financiera.",
        critical: true,
        weight: 3,
      },
      {
        id: "seguro-espana",
        label: "Una aseguradora espanola te ha confirmado que te lo asegura",
        detail:
          "Y con que matricula. La mayoria no aseguran matricula extranjera, y sin seguro no puedes moverlo.",
        weight: 2,
      },
      {
        id: "cita-itv",
        label: "Has mirado si hay cita de ITV de matriculacion en tu provincia",
        detail:
          "Las horas para inspeccion de importacion y reformas escasean. Puede alargarte semanas el coche parado en la puerta.",
        weight: 2,
      },
      {
        id: "residencia-exencion",
        label: "Si vuelves de vivir fuera: has mirado la exencion por cambio de residencia",
        detail:
          "Si has vivido fuera 12 meses y el coche es tuyo desde hace al menos 6, puedes estar exento del impuesto de matriculacion. Hay plazo para pedirla y no puedes vender el coche durante 12 meses. Es la exencion mas potente que existe y mucha gente la descubre tarde.",
        weight: 3,
      },
      {
        id: "fotos-concretas",
        label: "Te ha mandado las fotos que le has pedido",
        detail:
          "Pide en concreto: salpicadero con el motor arrancado, cuentakilometros, los cuatro bajos de puerta, hueco de la rueda de repuesto, tapon de aceite por dentro, permiso de circulacion completo y factura de la ultima revision.",
        weight: 2,
      },
      {
        id: "videollamada",
        label: "Videollamada con arranque en frio grabado",
        detail:
          "Que arranque el coche delante de ti, sin haberlo calentado antes. Escucha el primer segundo y mira el humo del escape. Sirve tambien para confirmar que el coche y el vendedor existen.",
        weight: 3,
      },
      {
        id: "inspeccion-destino-de",
        label: "Inspeccion profesional reservada en destino",
        detail:
          "En Alemania es lo unico que sustituye al historial que no existe. TUV Rheinland desde 29,90 euros, TUV Nord 89, DEKRA 49-150, ADAC 128-160. Reservala antes de viajar y que la haga alguien que no sea el vendedor.",
        onlyCountry: ["DE"],
        critical: true,
        weight: 3,
      },
      {
        id: "inspeccion-destino",
        label: "Valorada una inspeccion profesional en destino",
        detail:
          "Entre 50 y 350 euros segun pais. Si el coche pasa de 15.000 euros, sale a cuenta seguro.",
        onlyCountry: SIN_ALEMANIA,
        weight: 2,
      },
    ],
  },
  {
    id: "frio",
    title: "Arranque en frio",
    subtitle:
      "Lo PRIMERO que haces al llegar, antes incluso de sentarte a mirar papeles. Solo funciona una vez: si el motor ya esta caliente, has perdido la prueba mas reveladora del dia.",
    place: "En el sitio, motor parado toda la noche",
    items: [
      {
        id: "motor-frio",
        label: "El motor estaba frio al llegar (toca el capo)",
        detail:
          "Un motor precalentado esconde ruidos de arranque, humos y testigos. Si esta caliente, di que vuelves en dos horas. Que se moleste es informacion.",
        critical: true,
        weight: 3,
      },
      {
        id: "arranque-limpio",
        label: "Arranca a la primera, sin cascabeleo ni chirridos",
        detail:
          "Escucha los 3 primeros segundos: un repiqueteo metalico que desaparece al calentar suele ser cadena de distribucion estirada. En un TSI o un N47 eso son entre 1.500 y 2.500 euros.",
        weight: 3,
        repairCost: 1800,
      },
      {
        id: "humo-escape",
        label: "Sin humo azul, blanco denso ni negro al arrancar",
        detail:
          "Azul = quema aceite (segmentos o turbo). Blanco denso que no se va = junta de culata. Negro = inyeccion. Cualquiera de los tres es un no.",
        critical: true,
        weight: 3,
      },
      {
        id: "testigos",
        label: "Todos los testigos se encienden y se apagan",
        detail:
          "Al dar contacto deben encenderse TODOS (airbag, ABS, ESP, motor) y apagarse despues. Si alguno no llega a encenderse, le han quitado la bombilla para esconder una averia. Es el truco mas viejo que existe.",
        critical: true,
        weight: 3,
      },
      {
        id: "ralenti",
        label: "Ralenti estable, sin vibraciones raras",
        weight: 2,
        repairCost: 400,
      },
    ],
  },
  {
    id: "documentos",
    title: "Papeles",
    subtitle: "Con el arranque en frio ya comprobado. Sin papeles no hay compra, por bien que este el coche.",
    place: "En mano, delante del vendedor",
    items: [
      {
        id: "doc-de-1",
        label: "Zulassungsbescheinigung Teil I (Fahrzeugschein)",
        detail: "El permiso de circulacion aleman. Comprueba que el VIN coincide con el del coche.",
        onlyCountry: ["DE"],
        critical: true,
        weight: 3,
      },
      {
        id: "doc-de-2",
        label: "Zulassungsbescheinigung Teil II (Fahrzeugbrief) ORIGINAL",
        detail:
          "Es el titulo de propiedad. Si esta en un banco porque el coche tiene financiacion viva, no puedes matricularlo en Espana. Sin el Teil II original en la mano no pagues nada.",
        onlyCountry: ["DE"],
        critical: true,
        weight: 3,
      },
      {
        id: "contrato-agencia",
        label: "El contrato no es un Agenturgeschaft encubierto",
        detail:
          "Si pone 'Verkauf im Kundenauftrag' o 'Agenturgeschaft', el concesionario vende en nombre de un particular y con eso elimina toda la garantia. Tampoco firmes que compras 'als Gewerbetreibender'. Senal para detectarlo: si negocia el precio sin consultar al propietario, la agencia no es legitima y la garantia si te cubre.",
        onlyCountry: ["DE", "AT"],
        critical: true,
        weight: 3,
      },
      {
        id: "doc-fr-cg",
        label: "Carte grise a nombre del vendedor, barrada y firmada",
        detail: "Debe poner 'Vendu le' con fecha, hora y firma. Sin eso no puedes matricular en Espana.",
        onlyCountry: ["FR"],
        critical: true,
        weight: 3,
      },
      {
        id: "doc-fr-nongage",
        label: "Certificat de situation administrative de menos de 15 dias",
        detail:
          "Certifica que no hay cargas, embargos ni oposicion a la venta. Es gratis. Cubre solo las cargas: el historial entero esta en el informe HistoVec, que tambien debes pedirle.",
        onlyCountry: ["FR"],
        critical: true,
        weight: 3,
      },
      {
        id: "doc-fr-ct",
        label: "Controle technique de menos de 6 meses",
        detail: "Obligatorio para vender en Francia. Lee los defectos anotados, no solo el resultado.",
        onlyCountry: ["FR"],
        weight: 2,
      },
      {
        id: "doc-it",
        label: "Carta di circolazione + Certificato di Proprieta",
        onlyCountry: ["IT"],
        critical: true,
        weight: 3,
      },
      {
        id: "doc-nl",
        label: "Kentekenbewijs + codigo de traspaso (tenaamstellingscode)",
        detail: "Sin ese codigo no se puede hacer la exportacion en el RDW.",
        onlyCountry: ["NL"],
        critical: true,
        weight: 3,
      },
      {
        id: "doc-be",
        label: "Certificat d'immatriculation + certificat de conformite",
        onlyCountry: ["BE"],
        critical: true,
        weight: 3,
      },
      {
        id: "doc-pt",
        label: "DUA (Documento Unico Automovel) + IUC pagado",
        onlyCountry: ["PT"],
        critical: true,
        weight: 3,
      },
      {
        id: "doc-pl",
        label: "Dowod rejestracyjny + karta pojazdu",
        onlyCountry: ["PL"],
        critical: true,
        weight: 3,
      },
      {
        id: "doc-at",
        label: "Zulassungsschein + informe §57a (Pickerl)",
        onlyCountry: ["AT"],
        critical: true,
        weight: 3,
      },
      {
        id: "vin-multiples-puntos",
        label: "El VIN coincide en los TRES sitios y con los papeles",
        detail:
          "Salpicadero (visible desde fuera del parabrisas), vano motor y etiqueta del marco de la puerta. Busca punzonado desigual, tipografia distinta, remaches nuevos o pintura alrededor: es la firma de un coche robado, clonado o reconstruido de dos mitades.",
        critical: true,
        weight: 3,
      },
      {
        id: "sin-cargas",
        label: "Sin financiacion, reserva de dominio ni embargos",
        detail:
          "Cada pais lo prueba de una forma: Alemania con el Teil II original en mano, Francia con el certificat de situation administrative, Italia con la visura del PRA, Holanda con la consulta del RDW, Polonia con historiapojazdu. Exige el documento concreto, no la palabra del vendedor.",
        critical: true,
        weight: 3,
      },
      {
        id: "libro-mantenimiento",
        label: "Libro de mantenimiento sellado o facturas de taller",
        detail:
          "En Alemania se llama Scheckheft. Sin historial, descuenta al menos 1.000 euros: no sabes si la distribucion esta hecha.",
        weight: 3,
        repairCost: 1000,
      },
      {
        id: "historial-para-reventa",
        label: "Te llevas copia de TODO el historial de origen",
        detail:
          "El historial de la DGT espanola empieza de cero al matricular: accidentes, kilometros y uso anterior desaparecen. Esos papeles seran tu unico argumento el dia que vendas el coche.",
        weight: 2,
      },
      {
        id: "dos-llaves",
        label: "Tiene las dos llaves",
        detail: "Una llave keyless de premium aleman cuesta entre 300 y 500 euros codificada.",
        weight: 1,
        repairCost: 350,
      },
    ],
  },
  {
    id: "exterior",
    title: "Chapa y pintura",
    subtitle: "Con luz de dia y el coche seco. Si esta mojado no lo mires: la chapa engana.",
    place: "Fuera, dando una vuelta alrededor",
    items: [
      {
        id: "medidor-pintura",
        label: "Medidor de espesor: sin desviaciones respecto a la linea base",
        detail:
          "No busques un numero absoluto, busca diferencias. Fija la linea base midiendo techo y pilares (zonas que casi nunca se repintan) y compara el resto: el doble o el triple = repintado, mas de 500 micras = masilla, mas de 700 = reparacion fuera de norma. Necesitas un medidor Fe y no-Fe: medio coche premium es de aluminio y con uno magnetico barato no mides nada. Los paragolpes de plastico no se pueden medir.",
        weight: 3,
        repairCost: 800,
      },
      {
        id: "holguras",
        label: "Holguras de puertas, capo y porton iguales a ambos lados",
        detail:
          "Una separacion mayor en un lado que en otro significa golpe fuerte con tiron de chasis.",
        critical: true,
        weight: 3,
      },
      {
        id: "tornillos",
        label: "Tornillos de aletas, capo y bisagras sin marcas de llave",
        detail: "Si estan redondeados o repintados, esa pieza se ha desmontado.",
        weight: 2,
      },
      {
        id: "cristales",
        label: "Todos los cristales son de la misma marca y ano",
        detail:
          "Cada luna lleva grabado el fabricante y una fecha. Si una es de otra marca o de otro ano, la han cambiado: busca por que.",
        weight: 2,
      },
      {
        id: "oxido",
        label: "Sin oxido en bajos de puerta, pasos de rueda y faldones",
        detail:
          "Critico en coches del norte de Alemania, Holanda y Belgica por la sal del invierno. Pasa un iman: donde no se pega, hay masilla.",
        weight: 3,
        repairCost: 900,
      },
      {
        id: "granizo",
        label: "Sin marcas de granizo reparado en techo, capo y porton",
        detail:
          "Se mira con luz rasante y el coche seco. El medidor de pintura NO lo detecta, porque el granizo se repara desabollando sin pintar. Es muy comun en el sur de Alemania y Austria.",
        onlyCountry: ["DE", "AT"],
        weight: 2,
        repairCost: 700,
      },
      {
        id: "neumaticos",
        label: "Neumaticos: misma marca por eje, dibujo > 3 mm, DOT reciente",
        detail:
          "El codigo DOT da semana y ano. Mas de 6 anos hay que cambiarlos aunque tengan dibujo, y un juego de cuatro en 18 o 19 pulgadas premium son 600-900 euros. Desgaste desigual = direccion o amortiguadores.",
        weight: 2,
        repairCost: 700,
      },
      {
        id: "bajos",
        label: "Has mirado los bajos (con linterna o subido a un bordillo)",
        detail: "Busca goteos, carter golpeado, protector partido y soldaduras que no sean de fabrica.",
        weight: 3,
        repairCost: 600,
      },
      {
        id: "faros",
        label: "Faros sin condensacion ni fijaciones rotas",
        detail: "Un faro LED o matricial de un aleman premium pasa facil de 1.500 euros.",
        weight: 2,
        repairCost: 1300,
      },
    ],
  },
  {
    id: "interior",
    title: "Interior y electronica",
    subtitle: "El desgaste del interior es el detector de mentiras del cuentakilometros.",
    place: "Sentado dentro, con calma",
    items: [
      {
        id: "desgaste-coherente",
        label: "Volante, pomo, pedales y asiento acordes a los kilometros",
        detail:
          "Un volante pulido y unos pedales con la goma gastada no son de 80.000 km. Mira el brillo del cuero del asiento del conductor y el desgaste del reposapies, que casi nadie cambia.",
        critical: true,
        weight: 3,
      },
      {
        id: "vin-obd",
        label: "El VIN que devuelve la centralita por OBD coincide con el del chasis",
        detail:
          "Treinta segundos con un lector de 15 euros y casi nadie lo hace. Si no coinciden, el cuadro de instrumentos esta cambiado (adios al kilometraje) o el coche esta clonado.",
        critical: true,
        weight: 3,
      },
      {
        id: "monitores-emisiones",
        label: "Monitores de emisiones en 'ready', no en 'not ready'",
        detail:
          "Son hasta once autodiagnosticos que el coche completa conduciendo. Si estan incompletos y el coche tiene muchos kilometros, la memoria de averias se borro hace unas horas. Es la prueba de que han limpiado algo.",
        critical: true,
        weight: 3,
      },
      {
        id: "obd",
        label: "Lectura OBD hecha, sin codigos activos",
        detail:
          "Un lector Bluetooth de 15 euros lee el motor, pero NO lee ABS, airbag ni cambio: para eso hace falta VCDS, ODIS, ISTA o XENTRY, o sea taller o perito. Leer el kilometraje de varias centralitas (que es como se caza de verdad un cuentakilometros trucado) tambien necesita ese equipo.",
        weight: 3,
      },
      {
        id: "electronica",
        label: "Elevalunas, techo, climatizador, camara y pantalla funcionan",
        detail: "Pruebalo todo, uno por uno. El aire tiene que enfriar de verdad, no soplar fresco.",
        weight: 2,
        repairCost: 400,
      },
      {
        id: "humedad",
        label: "Sin senales de inundacion ni humedad",
        detail:
          "Levanta la alfombrilla y toca la moqueta del copiloto y del maletero, bajo la rueda de repuesto. Busca oxido en la tornilleria y los railes de los asientos, barro fino en el hueco de la rueda, condensacion en relojes y faros, y exceso de ambientador tapando el olor. Un coche inundado da problemas electricos para siempre.",
        critical: true,
        weight: 3,
      },
      {
        id: "cinturones",
        label: "Cinturones salen enteros, sin manchas ni fecha rara",
        detail: "Llevan fecha. Si son posteriores al coche, hubo un accidente con airbags.",
        weight: 2,
      },
      {
        id: "airbag-etiquetas",
        label: "Tapas de airbag sin holguras ni tornillos a la vista",
        detail:
          "Un airbag mal repuesto o directamente vacio es un peligro mortal y no sale en ningun informe.",
        critical: true,
        weight: 3,
      },
    ],
  },
  {
    id: "mecanica",
    title: "Motor, fluidos y transmision",
    subtitle: "Con el motor ya templado. Lo que se ve aqui no sale en ningun anuncio.",
    place: "Capo abierto",
    items: [
      {
        id: "aceite",
        label: "Aceite con nivel y color correctos, sin espuma ni lodos",
        detail:
          "Abre el tapon de llenado y mira por dentro: una pasta beige tipo mayonesa es agua mezclada con aceite, o sea junta de culata.",
        critical: true,
        weight: 3,
      },
      {
        id: "refrigerante",
        label: "Refrigerante limpio, sin manchas de aceite ni restos marrones",
        weight: 3,
        repairCost: 700,
      },
      {
        id: "fugas",
        label: "Sin fugas en motor, caja de cambios ni amortiguadores",
        detail: "Un motor sospechosamente limpio y recien lavado tambien es una senal.",
        weight: 3,
        repairCost: 600,
      },
      {
        id: "distribucion",
        label: "Distribucion hecha (con factura) o dentro de plazo",
        detail:
          "Correa: cada 120.000-160.000 km o 5-7 anos. Cambiarla cuesta 600-1.200 euros; que se rompa cuesta el motor entero. Sin factura, asume que NO esta hecha.",
        weight: 3,
        repairCost: 900,
      },
      {
        id: "dpf-egr",
        label: "Filtro de particulas y EGR sin averias",
        detail:
          "Pregunta si el coche se usaba en ciudad. Un diesel moderno de uso urbano es una bomba de relojeria: DPF nuevo son 1.200-2.000 euros.",
        onlyFuel: ["diesel"],
        weight: 3,
        repairCost: 1400,
      },
      {
        id: "dpf-contadores",
        label: "Contadores de regeneracion del DPF leidos por OBD",
        detail:
          "Mira cuantas regeneraciones lleva y la distancia desde la ultima. Regeneraciones muy frecuentes significan filtro al limite y factura a la vuelta de la esquina.",
        onlyFuel: ["diesel"],
        weight: 3,
        repairCost: 1400,
      },
      {
        id: "dpf-vaciado",
        label: "DPF y catalizador presentes y no vaciados",
        detail:
          "Sin remapeo que oculte el error. Un coche con el filtro vaciado es motivo de rechazo directo en la ITV de importacion: te quedas con un coche que no puedes matricular.",
        onlyFuel: ["diesel"],
        critical: true,
        weight: 3,
      },
      {
        id: "adblue",
        label: "Sistema AdBlue sin errores ni cuenta atras",
        detail:
          "Un inyector o una bomba de AdBlue son 800-1.500 euros y dejan el coche sin arrancar cuando se agota el contador.",
        onlyFuel: ["diesel"],
        weight: 2,
        repairCost: 1000,
      },
      {
        id: "bateria-hv",
        label: "Salud de la bateria (SOH) medida, no la autonomia del display",
        detail:
          "Pide un informe de bateria del servicio oficial. Menos del 85% en un coche de menos de 6 anos es mala senal.",
        onlyFuel: ["electrico", "phev"],
        critical: true,
        weight: 3,
      },
      {
        id: "garantia-bateria-es",
        label: "La garantia de bateria es transferible y valida en Espana",
        detail:
          "Confirmalo con la marca, no con el vendedor. Comprueba tambien que no haya campanas de revision pendientes.",
        onlyFuel: ["electrico", "phev"],
        weight: 2,
      },
      {
        id: "cable-tipo2",
        label: "Incluye cable de carga Tipo 2",
        detail: "No solo el Schuko de emergencia. Un cable Tipo 2 en condiciones son 250-400 euros.",
        onlyFuel: ["electrico", "phev"],
        weight: 1,
        repairCost: 350,
      },
      {
        id: "embrague",
        label: "Embrague agarra alto y sin patinar",
        detail:
          "En 5a a 1.500 rpm pisa a fondo: si las vueltas suben y el coche no acelera, esta acabado.",
        onlyGearbox: ["manual"],
        weight: 3,
        repairCost: 900,
      },
      {
        id: "dsg",
        label: "Cambio automatico suave, sin tirones ni retardos",
        detail:
          "Los DSG en seco y algunos CVT son el punto debil. Prueba parado: D-R-D con el pie en el freno, sin golpes secos. Mecatronica: 1.500-2.500 euros.",
        onlyGearbox: ["automatico"],
        weight: 3,
        repairCost: 1800,
      },
      {
        id: "turbo",
        label: "Turbo sin silbidos agudos ni retraso de respuesta",
        weight: 2,
        repairCost: 1200,
      },
    ],
  },
  {
    id: "prueba",
    title: "Prueba en carretera",
    subtitle: "Minimo 20 minutos y con autovia. Si no te dejan conducirlo, se acabo la visita.",
    place: "Al volante, radio apagada y ventanilla bajada",
    items: [
      {
        id: "te-dejan-conducir",
        label: "Te dejan conducirlo tu, solo y por donde tu quieras",
        critical: true,
        weight: 3,
      },
      {
        id: "direccion-recta",
        label: "Va recto soltando el volante un instante",
        detail: "Si se va a un lado: alineacion, neumaticos o chasis torcido por un golpe.",
        weight: 3,
        repairCost: 400,
      },
      {
        id: "frenada",
        label: "Frenada firme, sin vibraciones en el volante ni ruidos",
        detail: "Vibracion al frenar = discos alabeados, 300-600 euros. Pruebalo tambien fuerte.",
        weight: 2,
        repairCost: 450,
      },
      {
        id: "abs",
        label: "El ABS entra sin problemas en una frenada de emergencia",
        detail: "Buscad un sitio despejado. Debes notar el pedal pulsar bajo el pie.",
        weight: 2,
      },
      {
        id: "suspension",
        label: "Sin golpes secos en badenes ni carraspeo en curvas",
        weight: 2,
        repairCost: 500,
      },
      {
        id: "autovia",
        label: "Probado a mas de 120 km/h, estable y sin vibracion",
        detail:
          "Muchos defectos (rodamientos, equilibrado, alineacion, aerodinamica tras un golpe) solo salen ahi.",
        weight: 3,
      },
      {
        id: "temperatura",
        label: "La temperatura del motor se mantiene estable",
        detail: "Vigila la aguja en autovia y luego parado con el ventilador en marcha.",
        critical: true,
        weight: 3,
      },
      {
        id: "marcha-atras",
        label: "Todas las marchas entran limpias, incluida la marcha atras",
        weight: 2,
        repairCost: 800,
      },
      {
        id: "testigos-tras",
        label: "Al terminar no se ha encendido ningun testigo",
        critical: true,
        weight: 3,
      },
    ],
  },
  {
    id: "cierre",
    title: "Cerrar la compra",
    subtitle: "Ya has decidido que si. Ahora toca no meter la pata en la parte facil.",
    place: "Mesa, cafe y papeles",
    items: [
      {
        id: "contrato",
        label: "Contrato de compraventa bilingue firmado por duplicado",
        detail:
          "Datos completos de ambos, VIN, kilometros, precio, fecha y la frase de que se vende libre de cargas. En Alemania usa el modelo del ADAC.",
        critical: true,
        weight: 3,
      },
      {
        id: "factura-iva",
        label: "Si compras a profesional: factura con el regimen de IVA claro",
        detail:
          "Debe decir si aplica el regimen de bienes usados (REBU) o si es una entrega intracomunitaria exenta. De eso depende que pagues o no un 21% extra aqui.",
        weight: 3,
      },
      {
        id: "pago-seguro",
        label: "Pago por transferencia, con el coche delante",
        detail:
          "Lo ideal: transferencia desde la oficina del banco del vendedor, con el dinero y las llaves cambiando de manos a la vez.",
        critical: true,
        weight: 3,
      },
      {
        id: "informe-carfax-propio",
        label: "El informe de historial lo has pedido tu con el VIN",
        detail: "Un PDF que te manda el vendedor no vale: circulan falsificaciones de informes.",
        weight: 2,
      },
      {
        id: "baja-origen",
        label: "Baja o exportacion tramitada en el pais de origen",
        detail:
          "Si no se hace, las multas y los impuestos del pais de origen te seguiran llegando al titular anterior, y tu coche seguira figurando alli.",
        critical: true,
        weight: 3,
      },
      {
        id: "placas-correctas",
        label: "Si vuelves conduciendo, llevas las placas correctas",
        detail:
          "En Alemania necesitas Ausfuhrkennzeichen (la roja, con validez internacional y seguro para salir del pais), NO Kurzzeitkennzeichen (la amarilla, 5 dias y sin validez fuera). Confundirlas te deja tirado en la frontera.",
        onlyCountry: ["DE"],
        critical: true,
        weight: 3,
      },
      {
        id: "seguro-traslado",
        label: "Seguro de traslado contratado antes de arrancar",
        weight: 3,
      },
      {
        id: "traduccion-jurada",
        label: "Sabes que documentos hay que traducir y cuanto cuesta",
        detail: "Unos 150 euros de media. Preguntalo en la gestoria antes, no despues.",
        weight: 1,
        repairCost: 150,
      },
      {
        id: "zbe",
        label: "Si vives en zona de bajas emisiones, sabes que no puedes entrar hasta matricularlo",
        detail:
          "Sin distintivo ambiental espanol no puedes circular por las ZBE, y desde 2026 se multa automaticamente en muchisimos municipios. Comprueba tambien que etiqueta le va a tocar.",
        weight: 2,
      },
      {
        id: "tramites-es",
        label: "Tienes clara la lista de tramites en Espana",
        detail:
          "1) Modelo 576 del impuesto de matriculacion, que se autoliquida ANTES de matricular. 2) ITV de importacion y ficha tecnica. 3) IVTM en tu ayuntamiento. 4) Matriculacion en la DGT con su tasa. En ese orden.",
        weight: 2,
      },
      {
        id: "plazo-30-dias",
        label: "Sabes que tienes 30 dias naturales para matricularlo",
        detail:
          "Se cuentan desde que empiezas a usar el coche en Espana, y son naturales, no habiles. Pasado el plazo hay recargos, y circular con matricula extranjera fuera de plazo es multa y posible inmovilizacion.",
        weight: 3,
      },
    ],
  },
];

// --- Filtrado por coche ----------------------------------------------------

export interface ChecklistContext {
  country?: CountryCode;
  fuel?: Fuel;
  gearbox?: Gearbox;
  km?: number;
  year?: number;
}

function applies(item: CheckItem, ctx: ChecklistContext): boolean {
  if (item.onlyCountry && (!ctx.country || !item.onlyCountry.includes(ctx.country))) return false;
  if (item.onlyFuel && (!ctx.fuel || !item.onlyFuel.includes(ctx.fuel))) return false;
  if (item.onlyGearbox && (!ctx.gearbox || !item.onlyGearbox.includes(ctx.gearbox))) return false;
  if (item.minKm && (ctx.km ?? 0) < item.minKm) return false;
  if (item.minAge && ctx.year && new Date().getFullYear() - ctx.year < item.minAge) return false;
  return true;
}

/** Las fases con solo los puntos que le tocan a ESTE coche. */
export function phasesFor(ctx: ChecklistContext): CheckPhase[] {
  return PHASES.map((p) => ({ ...p, items: p.items.filter((i) => applies(i, ctx)) })).filter(
    (p) => p.items.length > 0,
  );
}

export function contextFromDossier(d: Dossier): ChecklistContext {
  return {
    country: d.listing?.country ?? d.cost?.country,
    fuel: d.listing?.fuel ?? d.cost?.fuel,
    gearbox: d.listing?.gearbox,
    km: d.listing?.km ?? d.cost?.km,
    year: d.listing?.year,
  };
}

export function allItems(ctx: ChecklistContext): CheckItem[] {
  return phasesFor(ctx).flatMap((p) => p.items);
}
