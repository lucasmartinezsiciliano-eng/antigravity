# VISAI MVP — Integration Map

## API Endpoints & Frontend Integration

Backend is **100% complete**. Frontend has **mock data**. This document maps which frontend pages need API integration.

---

## 1. BARBER DASHBOARD (`/barber/dashboard?id={barber_id}`)

### Current State
- ✅ Page exists: `stylescan/web/app/barber/dashboard/page.tsx`
- ⚠️ Using mock data

### Required API Calls

#### GET `/api/v1/barbers/{id}/dashboard`
**Current Mock:**
```typescript
GET /api/v1/barbers/{barber_id}/dashboard
Response: BarberDashboard {
  barber_id, name, promo_code, total_uses, 
  total_earned_euros, pending_payout_euros, recent_uses
}
```

**Frontend Location:** Line ~68 in `dashboard/page.tsx`
```typescript
// TODO: Replace with actual API call
// const data = await api.getBarberDashboard(barberId);
// setDashboard(data);
```

**Action:** 
1. Implement `api.getBarberDashboard(barber_id)` in `lib/api.ts`
2. Replace mock data with real call
3. Handle 404 (barber not found)

---

#### GET `/api/v1/barbers/{id}/reference-photos`
**Current Mock:** Returns `[]`

**Frontend Location:** Line ~80 in `dashboard/page.tsx`
```typescript
// TODO: Replace with actual API call
// const photosData = await api.getBarberReferencePhotos(barberId);
// setPhotos(photosData);
```

**Response Schema:**
```json
[
  {
    "id": "photo_id",
    "haircut_type": "fade",
    "photo_angle": "frontal",
    "cloudinary_url": "https://...",
    "validation_status": "approved|pending|rejected",
    "quality_score": 0.95,
    "created_at": "2026-05-15T..."
  }
]
```

**Action:**
1. Implement `api.getBarberReferencePhotos(barber_id)` in `lib/api.ts`
2. Replace mock data with real call

---

#### POST `/api/v1/barbers/{id}/reference-photos`
**Used By:** `ReferencePhotoUploadModal.tsx` (line ~173)

**Current Mock:**
```typescript
// await new Promise((resolve) => setTimeout(resolve, 2000));
// setQualityScore(0.92);
```

**Frontend Location:** `components/ReferencePhotoUploadModal.tsx`
```typescript
// TODO: Replace with actual API call
// const formData = new FormData();
// formData.append("file", file);
// ...
// const response = await fetch(`/api/v1/barbers/${barber_id}/reference-photos`, {...});
```

**Multipart Form:**
```
Content-Type: multipart/form-data
- file: File (binary)
- haircut_type: string (enum from HaircutType)
- photo_angle: string ("frontal" | "lateral")
```

**Response:**
```json
{
  "photo_id": "...",
  "status": "pending_validation",
  "quality_score": 0.92,
  "message": "Foto subida. Será validada en las próximas 24h."
}
```

**Action:**
1. Implement form data upload in modal
2. Wire API call to `/api/v1/barbers/{barber_id}/reference-photos`
3. Handle upload progress
4. Refresh photo list on success

---

## 2. LEADERBOARD (`/barber/leaderboard?period=...`)

### Current State
- ✅ Page exists: `stylescan/web/app/barber/leaderboard/page.tsx`
- ⚠️ Using mock data (5 entries)

### Required API Calls

#### GET `/api/v1/leaderboard?period={period}&city={city}&limit={limit}&offset={offset}`

**Query Parameters:**
- `period`: "week" | "month" | "all_time" (default: "all_time")
- `city_filter`: string (optional, e.g., "Barcelona")
- `limit`: int (1-100, default: 50)
- `offset`: int (default: 0)

**Response:**
```json
[
  {
    "rank": 1,
    "barber_id": "...",
    "barber_name": "...",
    "barbershop_name": "...",
    "city": "Barcelona",
    "clients_this_period": 89,
    "clients_all_time": 892,
    "current_tier": "platinum|gold|silver|bronze",
    "instagram_handle": "username" (optional)
  }
]
```

**Frontend Location:** Line ~62 in `leaderboard/page.tsx`
```typescript
// TODO: Replace with actual API call
// const data = await api.getLeaderboard(period, cityFilter);
// setEntries(data);
```

**Action:**
1. Implement `api.getLeaderboard(period, cityFilter, limit, offset)` in `lib/api.ts`
2. Replace mock data with real call
3. Pagination (load more button if offset > 0)

---

## 3. LEADERBOARD STATS (`/api/v1/leaderboard/stats/{barber_id}`)

**Not Yet Used** but needed for:
- Individual barber stats view
- Reference photo count/validation status

**Would Be Called From:**
- Potential detail page: `/barber/stats/{barber_id}`

**Response:**
```json
{
  "barber_id": "...",
  "name": "...",
  "city": "...",
  "clients_all_time": 892,
  "clients_this_week": 18,
  "clients_this_month": 67,
  "all_time_ranking_position": 1,
  "week_ranking_position": 3,
  "current_tier": "platinum",
  "reference_photos_count": 16,
  "reference_photos_validated": 14
}
```

---

## 4. PARENTAL CONSENT (`/parental-consent/authorize?token={token}`)

