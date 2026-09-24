/**
 * Un portal de coches y una API de eBay de mentira, en localhost.
 *
 * Sirven para lo que no se puede hacer contra los portales de verdad: ejecutar
 * los adaptadores enteros, con su fetcher, su robots.txt y sus fallos, y ver
 * que hacen. No prueban que los selectores de AutoScout24 sigan siendo validos
 * hoy —eso solo lo dice `npm run probe` desde una red sin filtro— pero si
 * prueban que todo lo demas funciona.
 */

import { createServer, type Server } from "node:http";

export interface PortalFalso {
  base: string;
  cierra: () => Promise<void>;
  /** Cuantas veces se ha pedido cada ruta. Para comprobar cache y ritmo. */
  peticiones: string[];
}

interface Opciones {
  /** Contenido de robots.txt. `null` = responde 404 (todo permitido). */
  robots?: string | null;
  /** Milisegundos de retraso en /lento. */
  retraso?: number;
}

const ANUNCIO_JSONLD = `
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"ItemList","itemListElement":[
 {"@type":"Car","name":"BMW 320d xDrive Touring","url":"/ofertas/bmw-320d-1234567",
  "brand":{"@type":"Brand","name":"BMW"},"model":"320d",
  "vehicleModelDate":"2019","vehicleTransmission":"Automatik","fuelType":"Diesel",
  "mileageFromOdometer":{"@type":"QuantitativeValue","value":"95000","unitCode":"KMT"},
  "vehicleEngine":{"enginePower":{"value":140,"unitText":"kW"}},
  "vehicleIdentificationNumber":"WBA8E51070K123456",
  "image":["/img/1.jpg"],
  "offers":{"@type":"Offer","price":"24.500","priceCurrency":"EUR",
   "availableAtOrFrom":{"address":{"addressLocality":"Munchen","addressCountry":"DE","postalCode":"80331"}}}},
 {"@type":"Car","name":"BMW 320d Advantage","url":"/ofertas/bmw-320d-7654321",
  "brand":{"@type":"Brand","name":"BMW"},"model":"320d",
  "vehicleModelDate":"2018","vehicleTransmission":"Schaltgetriebe","fuelType":"Diesel",
  "mileageFromOdometer":{"@type":"QuantitativeValue","value":"142000","unitCode":"KMT"},
  "offers":{"@type":"Offer","price":"18.900","priceCurrency":"EUR",
   "availableAtOrFrom":{"address":{"addressLocality":"Koln","addressCountry":"DE"}}}}
]}
</script>`;

/** Como el anterior pero sin JSON-LD: obliga a caer a la tercera estrategia. */
const ANUNCIO_HTML = `
<article data-guid="9001">
  <a href="/ofertas/audi-a4-9001"><h2>Audi A4 Avant 2.0 TDI</h2></a>
  <p data-testid="regular-price">21.750 €</p>
  <span data-testid="VehicleDetails-mileage_road">88.000 km</span>
  <span data-testid="VehicleDetails-calendar">04/2020</span>
  <span data-testid="VehicleDetails-gas_pump">Diesel</span>
  <span data-testid="VehicleDetails-transmission">Automatik</span>
  <span data-testid="VehicleDetails-speedometer">190 PS</span>
  <img src="/img/9001.jpg">
</article>`;

export function levantarPortal(op: Opciones = {}): Promise<PortalFalso> {
  const peticiones: string[] = [];

  const server: Server = createServer((req, res) => {
    const ruta = (req.url ?? "/").split("?")[0]!;
    peticiones.push(ruta);

    const html = (cuerpo: string, code = 200) => {
      res.writeHead(code, { "content-type": "text/html; charset=utf-8" });
      res.end(`<!doctype html><html><body>${cuerpo}</body></html>`);
    };
    const json = (cuerpo: unknown, code = 200) => {
      res.writeHead(code, { "content-type": "application/json" });
      res.end(JSON.stringify(cuerpo));
    };

    if (ruta === "/robots.txt") {
      if (op.robots === null) return json({}, 404);
      res.writeHead(200, { "content-type": "text/plain" });
      return res.end(op.robots ?? "User-agent: *\nDisallow: /privado\n");
    }

    // --- portal ---
    if (ruta.startsWith("/lst")) return html(ANUNCIO_JSONLD);
    if (ruta.startsWith("/solo-html")) return html(ANUNCIO_HTML);
    if (ruta.startsWith("/vacio")) return html("<p>Sin resultados</p>");
    if (ruta.startsWith("/privado")) return html("secreto");
    if (ruta.startsWith("/antibot")) return html("<h1>Verificando tu navegador</h1>", 403);
    if (ruta.startsWith("/lento")) {
      setTimeout(() => html(ANUNCIO_JSONLD), op.retraso ?? 3000);
      return;
    }

    // --- eBay de mentira ---
    if (ruta === "/identity/v1/oauth2/token") {
      const auth = req.headers.authorization ?? "";
      if (!auth.startsWith("Basic ")) return json({ error: "sin credenciales" }, 401);
      const [id, secreto] = Buffer.from(auth.slice(6), "base64").toString().split(":");
      if (id !== "cliente-bueno" || secreto !== "secreto-bueno") {
        return json({ error: "invalid_client" }, 401);
      }
      return json({ access_token: "token-de-prueba", expires_in: 7200 });
    }

    if (ruta === "/buy/browse/v1/item_summary/search") {
      if (req.headers.authorization !== "Bearer token-de-prueba") return json({ error: "token" }, 401);
      const mercado = req.headers["x-ebay-c-marketplace-id"];
      return json({
        itemSummaries: [
          {
            itemId: "v1|1122334455|0",
            title: "BMW 320d Touring - " + mercado,
            price: { value: "23450.00", currency: "EUR" },
            itemWebUrl: "https://www.ebay.de/itm/1122334455",
            image: { imageUrl: "https://i.ebayimg.com/1.jpg" },
            itemLocation: { country: "DE", city: "Hamburg", postalCode: "20095" },
            seller: { username: "autohaus_nord" },
            localizedAspects: [
              { name: "Marke", value: "BMW" },
              { name: "Kilometerstand", value: "112.500" },
              { name: "Baujahr", value: "2018" },
              { name: "Kraftstoffart", value: "Diesel" },
              { name: "Getriebe", value: "Automatik" },
              { name: "Leistung", value: "140 kW" },
            ],
          },
        ],
      });
    }

    json({ error: "no existe" }, 404);
  });

  return new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => {
      const { port } = server.address() as { port: number };
      resolve({
        base: `http://127.0.0.1:${port}`,
        peticiones,
        cierra: () => new Promise<void>((r) => server.close(() => r())),
      });
    });
  });
}
