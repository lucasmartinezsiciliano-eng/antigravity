"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const TABS = [
  { href: "/buscar", label: "Buscar" },
  { href: "/coste", label: "Coste real" },
  { href: "/revision", label: "Revision" },
  { href: "/informe", label: "Informe" },
];

export default function Nav() {
  const path = usePathname();
  return (
    <nav className="nav no-print">
      <div className="wrap nav-in">
        <Link href="/" className="brand">
          Coche<span>Europa</span>
        </Link>
        {TABS.map((t) => (
          <Link key={t.href} href={t.href} className={`tab${path?.startsWith(t.href) ? " on" : ""}`}>
            {t.label}
          </Link>
        ))}
      </div>
    </nav>
  );
}