### Current State
- ✅ Page exists: `stylescan/web/app/parental-consent/authorize/page.tsx`
- ⚠️ Using mock authorization (always succeeds)

### Required API Calls

#### POST `/api/v1/parental-consent/request`

**Request Body:**
```json
{
  "analysis_id": "...",
  "child_age": 15,
  "parent_email": "parent@example.com"
}
```

**Response:**
```json
{
  "request_id": "...",
  "status": "pending",
  "token_expires_at": "2026-05-18T...",
  "authorization_url": "https://visaiapp.com/parental-consent/authorize?token=..."
}
```

**Frontend Location:** Used in `analysis.py` route (backend triggers email)

**Action:**
- Called automatically when `age < 18` detected in `/api/v1/analysis`
- Backend sends email via Resend
- No frontend call needed (server-side)

---

#### GET `/api/v1/parental-consent/authorize?token={token}`

**Current Mock:** Line ~46 in `authorize/page.tsx`
```typescript
// await new Promise((resolve) => setTimeout(resolve, 1500));
// setStatus("authorized");
```

**Response Options:**
```json
// Success
{ "status": "authorized", "is_authorized": true, "message": "..." }

// Expired
{ "status": "expired", "error": "Token expirado..." }

// Invalid
{ "status": "error", "error": "Token no válido..." }
```

**Frontend Location:** Line ~26 in `authorize/page.tsx`
```typescript
// TODO: Replace with actual API call
// const response = await api.authorizeParentalConsent(token);
```

**Action:**
1. Implement `api.authorizeParentalConsent(token)` in `lib/api.ts`
2. Replace mock with real call
3. Handle 3 states: authorized, expired, error

---

#### GET `/api/v1/parental-consent/{token}/status`

**Optional** - for checking status without authorizing (not yet used)

**Response:**
```json
{
  "request_id": "...",
  "status": "pending|authorized|expired",
  "is_authorized": boolean,
  "token_expires_at": "..."
}
```

---

## 5. TELEGRAM INTEGRATION

### Current State
- ✅ Backend webhook ready: `POST /api/v1/telegram/webhook`
- ❌ No frontend UI for connecting Telegram

### Required API Calls

#### POST `/api/v1/barbers/{id}/telegram/connect`

**Request Body:**
```json
{
  "telegram_user_id": 123456789,
  "telegram_chat_id": 123456789,
  "telegram_username": "username",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response:**
```json
{
  "status": "connected",
  "message": "¡Hola John! Recibirás notificaciones en tiempo real..."
}
```

**Frontend:** Not yet implemented. Would need:
1. Telegram bot `/start` command → deep link to barber dashboard
2. OAuth flow to get telegram_user_id
3. Call this endpoint to register

---

#### PUT `/api/v1/barbers/{id}/telegram/preferences`

**Request Body:**
```json
{
  "notifications_enabled": true,
  "notify_on_new_analysis": true,
  "notify_on_ranking_change": true,
  "notify_on_weekly_summary": true,
  "language_code": "es"
}
```

**Frontend:** Settings page in barber dashboard (not yet created)

---

## Implementation Priority

### Phase 1 (MVP — by May 19)
1. ✅ Backend: **100% complete**
2. ⚠️ Frontend: **Mock → Real API**
   - [ ] `api.getBarberDashboard()`
   - [ ] `api.getBarberReferencePhotos()`
   - [ ] Photo upload form → `/api/v1/barbers/{id}/reference-photos`
   - [ ] `api.getLeaderboard()`
   - [ ] `api.authorizeParentalConsent()`

### Phase 2 (Week 2)
3. [ ] Telegram OAuth / deep linking
4. [ ] Background jobs (leaderboard updates)
5. [ ] Photo validation dashboard (admin)

### Phase 3 (Week 3+)
6. [ ] Analytics dashboard
7. [ ] Payout management (Stripe Connect)

---

## lib/api.ts — Functions to Implement

```typescript
// Barbers
export async function getBarberDashboard(barber_id: string): Promise<BarberDashboard>
export async function getBarberReferencePhotos(barber_id: string): Promise<ReferencePhoto[]>
export async function deleteReferencePhoto(barber_id: string, photo_id: string): Promise<void>

// Leaderboard
export async function getLeaderboard(
  period: "week" | "month" | "all_time",
  cityFilter?: string,
  limit?: number,
  offset?: number
): Promise<LeaderboardEntry[]>

export async function getBarberLeaderboardStats(barber_id: string): Promise<BarberLeaderboardStats>

// Parental Consent
export async function authorizeParentalConsent(token: string): Promise<ConsentResponse>

// Telegram (future)
export async function connectTelegram(barber_id: string, data: TelegramConnectRequest): Promise<void>
```

---

## Testing Checklist

- [ ] Test dashboard with 100+ photos (pagination)
- [ ] Test leaderboard filtering (city, period)
- [ ] Test parental consent with expired token
- [ ] Test photo upload with large file (>10MB rejected)
- [ ] Test photo upload with invalid format (non-image rejected)
- [ ] Mobile responsiveness (all pages)
- [ ] Error handling (404, 500, network timeout)

---

**Last Updated:** 2026-05-15
**Status:** Backend 100% done, Frontend needs API wiring
