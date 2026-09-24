"use client";

import { useMemo, useSyncExternalStore } from "react";
import { getServerSnapshot, getSnapshot, parseSnapshot, subscribe } from "@/lib/storage";
import type { Dossier } from "@/lib/types";

/** Los expedientes guardados, ya sincronizados entre pestanas. */
export function useDossiers(): {
  listo: boolean;
  dossiers: Dossier[];
  activo: Dossier | null;
} {
  const raw = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  return useMemo(() => {
    if (raw === "") return { listo: false, dossiers: [], activo: null };
    const { active, dossiers } = parseSnapshot(raw);
    return {
      listo: true,
      dossiers,
      activo: dossiers.find((d) => d.id === active) ?? dossiers[0] ?? null,
    };
  }, [raw]);
}
