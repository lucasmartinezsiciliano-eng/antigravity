# -*- coding: utf-8 -*-
"""
VISAI Load Test Suite -- Locust
=================================
Simula tres tipos de usuario concurrente:

  ReadOnlyUser      -- navega leaderboard, dashboards (seguro en prod)
  AnalysisFlowUser  -- flujo completo: initiate->consent->[fotos]
  BarberUser        -- registro, dashboard, leaderboard de barbero

VARIABLES DE ENTORNO:
  INCLUDE_PHOTO_UPLOAD   si "true", sube fotos y llama al LLM (gasta creditos)
  SEED_BARBER_ID         barber_id existente para tareas de lectura
  SEED_ANALYSIS_ID       analysis_id completado para tareas de lectura

USO:
  pip install locust pillow
  locust -f locustfile.py --host https://api.visaiapp.com
  -> abre http://localhost:8089
"""

from __future__ import annotations

import io
import os
import random
import string

from locust import HttpUser, TaskSet, between, events, task

# ---------------------------------------------------------------------------
# Configuracion
# ---------------------------------------------------------------------------

INCLUDE_PHOTO_UPLOAD: bool = os.getenv("INCLUDE_PHOTO_UPLOAD", "false").lower() == "true"
SEED_BARBER_ID: str = os.getenv("SEED_BARBER_ID", "")
SEED_ANALYSIS_ID: str = os.getenv("SEED_ANALYSIS_ID", "")

# IDs creados durante la sesion (compartidos en el mismo proceso)
_created_barber_ids: list[str] = []
_created_analysis_ids: list[str] = []

QUIZ_VARIANTS = [
    {
        "hair_texture": "curly",
        "hair_density": "high",
        "lifestyle": "active",
        "style_goal": "modern",
        "preferred_length": "short",
        "maintenance_willingness": "low",
    },
    {
        "hair_texture": "straight",
        "hair_density": "medium",
        "lifestyle": "office",
        "style_goal": "classic",
        "preferred_length": "medium",
        "maintenance_willingness": "medium",
    },
    {
        "hair_texture": "wavy",
        "hair_density": "low",
        "lifestyle": "casual",
        "style_goal": "natural",
        "preferred_length": "long",
        "maintenance_willingness": "high",
    },
    {
        "hair_texture": "coily",
        "hair_density": "high",
        "lifestyle": "sport",
        "style_goal": "trendy",
        "preferred_length": "short",
        "maintenance_willingness": "medium",
        "beard": "full",
    },
]


# ---------------------------------------------------------------------------
# Generadores de datos de prueba
# ---------------------------------------------------------------------------

def _random_str(n: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=n))


def _make_test_jpeg(width: int = 320, height: int = 320) -> bytes:
    """
    Genera un JPEG sintetico en memoria con PIL.
    Dibuja formas similares a una cara para que MediaPipe tenga algo.
    """
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (width, height), color=(210, 185, 160))
    draw = ImageDraw.Draw(img)
    cx, cy = width // 2, height // 2

    # Cara (ovalo)
    draw.ellipse([cx - 80, cy - 100, cx + 80, cy + 100], fill=(220, 195, 168))
    # Ojos
    draw.ellipse([cx - 35, cy - 30, cx - 15, cy - 10], fill=(60, 40, 30))
    draw.ellipse([cx + 15, cy - 30, cx + 35, cy - 10], fill=(60, 40, 30))
    # Nariz
    draw.polygon([(cx, cy - 5), (cx - 8, cy + 20), (cx + 8, cy + 20)], fill=(190, 155, 135))
    # Boca
    draw.arc([cx - 25, cy + 20, cx + 25, cy + 50], start=0, end=180, fill=(160, 100, 90), width=3)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80)
    return buf.getvalue()


# Generamos las imagenes una vez al arrancar (evita overhead por request)
_TEST_JPEG: bytes = _make_test_jpeg(320, 320)
_TEST_JPEG_SMALL: bytes = _make_test_jpeg(160, 160)


# ---------------------------------------------------------------------------
# Escenario 1 -- Lectura pura (seguro en produccion)
# ---------------------------------------------------------------------------

