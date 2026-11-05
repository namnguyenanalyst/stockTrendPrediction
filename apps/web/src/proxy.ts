import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

function extractRoleFromJwt(jwtToken: string): string | null {
  try {
    const parts = jwtToken.split(".");
    if (parts.length < 2) return null;
    const base64Url = parts[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    );
    const payload = JSON.parse(jsonPayload);
    return payload.role || null;
  } catch {
    return null;
  }
}

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const token =
    request.cookies.get("access_token")?.value ||
    request.cookies.get("auth_token")?.value;
  const isAuthenticated = Boolean(token && token.trim().length > 0);

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
    const role = token ? extractRoleFromJwt(token) : null;
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
