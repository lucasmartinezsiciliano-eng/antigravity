const TOKEN_KEY = "barber_token";
const ID_KEY = "barber_id";
const CODE_KEY = "barber_promo_code";

export function getBarberToken(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(new RegExp(`(?:^|; )${TOKEN_KEY}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

export function getBarberTokenFromCookieHeader(cookie: string): string | null {
  const match = cookie.match(new RegExp(`(?:^|; )${TOKEN_KEY}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

export function setBarberSession(token: string, barberId: string, promoCode: string) {
  const maxAge = 30 * 24 * 60 * 60; // 30 days
  const secure = location.protocol === "https:" ? "; Secure" : "";
  document.cookie = `${TOKEN_KEY}=${encodeURIComponent(token)}; path=/; max-age=${maxAge}; SameSite=Lax${secure}`;
  localStorage.setItem(ID_KEY, barberId);
  localStorage.setItem(CODE_KEY, promoCode);
}

export function clearBarberSession() {
  document.cookie = `${TOKEN_KEY}=; path=/; max-age=0`;
  localStorage.removeItem(ID_KEY);
  localStorage.removeItem(CODE_KEY);
}

export function getStoredBarberId(): string | null {
  if (typeof localStorage === "undefined") return null;
  return localStorage.getItem(ID_KEY);
}

export function getStoredPromoCode(): string | null {
  if (typeof localStorage === "undefined") return null;
  return localStorage.getItem(CODE_KEY);
}
