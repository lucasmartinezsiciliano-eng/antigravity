"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  Trophy,
  TrendingUp,
  MapPin,
  ExternalLink,
  ChevronRight,
  Search,
  Filter,
} from "lucide-react";

type LeaderboardEntry = {
  rank: number;
  barber_id: string;
  barber_name: string;
  barbershop_name: string;
  city: string;
  clients_this_period: number;
  clients_all_time: number;
  current_tier: string;
  instagram_handle?: string;
};

const TIER_BADGES: Record<string, { emoji: string; color: string }> = {
  platinum: { emoji: "💎", color: "from-cyan-500 to-blue-500" },
  gold: { emoji: "🥇", color: "from-yellow-500 to-amber-500" },
  silver: { emoji: "🥈", color: "from-gray-300 to-gray-400" },
  bronze: { emoji: "🥉", color: "from-orange-600 to-amber-600" },
};

export default function LeaderboardPage() {
  const searchParams = useSearchParams();
  const initialPeriod = (searchParams.get("period") || "all_time") as
    | "week"
    | "month"
    | "all_time";

  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState<"week" | "month" | "all_time">(initialPeriod);
  const [cityFilter, setCityFilter] = useState("");
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    const loadLeaderboard = async () => {
      setLoading(true);
      try {
        const { api } = await import("@/lib/api");
        const data = await api.getLeaderboard(period, cityFilter, 50, 0);
        setEntries(data);
      } catch (err: any) {
        console.error("Error loading leaderboard:", err.message);
      } finally {
        setLoading(false);
      }
    };

    loadLeaderboard();
  }, [period, cityFilter]);

  const filteredEntries = entries.filter((entry) => {
    const matchesSearch =
      entry.barber_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      entry.barbershop_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      entry.city.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCity = !cityFilter || entry.city === cityFilter;
    return matchesSearch && matchesCity;
  });

  const uniqueCities = Array.from(new Set(entries.map((e) => e.city))).sort();

  const getPeriodLabel = (p: "week" | "month" | "all_time") => {
    switch (p) {
      case "week":
        return "Esta Semana";
      case "month":
        return "Este Mes";
      case "all_time":
        return "Total (All-Time)";
    }
  };

  return (
    <div className="min-h-screen bg-black">
      {/* Header */}
      <div className="border-b border-gray-800 bg-gradient-to-b from-gray-900 to-black">
        <div className="max-w-6xl mx-auto px-4 py-8">
          <div className="flex items-center gap-3 mb-4">
            <Trophy className="h-8 w-8 text-gold" />
            <h1 className="text-4xl font-bold text-white">Leaderboard VISAI</h1>
          </div>
          <p className="text-gray-400">
            Top barberos de España según clientes analizados
          </p>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Controls */}
        <div className="mb-8 space-y-4">
          {/* Period Selector */}
          <div className="flex flex-wrap gap-3">
            {(["week", "month", "all_time"] as const).map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`px-4 py-2 rounded font-medium transition-colors ${
                  period === p
                    ? "bg-gold text-black"
                    : "bg-gray-900 text-gray-300 hover:bg-gray-800"
                }`}
              >
                {getPeriodLabel(p)}
              </button>
            ))}
          </div>

          {/* Search & Filter */}
          <div className="grid md:grid-cols-2 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-gray-500" />
              <input
                type="text"
                placeholder="Buscar barbero, barbería o ciudad..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-gray-900 border border-gray-800 rounded px-10 py-2 text-white placeholder-gray-500 focus:border-gold focus:outline-none transition-colors"
              />
            </div>

            <div className="relative">
              <Filter className="absolute left-3 top-3 h-4 w-4 text-gray-500" />
              <select
                value={cityFilter}
                onChange={(e) => setCityFilter(e.target.value)}
                className="w-full bg-gray-900 border border-gray-800 rounded px-10 py-2 text-white focus:border-gold focus:outline-none transition-colors appearance-none cursor-pointer"
              >
                <option value="">Todas las ciudades</option>
                {uniqueCities.map((city) => (
                  <option key={city} value={city}>
                    {city}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Leaderboard */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin">
              <div className="h-12 w-12 border-4 border-gold border-t-transparent rounded-full" />
            </div>
          </div>
        ) : filteredEntries.length === 0 ? (
          <div className="text-center py-12">
            <Trophy className="h-12 w-12 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400">No se encontraron barberos</p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredEntries.map((entry) => {
              const tier = TIER_BADGES[entry.current_tier] || TIER_BADGES.bronze;
              const clientCount = period === "week" ? entry.clients_this_period
                : period === "month" ? Math.floor(entry.clients_all_time / 3)
                : entry.clients_all_time;

              return (
                <Link
                  key={entry.barber_id}
                  href={`/barber/dashboard?id=${entry.barber_id}`}
                >
                  <div className="bg-gray-900 border border-gray-800 hover:border-gold rounded-lg p-4 transition-all hover:shadow-lg hover:shadow-gold/20 cursor-pointer group">
                    <div className="flex items-center gap-4">
                      {/* Rank */}
                      <div className="flex-shrink-0">
                        <div className="flex items-center justify-center h-12 w-12 rounded-full bg-gradient-to-br from-gold/20 to-gold/10">
                          {entry.rank <= 3 ? (
                            <span className="text-2xl">{tier.emoji}</span>
                          ) : (
                            <span className="text-white font-bold text-lg">
                              #{entry.rank}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Info */}
                      <div className="flex-1 min-w-0">
                        <h3 className="text-white font-bold group-hover:text-gold transition-colors">
                          {entry.barber_name}
                        </h3>
                        <p className="text-gray-400 text-sm">{entry.barbershop_name}</p>
                        <div className="flex items-center gap-4 text-xs text-gray-500 mt-2">
                          <span className="flex items-center gap-1">
                            <MapPin className="h-3 w-3" />
                            {entry.city}
                          </span>
                          {entry.instagram_handle && (
                            <span className="flex items-center gap-1">
                              <ExternalLink className="h-3 w-3" />
                              @{entry.instagram_handle}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Stats */}
                      <div className="flex-shrink-0 text-right">
                        <div className="text-gold font-bold text-lg flex items-center gap-1">
                          <TrendingUp className="h-4 w-4" />
                          {clientCount}
                        </div>
                        <p className="text-gray-400 text-xs">
                          {period === "week"
                            ? "análisis esta semana"
                            : period === "month"
                            ? "análisis este mes"
                            : "análisis total"}
                        </p>
                      </div>

                      {/* Arrow */}
                      <ChevronRight className="h-5 w-5 text-gray-600 group-hover:text-gold transition-colors flex-shrink-0" />
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        )}

        {/* Info Box */}
        <div className="mt-12 bg-gray-900 border border-gray-800 rounded-lg p-6">
          <h3 className="text-white font-bold mb-2">¿Cómo funciona el ranking?</h3>
          <p className="text-gray-400 text-sm">
            Cada barbero sube fotos de referencia (1 frontal + 1 lateral por corte).
            Los clientes usan tu código VISAI al analizar su cara. Cuantos más clientes
            usen tu código, más alto subes en el ranking. Los barberos con más clientes
            reciben badge de Oro, Plata y Bronce.
          </p>
        </div>
      </div>
    </div>
  );
}
