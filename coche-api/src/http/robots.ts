/**
 * robots.txt: lo minimo que hace falta para portarse bien.
 *
 * No es un parser completo del estandar, pero cubre lo que usan estos
 * portales: grupos por User-agent, Allow y Disallow con comodines, y
 * Crawl-delay. Gana la regla mas especifica, y Allow gana a Disallow con la
 * misma longitud, que es lo que dice el RFC 9309.
 */

interface Rule {
  allow: boolean;
  path: string;
}

export interface Robots {
  rules: Rule[];
  crawlDelay?: number;
}

export function parseRobots(txt: string, ua: string): Robots {
  const lineas = txt.split(/\r?\n/).map((l) => l.replace(/#.*$/, "").trim());
  const uaLower = ua.toLowerCase();

  let grupoActivo = false;
  let leyendoUa = false;
  let especificidad = -1; // -1 sin grupo, 0 comodin, 1 nombrado
  const reglas: Rule[] = [];
  let crawlDelay: number | undefined;

  for (const linea of lineas) {
    const i = linea.indexOf(":");
    if (i < 0) continue;
    const campo = linea.slice(0, i).trim().toLowerCase();
    const valor = linea.slice(i + 1).trim();

    if (campo === "user-agent") {
      const nombrado = valor !== "*" && uaLower.includes(valor.toLowerCase());
      const comodin = valor === "*";
      const nivel = nombrado ? 1 : comodin ? 0 : -1;

      if (!leyendoUa) {
        // Empieza un grupo nuevo: si el anterior era mas especifico, lo mantenemos.
        if (nivel > especificidad) {
          especificidad = nivel;
          grupoActivo = nivel >= 0;
          reglas.length = 0;
          crawlDelay = undefined;
        } else {
          grupoActivo = false;
        }
      } else if (nivel > especificidad) {
        especificidad = nivel;
        grupoActivo = true;
      }
      leyendoUa = true;
      continue;
    }

    leyendoUa = false;
    if (!grupoActivo) continue;

    if (campo === "disallow" || campo === "allow") {
      if (valor === "" && campo === "disallow") continue; // "Disallow:" vacio = permite todo
      reglas.push({ allow: campo === "allow", path: valor });
    } else if (campo === "crawl-delay") {
      const n = Number(valor);
      if (Number.isFinite(n) && n >= 0) crawlDelay = n;
    }
  }

  return { rules: reglas, crawlDelay };
}

/** Compara una ruta contra un patron de robots.txt (admite * y $). */
function coincide(path: string, patron: string): boolean {
  if (patron === "") return false;
  const anclado = patron.endsWith("$");
  const limpio = anclado ? patron.slice(0, -1) : patron;
  const regex = new RegExp(
    "^" + limpio.split("*").map((p) => p.replace(/[.+?^${}()|[\]\\]/g, "\\$&")).join(".*") + (anclado ? "$" : ""),
  );
  return regex.test(path);
}

export function permitido(robots: Robots, url: string): boolean {
  let path: string;
  try {
    const u = new URL(url);
    path = u.pathname + u.search;
  } catch {
    return false;
  }

  let mejor: { allow: boolean; len: number } | undefined;
  for (const r of robots.rules) {
    if (!coincide(path, r.path)) continue;
    const len = r.path.replace(/[*$]/g, "").length;
    // A igual longitud, Allow gana.
    if (!mejor || len > mejor.len || (len === mejor.len && r.allow)) {
      mejor = { allow: r.allow, len };
    }
  }
  return mejor ? mejor.allow : true;
}
