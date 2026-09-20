import { Suspense } from "react";
import Calculadora from "@/components/Calculadora";

export const metadata = {
  title: "Cuanto cuesta traerlo a Espana — Coche Europa",
};

export default function CostePage() {
  return (
    <Suspense fallback={<main className="wrap" style={{ paddingTop: 28 }}><p className="muted">Cargando...</p></main>}>
      <Calculadora />
    </Suspense>
  );
}