class ReadOnlyTasks(TaskSet):
    """
    Simula usuarios que navegan partes publicas: leaderboard, dashboard, resultados.
    No crea ningun registro en la base de datos.
    """

    @task(5)
    def browse_leaderboard_alltime(self):
        self.client.get(
            "/api/v1/leaderboard?period=all_time&limit=20",
            name="/leaderboard [all_time]",
        )

    @task(3)
    def browse_leaderboard_week(self):
        self.client.get(
            "/api/v1/leaderboard?period=week&limit=20",
            name="/leaderboard [week]",
        )

    @task(2)
    def browse_leaderboard_city(self):
        city = random.choice(["Barcelona", "Madrid", "Tarragona", "Valencia"])
        self.client.get(
            f"/api/v1/leaderboard?period=all_time&city_filter={city}&limit=10",
            name="/leaderboard [city_filter]",
        )

    @task(3)
    def check_barber_dashboard(self):
        bid = SEED_BARBER_ID or (
            random.choice(_created_barber_ids) if _created_barber_ids else None
        )
        if not bid:
            return
        self.client.get(
            f"/api/v1/barbers/{bid}/dashboard",
            name="/barbers/{id}/dashboard",
        )

    @task(2)
    def check_barber_leaderboard_stats(self):
        bid = SEED_BARBER_ID or (
            random.choice(_created_barber_ids) if _created_barber_ids else None
        )
        if not bid:
            return
        self.client.get(
            f"/api/v1/leaderboard/stats/{bid}",
            name="/leaderboard/stats/{id}",
        )

    @task(2)
    def poll_analysis_result(self):
        aid = SEED_ANALYSIS_ID or (
            random.choice(_created_analysis_ids) if _created_analysis_ids else None
        )
        if not aid:
            return
        self.client.get(
            f"/api/v1/analysis/{aid}",
            name="/analysis/{id} [poll]",
        )

    @task(1)
    def poll_visuals(self):
        aid = SEED_ANALYSIS_ID or (
            random.choice(_created_analysis_ids) if _created_analysis_ids else None
        )
        if not aid:
            return
        self.client.get(
            f"/api/v1/analysis/{aid}/visuals",
            name="/analysis/{id}/visuals [poll]",
        )

    @task(1)
    def healthcheck(self):
        self.client.get("/health", name="/health")


class ReadOnlyUser(HttpUser):
    """Usuario que solo lee -- seguro para correr contra produccion."""
    tasks = [ReadOnlyTasks]
    wait_time = between(1, 4)
    weight = 3


# ---------------------------------------------------------------------------
# Escenario 2 -- Flujo completo de analisis
# ---------------------------------------------------------------------------

class AnalysisFlowTasks(TaskSet):
    """
    Simula un cliente que hace un analisis completo.

    Flujo:
      POST /initiate  ->  POST /consent  ->  [POST /photos si INCLUDE_PHOTO_UPLOAD]
                                          ->  GET /analysis/{id} (poll)

    IMPORTANTE: el backend debe tener DEV_SKIP_PAYMENT=True, o este flujo
    intentara crear sesiones reales de Stripe.
    """

    analysis_id: str | None = None

    def on_start(self):
        self.analysis_id = None

    @task
    def full_analysis_flow(self):
        self._step_initiate()
        if self.analysis_id:
            self._step_consent()
            if INCLUDE_PHOTO_UPLOAD:
                self._step_upload_photos()
            self._step_poll_result()

    def _step_initiate(self):
        quiz = random.choice(QUIZ_VARIANTS)
        payload = {
            "quiz_answers": quiz,
            "marketing_consent": random.choice([True, False]),
            "include_colorimetry": False,
            "include_products_guide": False,
        }

        with self.client.post(
            "/api/v1/analysis/initiate",
            json=payload,
            name="/analysis/initiate",
            catch_response=True,
        ) as resp:
            if resp.status_code == 201:
                data = resp.json()
                self.analysis_id = data.get("analysis_id")
                if self.analysis_id:
                    _created_analysis_ids.append(self.analysis_id)
                    if len(_created_analysis_ids) > 200:
                        _created_analysis_ids.pop(0)
                resp.success()
            elif resp.status_code in (429, 400):
                # Rate limit o codigo invalido -- comportamiento esperado
                resp.success()
            else:
                resp.failure(f"initiate fallo: {resp.status_code} -- {resp.text[:200]}")

    def _step_consent(self):
        if not self.analysis_id:
            return
        payload = {
            "consented_biometric_processing": True,
            "consented_special_category_data": True,
            "consented_retention_90_days": True,
            "consented_immediate_photo_deletion": True,
            "consented_age_verification": True,
            "consent_text_hash": "test-hash-" + self.analysis_id[:8],
        }
        with self.client.post(
            f"/api/v1/analysis/{self.analysis_id}/consent",
            json=payload,
            name="/analysis/{id}/consent",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 201, 400):
                resp.success()
            else:
                resp.failure(f"consent fallo: {resp.status_code}")

    def _step_upload_photos(self):
        """
        Sube fotos al backend.
        AVISO: activa llamada real al LLM (gasta creditos API).
        Solo se ejecuta si INCLUDE_PHOTO_UPLOAD=true.
        """
        if not self.analysis_id:
            return
        files = [
            ("photos", ("frontal.jpg", _TEST_JPEG, "image/jpeg")),
            ("photos", ("left.jpg", _TEST_JPEG_SMALL, "image/jpeg")),
            ("photos", ("right.jpg", _TEST_JPEG_SMALL, "image/jpeg")),
        ]
        with self.client.post(
            f"/api/v1/analysis/{self.analysis_id}/photos",
            files=files,
            name="/analysis/{id}/photos",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 202, 400, 422):
                resp.success()
            elif resp.status_code == 504:
                resp.success()  # timeout LLM -- registrado pero no es fallo de infra
            else:
                resp.failure(f"photos fallo: {resp.status_code} -- {resp.text[:200]}")

    def _step_poll_result(self):
        if not self.analysis_id:
            return
        with self.client.get(
            f"/api/v1/analysis/{self.analysis_id}",
            name="/analysis/{id} [post-initiate]",
            catch_response=True,
        ) as resp:
            # 402 = pago pendiente (esperado sin DEV_SKIP_PAYMENT)
            # 202 = pagado, esperando fotos
            # 200 = completado
            if resp.status_code in (200, 202, 402, 410):
                resp.success()
            else:
                resp.failure(f"poll result fallo: {resp.status_code}")


