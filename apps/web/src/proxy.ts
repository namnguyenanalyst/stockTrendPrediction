import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

function parseJwtPayload(jwtToken: string): Record<string, unknown> | null {
  try {
    const parts = jwtToken.split(".");
    if (parts.length !== 3 || parts.some((part) => !part)) return null;
    const base64Url = parts[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    );
    const payload = JSON.parse(jsonPayload);
    return payload && typeof payload === "object" ? (payload as Record<string, unknown>) : null;
  } catch {
    return null;
  }
}

function isValidNonExpiredJwt(jwtToken: string): boolean {
  const payload = parseJwtPayload(jwtToken);
  if (!payload || typeof payload.exp !== "number") return false;
  return payload.exp * 1000 > Date.now();
}

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const rawToken =
    request.cookies.get("access_token")?.value ||
    request.cookies.get("auth_token")?.value;
  const token = rawToken?.trim() || "";
  const isAuthenticated = Boolean(token.length > 0 && isValidNonExpiredJwt(token));

  // 1. Root path "/" -> redirect to "/dashboard"
  if (pathname === "/") {
    const url = request.nextUrl.clone();
    url.pathname = "/dashboard";
    return NextResponse.redirect(url);
  }

  // 2. Auth routes: "/login", "/register"
  const isAuthRoute =
    pathname.startsWith("/login") || pathname.startsWith("/register");
  if (isAuthRoute && isAuthenticated) {
    const url = request.nextUrl.clone();
    url.pathname = "/dashboard";
    return NextResponse.redirect(url);
  }

  // 3. Admin routes: "/admin" - Chỉ cho phép role ADMIN
  const isAdminRoute = pathname.startsWith("/admin");
  if (isAdminRoute) {
    if (!isAuthenticated) {
      const loginUrl = new URL("/login", request.url);
      loginUrl.searchParams.set("redirect", pathname);
      return NextResponse.redirect(loginUrl);
    }
    const payload = parseJwtPayload(token);
    const role = typeof payload?.role === "string" ? payload.role : null;
    if (role !== "admin") {
      const url = request.nextUrl.clone();
      url.pathname = "/dashboard";
      return NextResponse.redirect(url);
    }
    return NextResponse.next();
  }

  // 4. Protected routes: "/dashboard", "/backtest"
  const isProtectedRoute =
    pathname.startsWith("/dashboard") || pathname.startsWith("/backtest");
  if (isProtectedRoute && !isAuthenticated) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

// Tương thích ngược cho các unit test
export const middleware = proxy;

export const config = {
  matcher: [
    "/",
    "/dashboard/:path*",
    "/backtest/:path*",
    "/admin/:path*",
    "/login",
    "/register",
  ],
};
