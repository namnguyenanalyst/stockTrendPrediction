import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
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

  // 3. Protected routes: "/dashboard", "/backtest"
  const isProtectedRoute =
    pathname.startsWith("/dashboard") || pathname.startsWith("/backtest");
  if (isProtectedRoute && !isAuthenticated) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/",
    "/dashboard/:path*",
    "/backtest/:path*",
    "/login",
    "/register",
  ],
};
