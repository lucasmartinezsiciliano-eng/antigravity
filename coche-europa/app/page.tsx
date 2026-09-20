import Link from "next/link";
import Dossiers from "@/components/Dossiers";

const PASOS = [
  {
    n: "01",
    title: "Busca en toda Europa a la vez",
    text: "Pones los filtros una sola vez y la app lanza la misma busqueda contra 13 portales de 9 paises. Alemania, Francia, Italia, Holanda, Polonia... y de paso los espanoles, para que veas si de verdad compensa.",
    href: "/buscar",
    cta: "Abrir el buscador",
  },
  {
    n: "02",
    title: "Calcula lo que cuesta de verdad",
    text: "El precio del anuncio no es el precio. Impuesto de matriculacion segun CO2, transporte, ITV de importacion, homologacion, gestoria y tasas. Te decimos el coste puerta a puerta y si sigue siendo un chollo.",
    href: "/coste",
    cta: "Calcular coste",
  },
  {
    n: "03",
    title: "Revisa el coche sin dejarte nada",
    text: "Una lista de 70 puntos que se filtra a los que le tocan a tu coche, en el orden correcto: lo que se comprueba desde casa antes de coger el avion, los papeles de cada pais, el arranque en frio, la chapa y la prueba en carretera.",
    href: "/revision",
    cta: "Empezar revision",
  },
];

export default function Home() {
  return (
    <main className="wrap" style={{ paddingTop: 44, paddingBottom: 30 }}>
      <section style={{ maxWidth: 700 }}>
        <div className="pill accent" style={{ marginBottom: 18 }}>
          Comprar fuera sale barato. Comprar mal, carisimo.
        </div>
        <h1>
          Encuentra tu coche en Europa
          <br />
          <span style={{ color: "var(--muted)" }}>y comprueba que esta bien antes de pagar.</span>
        </h1>
        <p className="muted" style={{ marginTop: 18, fontSize: 17, lineHeight: 1.6 }}>
          Un aleman de tres anos puede costar 4.000 euros menos que aqui. Tambien puede llegar con
          los kilometros maquillados, sin el Teil II o con un impuesto de matriculacion que se come
          el ahorro entero. Esta app cubre las tres cosas.
        </p>
        <div className="row" style={{ marginTop: 26 }}>
          <Link href="/buscar" className="btn primary">
            Buscar coches
          </Link>
          <Link href="/revision" className="btn">
            Ya tengo uno en mente
          </Link>
        </div>
      </section>

      <section className="grid grid-3" style={{ marginTop: 52 }}>
        {PASOS.map((p) => (
          <Link key={p.n} href={p.href} className="card" style={{ textDecoration: "none" }}>
            <div className="mono dim tiny" style={{ letterSpacing: "0.1em" }}>
              PASO {p.n}
            </div>
            <h3 style={{ marginTop: 10, marginBottom: 8 }}>{p.title}</h3>
            <p className="muted small">{p.text}</p>
            <div className="small" style={{ marginTop: 14, color: "var(--accent)" }}>
              {p.cta} &rarr;
            </div>
          </Link>
        ))}
      </section>

      <Dossiers />

      <section className="card" style={{ marginTop: 40 }}>
        <h3>Lo que esta app no hace</h3>
        <div className="stack small muted" style={{ marginTop: 12 }}>
          <div className="note">
            <strong style={{ color: "var(--text)" }}>No se inventa anuncios.</strong> Los portales
            grandes no tienen API abierta, asi que la app construye la busqueda con tus filtros y la
            abre en cada uno. Si conectas una fuente propia, sus resultados aparecen mezclados en la
            lista unificada.
          </div>
          <div className="note">
            <strong style={{ color: "var(--text)" }}>No sustituye a una gestoria.</strong> Los
            calculos fiscales son orientativos. La base imponible del impuesto de matriculacion la
            fija Hacienda con sus propias tablas de valor, no el precio que pagues.
          </div>
          <div className="note">
            <strong style={{ color: "var(--text)" }}>No sustituye a un mecanico.</strong> La revision
            guiada evita los errores de bulto, pero si el coche vale mas de 15.000 euros, una
            inspeccion profesional en destino cuesta 150 y los vale.
          </div>
        </div>
      </section>
    </main>
  );
}
