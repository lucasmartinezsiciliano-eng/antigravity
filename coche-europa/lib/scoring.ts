/** Nota, veredicto y cuanto hay que bajar el precio. */

import { allItems, type ChecklistContext } from "./checklist";
import type { Answer, CheckItem, Verdict } from "./types";

export function evaluate(
  answers: Record<string, Answer>,
  ctx: ChecklistContext,
): Verdict {
  const items = allItems(ctx);
  const answered = items.filter((i) => answers[i.id] && answers[i.id] !== null);
  const valid = answered.filter((i) => answers[i.id] !== "na");

  const pesoTotal = valid.reduce((s, i) => s + i.weight, 0);
  const pesoOk = valid
    .filter((i) => answers[i.id] === "ok")
    .reduce((s, i) => s + i.weight, 0);

  const score = pesoTotal === 0 ? 0 : Math.round((pesoOk / pesoTotal) * 100);

  const defects: CheckItem[] = valid.filter((i) => answers[i.id] === "ko");
  const redFlags = defects.filter((i) => i.critical);
  // Un punto clave no se negocia: o esta bien o te vas. Solo el resto entra
  // en la lista de descuentos.
  const negociables = defects.filter((i) => !i.critical);
  const descuento = negociables.reduce((s, i) => s + (i.repairCost ?? 0), 0);

  const progreso = items.length === 0 ? 0 : answered.length / items.length;

  let level: Verdict["level"];
  let title: string;
  let message: string;

  if (progreso < 0.6) {
    level = "incompleto";
    title = "Revision a medias";
    message =
      "Te falta mas de un tercio de la revision. Con esto todavia no puedes decidir: sigue hasta el final antes de hablar de dinero.";
  } else if (redFlags.length > 0) {
    level = "huir";
    title = redFlags.length === 1 ? "1 motivo para irte" : `${redFlags.length} motivos para irte`;
    message =
      "Has marcado como mal alguno de los puntos innegociables. No es cuestion de precio: por muy barato que te lo pongan, este coche te va a costar mas de lo que crees. Dale las gracias y vete.";
  } else if (score < 60) {
    level = "riesgo";
    title = "Riesgo alto";
    message =
      "Demasiadas cosas fallan. Solo tiene sentido si es muy barato y te lo mira un taller antes de pagar. Si tienes dudas, hay mas coches.";
  } else if (score < 85 || descuento > 0) {
    level = "negociar";
    title = "Comprable, pero negociando";
    message =
      "El coche esta bien de base y los fallos tienen arreglo. Usa la lista de defectos como argumento: no pidas descuento en general, pide el importe concreto de cada cosa.";
  } else {
    level = "ok";
    title = "Buena compra";
    message =
      "La revision ha salido limpia. Cierra el precio, pide contrato bilingue y asegurate de la baja en el pais de origen.";
  }

  return {
    score,
    answered: answered.length,
    totalItems: items.length,
    redFlags,
    defects,
    negociables,
    descuento,
    level,
    title,
    message,
  };
}

/**
 * Lo maximo que deberias pagar por el coche, mirando el bolsillo:
 * lo que cuesta aqui, menos lo que cuesta traerlo, menos lo que hay que
 * arreglarle, menos un margen para los imprevistos (que los habra).
 */
export function precioMaximo(opts: {
  precioEspana?: number;
  sobrecosteImportacion: number;
  descuentoDefectos: number;
  margen?: number;
}): number | undefined {
  if (!opts.precioEspana) return undefined;
  const margen = opts.margen ?? 0.05;
  return Math.round(
    (opts.precioEspana - opts.sobrecosteImportacion - opts.descuentoDefectos) * (1 - margen),
  );
}

export const LEVEL_COLOR: Record<Verdict["level"], string> = {
  ok: "var(--ok)",
  negociar: "var(--warn)",
  riesgo: "var(--warn)",
  huir: "var(--bad)",
  incompleto: "var(--muted)",
};
