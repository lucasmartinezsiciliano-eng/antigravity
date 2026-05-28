"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Copy,
  TrendingUp,
  Users,
  Euro,
  Upload,
  Trophy,
  ChevronRight,
  AlertCircle,
  CheckCircle2,
  Clock,
  Camera,
  LogOut,
} from "lucide-react";
import { api } from "@/lib/api";
import { getStoredBarberId, getStoredPromoCode, clearBarberSession } from "@/lib/barber-auth";
import ReferencePhotoUploadModal from "@/components/ReferencePhotoUploadModal";

type BarberDashboardData = {
  barber_id: string;
  name: string;
  barbershop_name?: string;
  promo_code: string;
  clients_all_time?: number;
  clients_this_week?: number;
  all_time_ranking_position?: number | null;
  current_tier?: string;
  reference_photos_count: number;
  reference_photos_validated: number;
  total_earned_euros: number;
  pending_payout_euros: number;
  total_uses?: number;
  total_paid_out_euros?: number;
  is_active?: boolean;
  contract_signed_at?: string | null;
  recent_uses?: Array<{ date: string; earned_euros: number }>;
};

type ReferencePhoto = {
  id: string;
  haircut_type: string;
  photo_angle: string;
  cloudinary_url: string;
  validation_status: string;
  created_at: string;
};

const TIER_BADGES: Record<string, { emoji: string; color: string; label: string }> = {
  platinum: { emoji: "💎", color: "from-cyan-500 to-blue-500", label: "Platino" },
  gold: { emoji: "🥇", color: "from-yellow-500 to-amber-500", label: "Oro" },
  silver: { emoji: "🥈", color: "from-gray-300 to-gray-400", label: "Plata" },
  bronze: { emoji: "🥉", color: "from-orange-600 to-amber-600", label: "Bronce" },
};

