/**
 * Revision guiada antes de comprar un coche fuera de Espana.
 *
 * El orden importa: esta pensado para hacerse tal cual, de arriba a abajo.
 * Lo que se puede comprobar desde casa va primero, porque un billete de avion
 * cuesta menos que un viaje tirado a la basura.
 *
 * - `critical: true`  -> si falla, te levantas y te vas. No se negocia.
 * - `repairCost`      -> lo que cuesta arreglarlo. Alimenta la negociacion.
 * - `weight`          -> cuanto pesa en la nota final (1 normal, 2 importante, 3 grave).
 */

import type { CheckItem, CheckPhase, CountryCode, Dossier, Fuel, Gearbox } from "./types";

export const PHASES: CheckPhase[] = [
  {
    id: "antes",
    title: "Antes de coger el avion",
    subtitle: "Todo esto se hace por WhatsApp desde el sofa. Si algo falla aqui, no viajes.",
    place: "Desde casa",
    items: [
      {
        id: "vin-anuncio",
        label: "Tienes el VIN completo (17 caracteres)",
        detail:
          "Pidelo por mensaje. Si el vendedor se niega a dar el numero de bastidor, ya tienes tu respuesta: no hay ninguna razon honesta para ocultarlo.",
        critical: true,
        weight: 3,
      },
      {
        id: "informe-vin",
        label: "Informe de historial por VIN pedido y sin sorpresas",
        detail:
          "carVertical, autoDNA o CarFax. 20-30 EUR. Busca: siniestros, robo, cambios de km, uso como taxi o alquiler, embargos.",
        critical: true,
        weight: 3,
      },
      {
        id: "km-coherentes",
        label: "Los km cuadran con el historial y con la edad",
        detail:
          "Media europea: 15.000-20.000 km/ano. Un aleman de 2018 con 60.000 km es raro. Contrasta con los informes de la ITV local (HU en Alemania, controle technique en Francia): llevan el km anotado en cada revision.",
        critical: true,
        weight: 3,
      },
      {
        id: "fotos-concretas",
        label: "Te ha mandado las fotos que le has pedido",
        detail:
          "Pide en concreto: salpicadero con el motor arrancado (testigos), cuentakilometros, los 4 bajos de puerta, hueco de rueda de repuesto, tapon de aceite por dentro y factura de la ultima revision.",
        weight: 2,
      },
      {
        id: "videollamada",
        label: "Videollamada con arranque en frio grabado",
        detail:
          "Que arranque el coche delante de ti por videollamada, sin haberlo calentado antes. Escucha el primer segundo y mira el humo del escape.",
        weight: 3,
        critical: false,
      },
      {
        id: "titular",
        label: "El vendedor es el titular que figura en los papeles",
        detail:
          "Pide foto del permiso de circulacion y de su DNI/Personalausweis. Si vende 'para un amigo' o es un intermediario sin factura, el riesgo se dispara.",
        critical: true,
        weight: 3,
      },
      {
        id: "coc",
        label: "Tiene COC (certificado de conformidad europeo)",
        detail:
          "Con COC la homologacion en Espana es tramite. Sin el, ficha tecnica reducida: +250 EUR y semanas de espera.",
        weight: 2,
        repairCost: 250,
      },
      {
        id: "co2-oficial",
        label: "Sabes el CO2 oficial (g/km) del coche exacto",
        detail:
          "Esta en el COC (apartado V.7) o en la ficha tecnica. Es lo que decide si pagas 0% o 14,75% de impuesto de matriculacion. No te fies del anuncio.",
        critical: true,
        weight: 3,
      },
      {
        id: "precio-mercado",
        label: "Has comparado con el precio del mismo coche en Espana",
        detail:
          "Mismo ano, motor y km en Coches.net y Milanuncios. Si el ahorro no supera los 1.500 EUR, no compensa el lio.",
        weight: 2,
      },
    ],
  },
  {
    id: "documentos",
    title: "Papeles",
    subtitle: "Lo primero al llegar, antes de mirar el coche. Sin papeles no hay compra.",
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
          "Es el titulo de propiedad. Si esta en un banco porque el coche tiene financiacion, no puedes matricularlo en Espana. Sin el Teil II original no pagues nada.",
        onlyCountry: ["DE"],
        critical: true,
        weight: 3,
      },
      {
        id: "doc-de-hu",
        label: "Informe de la ultima HU/AU (TUV, DEKRA)",
        detail:
          "Equivale a la ITV. Lleva los km anotados: es tu mejor prueba contra el maquillaje del cuentakilometros. Pide tambien los anteriores.",
        onlyCountry: ["DE"],
        weight: 3,
      },
      {
        id: "doc-fr-cg",
        label: "Carte grise a nombre del vendedor, barrada y firmada",
        detail:
          "Debe poner 'Vendu le [fecha]' con hora y firma. Sin eso no puedes matricular en Espana.",
        onlyCountry: ["FR"],
        critical: true,
        weight: 3,
      },
      {
        id: "doc-fr-nongage",
        label: "Certificat de situation administrative (non-gage) de menos de 15 dias",
        detail:
          "Certifica que el coche no tiene cargas, embargos ni oposicion a la venta. Gratis en histovec.interieur.gouv.fr. Si el vendedor no lo tiene, sacalo tu con la matricula.",
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
        label: "Carta di circolazione + Certificato di Proprieta digitale",
        detail: "Comprueba en el PRA que no hay fermo amministrativo (embargo).",
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
        label: "Certificat d'immatriculation + Certificat de conformite",
        onlyCountry: ["BE"],
        critical: true,
        weight: 3,
      },
      {
        id: "doc-pt",
        label: "DUA (Documento Unico Automovel) + comprovativo de IUC pago",
        onlyCountry: ["PT"],
        critical: true,
        weight: 3,
      },
      {
        id: "doc-pl",
        label: "Dowod rejestracyjny + karta pojazdu",
        detail:
          "En Polonia mira con lupa el historial: es el mercado con mas manipulacion de km de Europa.",
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
        id: "vin-fisico",
        label: "El VIN del chasis coincide con el de los papeles",
        detail:
          "Miralo grabado en el vano motor y en el salpicadero (visible desde fuera del parabrisas). Busca golpes, repintados o remaches raros alrededor: es la firma de un coche robado o reconstruido.",
        critical: true,
        weight: 3,
      },
      {
        id: "libro-mantenimiento",
        label: "Libro de mantenimiento sellado o facturas de taller",
        detail:
          "En Alemania se llama Scheckheft. Sin historial de mantenimiento, descuenta al menos 1.000 EUR: no sabes si la distribucion esta hecha.",
        weight: 3,
        repairCost: 1000,
      },
      {
        id: "dos-llaves",
        label: "Tiene las dos llaves",
        detail: "Una llave de repuesto con codificacion cuesta entre 150 y 400 EUR.",
        weight: 1,
        repairCost: 250,
      },
      {
        id: "sin-cargas",
        label: "Sin financiacion, reserva de dominio ni embargos",
        critical: true,
        weight: 3,
      },
    ],
  },
  {
    id: "frio",
    title: "Arranque en frio",
    subtitle:
      "Lo PRIMERO que haces al llegar. Si el motor ya esta caliente cuando llegas, es una senal en si misma: vuelve otro dia.",
    place: "En el sitio, motor parado toda la noche",
    items: [
      {
        id: "motor-frio",
        label: "El motor estaba frio al llegar (toca el capo)",
        detail:
          "Un motor precalentado esconde ruidos de arranque, humos y testigos. Si esta caliente, di que vuelves en dos horas.",
        critical: true,
        weight: 3,
      },
      {
        id: "arranque-limpio",
        label: "Arranca a la primera, sin cascabeleo ni chirridos",
        detail:
          "Escucha los 3 primeros segundos: un repiqueteo metalico que desaparece al calentar suele ser cadena de distribucion estirada. En un TSI o un N47 eso son 1.500-2.500 EUR.",
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
          "Al dar contacto deben encenderse TODOS (airbag, ABS, ESP, motor). Si alguno no se enciende, le han quitado la bombilla para esconder una averia. Es el truco mas viejo del mundo.",
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
    id: "exterior",
    title: "Chapa y pintura",
    subtitle: "Con luz de dia y el coche seco. Si llueve o esta mojado, no lo mires: la chapa engana.",
    place: "Fuera, dando una vuelta alrededor",
    items: [
      {
        id: "medidor-pintura",
        label: "Medidor de espesor de pintura: valores homogeneos",
        detail:
          "20 EUR en Amazon y es la mejor inversion de todo el viaje. Original: 80-150 micras. Mas de 250 = repintado. Mas de 500 = masilla. Mide TODAS las piezas y compara entre ellas.",
        weight: 3,
        repairCost: 800,
      },
      {
        id: "holguras",
        label: "Holguras de puertas, capo y porton iguales a ambos lados",
        detail:
          "Una separacion mayor en un lado que en otro = el coche ha tenido un golpe fuerte y le han tirado del chasis.",
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
        id: "neumaticos",
        label: "Neumaticos: misma marca por eje, dibujo > 3 mm, DOT reciente",
        detail:
          "El codigo DOT da semana y ano (ej. 3221 = semana 32 de 2021). Mas de 6 anos hay que cambiarlos aunque tengan dibujo. Desgaste desigual = direccion o amortiguadores.",
        weight: 2,
        repairCost: 500,
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
        detail: "Un faro LED o matricial de un aleman premium puede costar mas de 1.500 EUR.",
        weight: 2,
        repairCost: 900,
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
        label: "Volante, pomo, pedales y asiento acordes a los km",
        detail:
          "Un volante pulido y unos pedales con la goma gastada no son de 80.000 km. Mira tambien el brillo del cuero del asiento del conductor y el desgaste del reposapies.",
        critical: true,
        weight: 3,
      },
      {
        id: "obd",
        label: "Lectura OBD hecha, sin codigos activos ni memoria recien borrada",
        detail:
          "Un lector Bluetooth cuesta 15 EUR. Si la memoria esta vacia del todo Y el coche tiene muchos km, sospecha: la han borrado esta manana. Mira tambien la disponibilidad de los monitores de emisiones ('not ready' = borrado reciente).",
        critical: true,
        weight: 3,
      },
      {
        id: "electronica",
        label: "Elevalunas, techo, climatizador, camara y pantalla funcionan",
        detail: "Pruebalo TODO, uno por uno. El aire acondicionado tiene que enfriar de verdad, no soplar fresco.",
        weight: 2,
        repairCost: 400,
      },
      {
        id: "humedad",
        label: "Sin olor a humedad ni moqueta mojada",
        detail:
          "Levanta la alfombrilla y toca la moqueta del copiloto y del maletero (bajo la rueda de repuesto). Agua ahi = coche inundado o desagues atascados. La electronica mojada da problemas para siempre.",
        critical: true,
        weight: 3,
      },
      {
        id: "cinturones",
        label: "Cinturones salen enteros, sin manchas ni fecha rara",
        detail: "Los cinturones llevan fecha. Si son posteriores al coche, hubo un accidente con airbags.",
        weight: 2,
      },
      {
        id: "airbag-etiquetas",
        label: "Tapas de airbag sin holguras ni tornillos a la vista",
        detail: "Un airbag mal repuesto o directamente vacio es un peligro mortal y no se ve en ningun informe.",
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
          "Abre el tapon de llenado y mira por dentro: una pasta beige tipo mayonesa = agua mezclada con aceite = junta de culata.",
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
          "Correa: cada 120.000-160.000 km o 5-7 anos. Cambiarla cuesta 600-1.200 EUR. Que se rompa cuesta el motor entero. Sin factura, asume que NO esta hecha.",
        weight: 3,
        repairCost: 900,
      },
      {
        id: "dpf-egr",
        label: "Filtro de particulas y EGR sin averias (diesel)",
        detail:
          "Pregunta cuantas regeneraciones hace y si el coche se usaba en ciudad. Un diesel moderno de uso urbano es una bomba de relojeria: DPF nuevo 1.200-2.000 EUR.",
        onlyFuel: ["diesel"],
        weight: 3,
        repairCost: 1400,
      },
      {
        id: "adblue",
        label: "Sistema AdBlue sin errores ni cuenta atras",
        detail: "Un inyector o bomba de AdBlue son 800-1.500 EUR y dejan el coche sin arrancar cuando se agota el contador.",
        onlyFuel: ["diesel"],
        weight: 2,
        repairCost: 1000,
      },
      {
        id: "bateria-hv",
        label: "Salud de la bateria (SOH) medida, no solo la autonomia del display",
        detail:
          "Pide un informe de bateria (muchas marcas lo emiten en el servicio oficial). Menos del 85% de SOH en un coche de menos de 6 anos es mala senal. Comprueba tambien que la garantia de bateria es valida en Espana.",
        onlyFuel: ["electrico", "phev"],
        critical: true,
        weight: 3,
      },
      {
        id: "embrague",
        label: "Embrague agarra alto y sin patinar",
        detail: "En 5a a 1.500 rpm, pisa a fondo: si las vueltas suben y el coche no acelera, el embrague esta acabado.",
        onlyGearbox: ["manual"],
        weight: 3,
        repairCost: 900,
      },
      {
        id: "dsg",
        label: "Cambio automatico suave, sin tirones ni retardos",
        detail:
          "Los DSG en seco (DQ200) y algunos CVT son el punto debil. Prueba parado: D-R-D con el pie en el freno, sin golpes secos. Mecatronica: 1.500-2.500 EUR.",
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
    subtitle:
      "Minimo 20 minutos y con autovia. Si el vendedor no te deja conducirlo, se acabo la visita.",
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
        detail: "Vibracion al frenar = discos alabeados: 300-600 EUR. Pruebalo tambien con una frenada fuerte.",
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
        detail: "Muchos defectos (rodamientos, equilibrado, alineacion, aerodinamica tras un golpe) solo salen ahi.",
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
          "Datos completos de ambos, VIN, km, precio, fecha y la frase de que se vende libre de cargas. En Alemania usa el modelo del ADAC.",
        critical: true,
        weight: 3,
      },
      {
        id: "factura-iva",
        label: "Si compras a profesional: factura con el regimen de IVA claro",
        detail:
          "Tiene que decir si aplica el regimen de bienes usados (REBU) o si es una entrega intracomunitaria exenta. De ello depende que pagues o no un 21% extra aqui.",
        weight: 3,
      },
      {
        id: "pago-seguro",
        label: "Pago por transferencia, nunca efectivo a ciegas",
        detail:
          "Ideal: transferencia desde el banco del vendedor, con el dinero en mano de ambos. Nada de Bizum, cripto ni 'senal para reservarlo' antes de ver el coche.",
        critical: true,
        weight: 3,
      },
      {
        id: "baja-origen",
        label: "Baja o exportacion tramitada en el pais de origen",
        detail:
          "En Alemania: Ausfuhrkennzeichen o baja. En Francia: declaration de cession en el ANTS. Si no se hace, las multas del pais de origen te seguiran llegando a ti.",
        critical: true,
        weight: 3,
      },
      {
        id: "seguro-traslado",
        label: "Seguro de traslado contratado antes de arrancar",
        weight: 3,
      },
      {
        id: "tramites-es",
        label: "Tienes clara la lista de tramites en Espana",
        detail:
          "1) Modelo 576 (impuesto de matriculacion) en Hacienda. 2) ITV de importacion y ficha tecnica. 3) Impuesto de circulacion en tu ayuntamiento. 4) Matriculacion en la DGT con la tasa. En ese orden.",
        weight: 2,
      },
      {
        id: "plazo-30-dias",
        label: "Sabes que tienes 30 dias habiles para matricularlo",
        detail:
          "Desde que el coche entra en Espana. Pasado el plazo hay recargos, y circular con matricula extranjera caducada es multa y posible inmovilizacion.",
        weight: 2,
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
