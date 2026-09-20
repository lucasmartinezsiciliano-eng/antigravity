"use client";

import { useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useRouter } from "next/navigation";
import {
  CCAA_ITP,
  DATOS_ACTUALIZADOS,
  calcularCostes,
  tramoIedmt,
  valorFiscalEstimado,
} from "@/lib/import-cost";
import { COUNTRIES } from "@/lib/portals";
import { createDossier, getActiveId, getDossier, saveDossier } from "@/lib/storage";
import type { CostInputs, CountryCode, Fuel, TransportMode } from "@/lib/types";

const PAISES: CountryCode[] = ["DE", "FR", "IT", "NL", "BE", "AT", "PT", "PL", "LU"];
const euros = (n: number) =>
  Math.round(n).toLocaleString("es-ES", { maximumFractionDigits: 0 }) + " €";

export default function Calculadora() {
  const params = useSearchParams();
  const router = useRouter();
  const [guardado, setGuardado] = useState(false);

  const nombre = params.get("name") ?? "";
  const anio = Number(params.get("year")) || undefined;

  const [i, setI] = useState<CostInputs>({
    price: Number(params.get("price")) || 12000,
    country: (params.get("country") as CountryCode) || "DE",
    region: "peninsula",
    co2: Number(params.get("co2")) || undefined,
    fuel: (params.get("fuel") as Fuel) || undefined,
    firstRegistration: anio ? `${anio}-06-01` : undefined,
    km: Number(params.get("km")) || undefined,
    seller: "particular",
    itpRate: 5,
    includeItp: true,
    transport: "camion",
    hasCoc: false,
    useGestoria: true,
    vinReport: true,
  });

  const [precioNuevo, setPrecioNuevo] = useState<number | "">("");

  const set = <K extends keyof CostInputs>(k: K, v: CostInputs[K]) =>
    setI((prev) => ({ ...prev, [k]: v }));

  const r = useMemo(() => calcularCostes(i), [i]);
  const tramo = tramoIedmt(i.co2, i.region);
  const num = (v: string) => (v === "" ? undefined : Number(v));

  function estimarValorFiscal() {
    if (!precioNuevo) return;
    set("valorFiscal", valorFiscalEstimado(Number(precioNuevo), i.firstRegistration));
  }

  function guardar() {
    const id = getActiveId();
    const d = id ? getDossier(id) : undefined;
    if (d) saveDossier({ ...d, cost: i });
    else createDossier({ name: nombre || "Coche sin nombre", cost: i });
    setGuardado(true);
  }

  return (
    <main className="wrap narrow" style={{ paddingTop: 28, paddingBottom: 40 }}>
      <h1 style={{ fontSize: 28 }}>Lo que cuesta de verdad</h1>
      <p className="muted small" style={{ marginTop: 8 }}>
        {nombre ? `${nombre}. ` : ""}El precio del anuncio es la mitad de la historia. Esto es el
        coste puerta a puerta, con el coche ya matriculado y rodando en Espana.
      </p>

      <div className="card" style={{ marginTop: 22 }}>
        <div className="grid grid-2">
          <label className="field">
            Precio del coche
            <input
              type="number"
              inputMode="numeric"
              value={i.price || ""}
              onChange={(e) => set("price", Number(e.target.value) || 0)}
            />
          </label>
          <label className="field">
            Pais de compra
            <select value={i.country} onChange={(e) => set("country", e.target.value as CountryCode)}>
              {PAISES.map((c) => (
                <option key={c} value={c}>
                  {COUNTRIES[c].flag} {COUNTRIES[c].name}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            CO2 oficial (g/km)
            <input
              type="number"
              inputMode="numeric"
              value={i.co2 ?? ""}
              onChange={(e) => set("co2", num(e.target.value))}
              placeholder="Mirar el COC, apartado V.7"
            />
          </label>
          <label className="field">
            Primera matriculacion
            <input
              type="date"
              value={i.firstRegistration ?? ""}
              onChange={(e) => set("firstRegistration", e.target.value || undefined)}
            />
          </label>
          <label className="field">
            Kilometros
            <input
              type="number"
              inputMode="numeric"
              value={i.km ?? ""}
              onChange={(e) => set("km", num(e.target.value))}
            />
          </label>
          <label className="field">
            Quien vende
            <select value={i.seller} onChange={(e) => set("seller", e.target.value as CostInputs["seller"])}>
              <option value="particular">Particular</option>
              <option value="profesional">Profesional / concesionario</option>
            </select>
          </label>
          <label className="field">
            Donde lo matriculas
            <select value={i.region} onChange={(e) => set("region", e.target.value as CostInputs["region"])}>
              <option value="peninsula">Peninsula y Baleares</option>
              <option value="canarias">Canarias</option>
              <option value="ceuta-melilla">Ceuta y Melilla</option>
            </select>
          </label>
          <label className="field">
            Como lo traes
            <select value={i.transport} onChange={(e) => set("transport", e.target.value as TransportMode)}>
              <option value="camion">En camion</option>
              <option value="conducirlo">Voy a buscarlo</option>
              <option value="ya-en-espana">Ya esta aqui</option>
            </select>
          </label>
        </div>

        <details style={{ marginTop: 18 }}>
          <summary className="small muted" style={{ cursor: "pointer" }}>
            Ajustes finos: valor fiscal, ITP y extras
          </summary>
          <div className="grid grid-2" style={{ marginTop: 14 }}>
            <label className="field">
              Valor segun tablas de Hacienda
              <input
                type="number"
                inputMode="numeric"
                value={i.valorFiscal ?? ""}
                onChange={(e) => set("valorFiscal", num(e.target.value))}
                placeholder={`Si lo dejas vacio usamos ${euros(i.price)}`}
              />
            </label>
            <label className="field">
              Precio del modelo nuevo (para estimarlo)
              <div className="row" style={{ gap: 6, flexWrap: "nowrap" }}>
                <input
                  type="number"
                  inputMode="numeric"
                  value={precioNuevo}
                  onChange={(e) => setPrecioNuevo(e.target.value === "" ? "" : Number(e.target.value))}
                  placeholder="45000"
                />
                <button type="button" className="btn sm" onClick={estimarValorFiscal}>
                  Estimar
                </button>
              </div>
            </label>
            <label className="field">
              Tu comunidad autonoma (ITP)
              <select
                value={i.itpRate}
                onChange={(e) => set("itpRate", Number(e.target.value))}
              >
                {CCAA_ITP.map((c) => (
                  <option key={c.id} value={c.rate}>
                    {c.name} ({c.rate}%)
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              Precio del mismo coche en Espana
              <input
                type="number"
                inputMode="numeric"
                value={i.precioEspana ?? ""}
                onChange={(e) => set("precioEspana", num(e.target.value))}
                placeholder="Miralo en Coches.net"
              />
            </label>
          </div>
          <div className="stack" style={{ marginTop: 14 }}>
            <Toggle
              on={i.includeItp}
              onChange={(v) => set("includeItp", v)}
              label="Incluir ITP (compra a particular)"
              hint="Discutido en compras dentro de la UE. Lo dejamos activado para no quedarnos cortos."
            />
            <Toggle
              on={i.hasCoc}
              onChange={(v) => set("hasCoc", v)}
              label="El coche trae COC"
              hint="Certificado de conformidad europeo. Sin el, +400 EUR y semanas de tramites."
            />
            <Toggle
              on={i.useGestoria}
              onChange={(v) => set("useGestoria", v)}
              label="Contratar gestoria"
              hint="Son cuatro ventanillas distintas. Puedes hacerlo tu."
            />
            <Toggle
              on={i.vinReport}
              onChange={(v) => set("vinReport", v)}
              label="Informe de historial por VIN"
              hint="25 EUR. El dinero mejor gastado de toda la compra."
            />
          </div>
        </details>
      </div>

      <div className="card" style={{ marginTop: 20 }}>
        <div className="spread">
          <div>
            <div className="tiny dim">COSTE TOTAL EN ESPANA</div>
            <div className="big-num">{euros(r.total)}</div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div className="tiny dim">SOBRE EL PRECIO DEL ANUNCIO</div>
            <div style={{ fontSize: 20, fontWeight: 650, color: "var(--warn)" }}>
              +{euros(r.sobrecoste)}
            </div>
          </div>
        </div>

        {r.ahorro !== undefined && (
          <div
            className={`note ${r.ahorro > 1500 ? "accent" : r.ahorro > 0 ? "warn" : "bad"}`}
            style={{ marginTop: 16 }}
          >
            {r.ahorro > 1500 ? (
              <>
                Te ahorras <strong style={{ color: "var(--text)" }}>{euros(r.ahorro)}</strong> frente
                a comprarlo en Espana. Compensa.
              </>
            ) : r.ahorro > 0 ? (
              <>
                Solo te ahorras <strong style={{ color: "var(--text)" }}>{euros(r.ahorro)}</strong>.
                Por ese margen no merece la pena el viaje, los tramites ni el riesgo.
              </>
            ) : (
              <>
                Pierdes <strong style={{ color: "var(--text)" }}>{euros(Math.abs(r.ahorro))}</strong>{" "}
                respecto a comprarlo aqui. Busca otro.
              </>
            )}
          </div>
        )}

        <div className="lines" style={{ marginTop: 18 }}>
          {r.lines.map((l) => (
            <div key={l.key} className="line">
              <div style={{ minWidth: 0 }}>
                <div>
                  {l.label}
                  {l.optional && <span className="tiny dim"> · opcional</span>}
                </div>
                {l.note && (
                  <div className="tiny dim" style={{ marginTop: 2 }}>
                    {l.note}
                  </div>
                )}
              </div>
              <div className="amt">{euros(l.amount)}</div>
            </div>
          ))}
          <div className="line total">
            <span>Total</span>
            <span className="amt">{euros(r.total)}</span>
          </div>
        </div>

        <div className="row" style={{ marginTop: 16, gap: 8 }}>
          <span className="pill">Impuestos {euros(r.impuestos)}</span>
          <span className="pill">Gastos {euros(r.gastos)}</span>
          <span className={`pill ${tramo.rate === 0 ? "ok" : tramo.rate > 9 ? "bad" : "warn"}`}>
            Matriculacion {tramo.rate}%
          </span>
        </div>
      </div>

      {r.avisos.length > 0 && (
        <div className="card" style={{ marginTop: 18 }}>
          <h3>Ojo con esto</h3>
          <div className="stack" style={{ marginTop: 12 }}>
            {r.avisos.map((a, n) => (
              <div key={n} className="note warn small">
                {a}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="row" style={{ marginTop: 20 }}>
        <button className="btn primary" onClick={guardar}>
          {guardado ? "Guardado" : "Guardar en mi coche"}
        </button>
        <button className="btn" onClick={() => router.push("/revision")}>
          Ir a la revision
        </button>
      </div>

      <p className="tiny dim" style={{ marginTop: 22 }}>
        Tipos vigentes revisados en {DATOS_ACTUALIZADOS}. El impuesto de matriculacion se calcula
        sobre el valor que fija Hacienda en sus tablas, que puede ser mayor que lo que pagues. Los
        gastos de transporte, ITV, homologacion y gestoria son medias de mercado: pide presupuesto.
      </p>
    </main>
  );
}

function Toggle({
  on,
  onChange,
  label,
  hint,
}: {
  on: boolean;
  onChange: (v: boolean) => void;
  label: string;
  hint?: string;
}) {
  return (
    <label className="row" style={{ gap: 10, alignItems: "flex-start", cursor: "pointer" }}>
      <input
        type="checkbox"
        checked={on}
        onChange={(e) => onChange(e.target.checked)}
        style={{ width: 18, height: 18, marginTop: 2, flex: "0 0 auto", accentColor: "var(--accent)" }}
      />
      <span style={{ flex: 1 }}>
        <span className="small">{label}</span>
        {hint && (
          <span className="tiny dim" style={{ display: "block" }}>
            {hint}
          </span>
        )}
      </span>
    </label>
  );
}
