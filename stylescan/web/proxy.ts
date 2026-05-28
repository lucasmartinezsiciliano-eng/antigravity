import { NextRequest, NextResponse } from "next/server";

const PUBLIC_BARBER_ROUTES = ["/barber/login", "/barber/leaderboard"];
const BARBER_HOST = "barberos.visaiapp.com";

export default function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const host = request.headers.get("host") ?? "";

  // barberos.visai.es → redirect root to barber login
  if (host.startsWith(BARBER_HOST) && (pathname === "/" || pathname === "")) {
    return NextResponse.redirect(new URL("/barber/dashboard", request.url));
  }

  if (!pathname.startsWith("/barber/")) return NextResponse.next();
  if (PUBLIC_BARBER_ROUTES.some((r) => pathname.startsWith(r))) return NextResponse.next();

  const token = request.cookies.get("barber_token")?.value;
  if (!token) {
    const loginUrl = new URL("/barber/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/", "/barber/:path*"],
};