function BarberDashboardInner() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const barberId = searchParams.get("id") || getStoredBarberId() || "";
  const promoCode = searchParams.get("promo_code") || getStoredPromoCode() || "";

  const [dashboard, setDashboard] = useState<BarberDashboardData | null>(null);
  const [photos, setPhotos] = useState<ReferencePhoto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [copySuccess, setCopySuccess] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    const loadDashboard = async () => {
      if (!barberId) {
        setError("No barber ID provided");
        setLoading(false);
        return;
      }

      try {
        // Load dashboard stats
        const data = await api.getBarberDashboard(barberId, promoCode || undefined);
        setDashboard({
          ...data,
          reference_photos_count: 0,
          reference_photos_validated: 0,
        });

        // Load reference photos
        try {
          const photosData = await api.getBarberReferencePhotos(barberId);
          setPhotos(photosData);

          // Update photo counts
          setDashboard((prev) =>
            prev
              ? {
                  ...prev,
                  reference_photos_count: photosData.length,
                  reference_photos_validated: photosData.filter(
                    (p) => p.validation_status === "approved",
                  ).length,
                }
              : null,
          );
        } catch {
          console.warn("Could not load reference photos");
          setPhotos([]);
        }
      } catch (err: any) {
        setError(err.message || "Error loading dashboard");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    loadDashboard();
  }, [barberId, refreshKey]);

  const copyPromoCode = () => {
    if (dashboard?.promo_code) {
      navigator.clipboard.writeText(dashboard.promo_code);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    }
  };

  if (loading) {
    return (
      <div style={{ minHeight: "100dvh", background: "var(--bg)", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div className="spinner" style={{ width: 48, height: 48 }} />
      </div>
    );
  }

  if (error || !dashboard) {
    return (
      <div style={{ minHeight: "100dvh", background: "var(--bg)", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ textAlign: "center", padding: "0 24px" }}>
          <AlertCircle style={{ width: 48, height: 48, color: "var(--danger)", margin: "0 auto 16px" }} />
          <p style={{ color: "var(--text)", fontSize: 17, marginBottom: 16 }}>{error || "Dashboard not found"}</p>
          <Link href="/" style={{ color: "var(--gold)", textDecoration: "underline" }}>
            Volver al inicio
          </Link>
        </div>
      </div>
    );
  }

  const tier = TIER_BADGES[dashboard.current_tier ?? "bronze"] || TIER_BADGES.bronze;
  const contractUnsigned = !dashboard.contract_signed_at;
  const hasFrontal = photos.some((p) => p.photo_angle === "frontal");
  const hasLateral = photos.some((p) => p.photo_angle === "lateral");
  const photosMissing = !hasFrontal || !hasLateral;
  const codeInactive = contractUnsigned || photosMissing;

  return (
    <div className="min-h-screen bg-black">
      {/* Activation banner — shows what's still needed */}
      {codeInactive && (
        <div className="bg-amber-900/40 border-b border-amber-700/50">
          <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-amber-400 flex-shrink-0" />
              <p className="text-amber-200 text-sm">
                <span className="font-semibold">Tu código sigue inactivo.</span>{" "}
                {contractUnsigned && photosMissing
                  ? "Firma el contrato y sube fotos de referencia (frontal + lateral) para activarlo."
                  : contractUnsigned
                    ? "Firma el contrato de colaboración para activarlo."
                    : !hasFrontal && !hasLateral
                      ? "Sube al menos 1 foto frontal y 1 lateral de un corte para activarlo."
                      : !hasFrontal
                        ? "Sube al menos 1 foto frontal de un corte para activarlo."
                        : "Sube al menos 1 foto lateral de un corte para activarlo."}
              </p>
            </div>
            <Link
              href={contractUnsigned
                ? `/barber/contrato?id=${encodeURIComponent(barberId)}`
                : `/barber/fotos-referencia?id=${barberId}`}
              className="bg-amber-500 hover:bg-amber-400 text-black font-bold text-sm px-4 py-1.5 rounded flex-shrink-0 transition-colors"
            >
              {contractUnsigned ? "Firmar →" : "Subir fotos →"}
            </Link>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="border-b border-gray-800 bg-gradient-to-b from-gray-900 to-black">
        <div className="max-w-4xl mx-auto px-4 py-6 flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">{dashboard.name}</h1>
            <p className="text-gray-400">Tu panel de control VISAI</p>
          </div>
          <button
            onClick={() => {
              clearBarberSession();
              router.push("/barber/login");
            }}
            className="flex items-center gap-2 text-gray-500 hover:text-gray-300 text-sm transition-colors mt-2"
          >
            <LogOut className="h-4 w-4" />
            Salir
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Tier Badge + Quick Stats */}
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          {/* Tier Card */}
          <div className={`bg-gradient-to-br ${tier.color} p-6 rounded-lg shadow-lg`}>
            <div className="text-5xl mb-2">{tier.emoji}</div>
            <h2 className="text-white font-bold text-xl mb-1">Tier: {tier.label}</h2>
            <p className="text-white/80">
              Posición #{dashboard.all_time_ranking_position || "—"}
            </p>
          </div>

          {/* Promo Code Card */}
          <div className="bg-gray-900 border border-gray-800 p-6 rounded-lg">
            <h3 className="text-gray-400 text-sm font-semibold mb-3">Tu Código VISAI</h3>
            <div className="flex items-center justify-between bg-gray-800 rounded px-4 py-3">
              <code className="text-gold font-mono text-lg font-bold">
                {dashboard.promo_code}
              </code>
              <button
                onClick={copyPromoCode}
                className={`p-2 rounded transition-colors ${
                  copySuccess
                    ? "bg-green-500 text-white"
                    : "bg-gray-700 hover:bg-gray-600 text-gray-300"
                }`}
              >
                {copySuccess ? (
                  <CheckCircle2 className="h-5 w-5" />
                ) : (
                  <Copy className="h-5 w-5" />
                )}
              </button>
            </div>
            <p className="text-xs text-gray-400 mt-2">
              Comparte con tus clientes • Ellos ahorran €3 • Tú ganas €3 por análisis
            </p>
            <p className="text-xs text-green-400 mt-1 font-semibold">
              ✓ Totalmente gratis para ti — solo compartes el código
            </p>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid md:grid-cols-4 gap-4 mb-8">
          <MetricCard
            icon={<Users className="h-6 w-6" />}
            label="Esta Semana"
            value={dashboard.clients_this_week ?? dashboard.total_uses ?? 0}
            subtext="análisis completados"
          />
          <MetricCard
            icon={<TrendingUp className="h-6 w-6" />}
            label="Total (All-Time)"
            value={dashboard.clients_all_time ?? dashboard.total_uses ?? 0}
            subtext="desde que te registraste"
          />
          <MetricCard
            icon={<Euro className="h-6 w-6" />}
            label="Ganado Total"
            value={`€${dashboard.total_earned_euros.toFixed(2)}`}
            subtext="menos fees"
          />
          <MetricCard
            icon={<Clock className="h-6 w-6" />}
            label="Pendiente"
            value={`€${dashboard.pending_payout_euros.toFixed(2)}`}
            subtext="en espera de pago"
          />
        </div>

        {/* Reference Photos Section */}
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-white font-bold text-lg flex items-center gap-2">
                <Camera className="h-5 w-5" />
                Fotos de Referencia
              </h2>
              <p className="text-gray-400 text-sm mt-1">
                {dashboard.reference_photos_validated} / {dashboard.reference_photos_count}{" "}
                aprobadas
              </p>
            </div>
            <button
              onClick={() => setShowUploadModal(true)}
              className="bg-gold hover:bg-gold/90 text-black font-bold px-4 py-2 rounded flex items-center gap-2 transition-colors"
            >
              <Upload className="h-4 w-4" />
              Subir Foto
            </button>
          </div>

          {dashboard.reference_photos_count === 0 ? (
            <div className="text-center py-12">
              <Camera className="h-12 w-12 text-gray-600 mx-auto mb-3" />
              <p className="text-gray-400 mb-4">
                Aún no has subido fotos de referencia.
              </p>
              <p className="text-gray-500 text-sm mb-6">
                Sube 1 foto frontal + 1 lateral de cada corte que haces.
                <br />
                Esto ayuda a VISAI a generar mejores análisis para tus clientes.
              </p>
              <button
                onClick={() => setShowUploadModal(true)}
                className="bg-gold hover:bg-gold/90 text-black font-bold px-6 py-2 rounded transition-colors"
              >
                Empezar a Subir
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {photos.map((photo) => (
                <div
                  key={photo.id}
                  className="bg-gray-800 rounded overflow-hidden group cursor-pointer"
                >
                  <div className="aspect-square bg-gray-700 flex items-center justify-center relative">
                    <img
                      src={photo.cloudinary_url}
                      alt={photo.haircut_type}
                      className="w-full h-full object-cover opacity-60 group-hover:opacity-100 transition-opacity"
                    />
                    {photo.validation_status === "approved" && (
                      <CheckCircle2 className="absolute h-6 w-6 text-green-500 bottom-2 right-2" />
                    )}
                    {photo.validation_status === "pending" && (
                      <Clock className="absolute h-6 w-6 text-yellow-500 bottom-2 right-2" />
                    )}
                  </div>
                  <div className="p-3">
                    <p className="text-white text-xs font-semibold">
                      {photo.haircut_type}
                    </p>
                    <p className="text-gray-400 text-xs">{photo.photo_angle}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick Links */}
        <div className="grid md:grid-cols-3 gap-4">
          <Link href={`/barber/leaderboard`}>
            <div className="bg-gray-900 border border-gray-800 hover:border-gold p-4 rounded-lg cursor-pointer transition-colors group">
              <Trophy className="h-6 w-6 text-gold mb-2 group-hover:scale-110 transition-transform" />
              <h3 className="text-white font-bold mb-1">Ver Leaderboard</h3>
              <p className="text-gray-400 text-sm">
                Compara tu ranking con otros barberos
              </p>
              <ChevronRight className="h-4 w-4 text-gold mt-2 group-hover:translate-x-1 transition-transform" />
            </div>
          </Link>

          <Link href="/">
            <div className="bg-gray-900 border border-gray-800 hover:border-gold p-4 rounded-lg cursor-pointer transition-colors group">
              <Upload className="h-6 w-6 text-gold mb-2 group-hover:scale-110 transition-transform" />
              <h3 className="text-white font-bold mb-1">Volver al Análisis</h3>
              <p className="text-gray-400 text-sm">Usa tu código con un nuevo cliente</p>
              <ChevronRight className="h-4 w-4 text-gold mt-2 group-hover:translate-x-1 transition-transform" />
            </div>
          </Link>

          <Link href="/">
            <div className="bg-gray-900 border border-gray-800 hover:border-gold p-4 rounded-lg cursor-pointer transition-colors group">
              <AlertCircle className="h-6 w-6 text-gold mb-2 group-hover:scale-110 transition-transform" />
              <h3 className="text-white font-bold mb-1">Preguntas Frecuentes</h3>
              <p className="text-gray-400 text-sm">Resuelve dudas sobre tu programa</p>
              <ChevronRight className="h-4 w-4 text-gold mt-2 group-hover:translate-x-1 transition-transform" />
            </div>
          </Link>
        </div>
      </div>

      {/* Upload Modal */}
      <ReferencePhotoUploadModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        barber_id={barberId}
        onSuccess={() => {
          setShowUploadModal(false);
          setRefreshKey((k) => k + 1);
        }}
      />
    </div>
  );
}

export default function BarberDashboard() {
  return (
    <Suspense fallback={
      <div style={{ minHeight: "100dvh", background: "var(--bg)", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div className="spinner" style={{ width: 48, height: 48 }} />
      </div>
    }>
      <BarberDashboardInner />
    </Suspense>
  );
}

function MetricCard({
  icon,
  label,
  value,
  subtext,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  subtext: string;
}) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
      <div className="text-gold mb-2">{icon}</div>
      <p className="text-gray-400 text-xs font-semibold mb-1">{label}</p>
      <p className="text-white text-2xl font-bold">{value}</p>
      <p className="text-gray-500 text-xs mt-1">{subtext}</p>
    </div>
  );
}
