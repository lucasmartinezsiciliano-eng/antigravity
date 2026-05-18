"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
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
} from "lucide-react";
import { api } from "@/lib/api";
import ReferencePhotoUploadModal from "@/components/ReferencePhotoUploadModal";

type BarberDashboardData = {
  barber_id: string;
  name: string;
  promo_code: string;
  clients_all_time: number;
  clients_this_week: number;
  all_time_ranking_position: number | null;
  current_tier: string;
  reference_photos_count: number;
  reference_photos_validated: number;
  total_earned_euros: number;
  pending_payout_euros: number;
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

export default function BarberDashboard() {
  const searchParams = useSearchParams();
  const barberId = searchParams.get("id") || "";

  const [dashboard, setDashboard] = useState<BarberDashboardData | null>(null);
  const [photos, setPhotos] = useState<ReferencePhoto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [copySuccess, setCopySuccess] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);

  useEffect(() => {
    const loadDashboard = async () => {
      if (!barberId) {
        setError("No barber ID provided");
        setLoading(false);
        return;
      }

      try {
        // Load dashboard stats
        const data = await api.getBarberDashboard(barberId);
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
  }, [barberId]);

  const copyPromoCode = () => {
    if (dashboard?.promo_code) {
      navigator.clipboard.writeText(dashboard.promo_code);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="animate-spin">
          <div className="h-12 w-12 border-4 border-gold border-t-transparent rounded-full" />
        </div>
      </div>
    );
  }

  if (error || !dashboard) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <p className="text-white text-lg">{error || "Dashboard not found"}</p>
          <Link href="/" className="text-gold hover:underline mt-4 inline-block">
            Volver al inicio
          </Link>
        </div>
      </div>
    );
  }

  const tier = TIER_BADGES[dashboard.current_tier] || TIER_BADGES.bronze;

  return (
    <div className="min-h-screen bg-black">
      {/* Header */}
      <div className="border-b border-gray-800 bg-gradient-to-b from-gray-900 to-black">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-white mb-2">{dashboard.name}</h1>
          <p className="text-gray-400">Tu panel de control VISAI</p>
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
              Comparte con tus clientes • Ellos ahorran €2 • Tú ganas €2
            </p>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid md:grid-cols-4 gap-4 mb-8">
          <MetricCard
            icon={<Users className="h-6 w-6" />}
            label="Esta Semana"
            value={dashboard.clients_this_week}
            subtext="análisis completados"
          />
          <MetricCard
            icon={<TrendingUp className="h-6 w-6" />}
            label="Total (All-Time)"
            value={dashboard.clients_all_time}
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
        barber_id={barber_id}
        onSuccess={() => {
          // Refresh dashboard data after successful upload
          window.location.reload();
        }}
      />
    </div>
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