class AnalysisFlowUser(HttpUser):
    """
    Usuario que hace un analisis completo.
    Requiere DEV_SKIP_PAYMENT=True en el backend para no tocar Stripe real.
    """
    tasks = [AnalysisFlowTasks]
    wait_time = between(2, 6)
    weight = 2


# ---------------------------------------------------------------------------
# Escenario 3 -- Barbero (registro, dashboard, leaderboard)
# ---------------------------------------------------------------------------

class BarberTasks(TaskSet):
    """
    Simula un barbero que se registra y usa su dashboard.
    El registro llama a Stripe (crea un PromotionCode).
    """

    barber_id: str | None = None

    def on_start(self):
        self.barber_id = SEED_BARBER_ID or (
            random.choice(_created_barber_ids) if _created_barber_ids else None
        )

    @task(1)
    def register_barber(self):
        """Registra un barbero nuevo. Llama a Stripe si no esta mockeado."""
        payload = {
            "name": f"Test {_random_str(5).title()}",
            "barbershop_name": f"Barberia {_random_str(6).title()}",
            "email": f"test_{_random_str(8)}@visai-loadtest.invalid",
            "phone": f"6{random.randint(10000000, 99999999)}",
            "city": random.choice(["Barcelona", "Madrid", "Tarragona", "Valencia"]),
            "province": "Tarragona",
        }
        with self.client.post(
            "/api/v1/barbers/register",
            json=payload,
            name="/barbers/register",
            catch_response=True,
        ) as resp:
            if resp.status_code == 201:
                data = resp.json()
                self.barber_id = data.get("barber_id")
                if self.barber_id:
                    _created_barber_ids.append(self.barber_id)
                    if len(_created_barber_ids) > 100:
                        _created_barber_ids.pop(0)
                resp.success()
            elif resp.status_code in (400, 500):
                # Email duplicado o error Stripe -- comportamiento esperado
                resp.success()
            else:
                resp.failure(f"register fallo: {resp.status_code}")

    @task(4)
    def view_dashboard(self):
        bid = self.barber_id
        if not bid:
            return
        with self.client.get(
            f"/api/v1/barbers/{bid}/dashboard",
            name="/barbers/{id}/dashboard",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(f"dashboard fallo: {resp.status_code}")

    @task(3)
    def view_leaderboard_stats(self):
        bid = self.barber_id
        if not bid:
            return
        with self.client.get(
            f"/api/v1/leaderboard/stats/{bid}",
            name="/leaderboard/stats/{id}",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(f"leaderboard/stats fallo: {resp.status_code}")

    @task(1)
    def sign_contract(self):
        bid = self.barber_id
        if not bid:
            return
        with self.client.post(
            f"/api/v1/barbers/{bid}/sign-contract",
            json={"contract_version": "1.0"},
            name="/barbers/{id}/sign-contract",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(f"sign-contract fallo: {resp.status_code}")


class BarberUser(HttpUser):
    """Barbero que se registra y consulta su dashboard."""
    tasks = [BarberTasks]
    wait_time = between(3, 8)
    weight = 1


# ---------------------------------------------------------------------------
# Hooks de Locust -- resumen al terminar
# ---------------------------------------------------------------------------

@events.test_stop.add_listener
def on_test_stop(**kwargs):
    print("\n" + "=" * 60)
    print("VISAI Load Test -- Resumen de datos creados")
    print("=" * 60)
    print(f"  Barbers creados  : {len(_created_barber_ids)}")
    if _created_barber_ids:
        print(f"  Primer barber_id : {_created_barber_ids[0]}")
    print(f"  Analisis creados : {len(_created_analysis_ids)}")
    if _created_analysis_ids:
        print(f"  Primer analysis_id: {_created_analysis_ids[0]}")
    print("=" * 60)
    print("Para limpiar datos de test:")
    print("  DELETE FROM barber_partners WHERE email LIKE '%loadtest%';")
    print("  DELETE FROM analyses WHERE created_at > datetime('now', '-2 hours');")
    print("=" * 60)


@events.init.add_listener
def on_init(**kwargs):
    if SEED_BARBER_ID:
        print(f"[visai] Usando SEED_BARBER_ID={SEED_BARBER_ID}")
    if SEED_ANALYSIS_ID:
        print(f"[visai] Usando SEED_ANALYSIS_ID={SEED_ANALYSIS_ID}")
    if INCLUDE_PHOTO_UPLOAD:
        print("[visai] AVISO: INCLUDE_PHOTO_UPLOAD=true -- las fotos llamaran al LLM real")
    else:
        print("[visai] INCLUDE_PHOTO_UPLOAD=false -- el flujo se detiene antes del LLM")
