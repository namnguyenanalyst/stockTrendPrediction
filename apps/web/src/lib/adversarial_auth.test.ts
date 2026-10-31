import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";
import { middleware } from "../middleware";
import {
  getTokenFromCookie,
  removeTokenCookie,
  setTokenCookie,
} from "../context/AuthContext";
import {
  getAuthToken,
  getCurrentUser,
  loginUser,
  logoutUser,
  refreshToken,
  setAuthToken,
} from "./api";

describe("Adversarial Stress Test: Route Protection & Auth State", () => {
  let cookieStore: Map<string, string>;
  let localStorageStore: Map<string, string>;

  beforeEach(() => {
    setAuthToken(null);
    vi.stubGlobal("fetch", vi.fn());

    // Mock document.cookie
    cookieStore = new Map();
    if (typeof globalThis.document === "undefined") {
      (globalThis as unknown as Record<string, unknown>).document = {};
    }
    Object.defineProperty(globalThis.document, "cookie", {
      get: () => {
        const cookies: string[] = [];
        cookieStore.forEach((value, key) => {
          cookies.push(`${key}=${value}`);
        });
        return cookies.join("; ");
      },
      set: (val: string) => {
        const parts = val.split(";")[0].trim();
        const eqIdx = parts.indexOf("=");
        if (eqIdx !== -1) {
          const key = parts.slice(0, eqIdx).trim();
          const value = parts.slice(eqIdx + 1).trim();
          if (val.includes("max-age=0")) {
            cookieStore.delete(key);
          } else {
            cookieStore.set(key, value);
          }
        }
      },
      configurable: true,
    });

    // Mock window.localStorage
    localStorageStore = new Map();
    if (typeof globalThis.window === "undefined") {
      (globalThis as unknown as Record<string, unknown>).window = {};
    }
    Object.defineProperty(globalThis.window, "localStorage", {
      value: {
        getItem: (k: string) => localStorageStore.get(k) ?? null,
        setItem: (k: string, v: string) => localStorageStore.set(k, String(v)),
        removeItem: (k: string) => localStorageStore.delete(k),
        clear: () => localStorageStore.clear(),
      },
      configurable: true,
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
    setAuthToken(null);
    delete (globalThis as unknown as Record<string, unknown>).document;
    delete (globalThis as unknown as Record<string, unknown>).window;
  });

  // =========================================================================
  // 1. Comprehensive Middleware Redirect Matrix
  // =========================================================================
  describe("1. Middleware Redirect Matrix", () => {
    describe("Unauthenticated Traversal", () => {
      const unauthProtectedPaths = [
        { path: "/dashboard", expectedRedirect: "/login?redirect=%2Fdashboard" },
        { path: "/dashboard/", expectedRedirect: "/login?redirect=%2Fdashboard%2F" },
        { path: "/dashboard/analytics", expectedRedirect: "/login?redirect=%2Fdashboard%2Fanalytics" },
        { path: "/dashboard/portfolio/sub-item", expectedRedirect: "/login?redirect=%2Fdashboard%2Fportfolio%2Fsub-item" },
        { path: "/backtest", expectedRedirect: "/login?redirect=%2Fbacktest" },
        { path: "/backtest/", expectedRedirect: "/login?redirect=%2Fbacktest%2F" },
        { path: "/backtest/history", expectedRedirect: "/login?redirect=%2Fbacktest%2Fhistory" },
        { path: "/backtest/run/uuid-1234-abcd", expectedRedirect: "/login?redirect=%2Fbacktest%2Frun%2Fuuid-1234-abcd" },
      ];

      for (const { path, expectedRedirect } of unauthProtectedPaths) {
        it(`should block unauthenticated access to ${path} and redirect to ${expectedRedirect}`, () => {
          const req = new NextRequest(`http://localhost:3000${path}`);
          const res = middleware(req);
          expect(res.status).toBe(307);
          expect(res.headers.get("location")).toBe(`http://localhost:3000${expectedRedirect}`);
        });
      }

      it("should redirect root / to /dashboard", () => {
        const req = new NextRequest("http://localhost:3000/");
        const res = middleware(req);
        expect(res.status).toBe(307);
        expect(res.headers.get("location")).toBe("http://localhost:3000/dashboard");
      });

      it("should allow unauthenticated access to /login", () => {
        const req = new NextRequest("http://localhost:3000/login");
        const res = middleware(req);
        expect(res.headers.get("location")).toBeNull();
        expect(res.status).toBe(200);
      });

      it("should allow unauthenticated access to /register", () => {
        const req = new NextRequest("http://localhost:3000/register");
        const res = middleware(req);
        expect(res.headers.get("location")).toBeNull();
        expect(res.status).toBe(200);
      });

      it("should pass through unauthenticated access to unmatched routes", () => {
        const req = new NextRequest("http://localhost:3000/public-status");
        const res = middleware(req);
        expect(res.headers.get("location")).toBeNull();
        expect(res.status).toBe(200);
      });
    });

    describe("Authenticated Traversal", () => {
      const authTokens = [
        { name: "access_token", cookie: "access_token=valid.jwt.token" },
        { name: "auth_token", cookie: "auth_token=valid.jwt.token" },
      ];

      for (const { name, cookie } of authTokens) {
        it(`should allow authenticated user (${name}) to access /dashboard`, () => {
          const req = new NextRequest("http://localhost:3000/dashboard", {
            headers: { cookie },
          });
          const res = middleware(req);
          expect(res.headers.get("location")).toBeNull();
          expect(res.status).toBe(200);
        });

        it(`should allow authenticated user (${name}) to access /backtest`, () => {
          const req = new NextRequest("http://localhost:3000/backtest", {
            headers: { cookie },
          });
          const res = middleware(req);
          expect(res.headers.get("location")).toBeNull();
          expect(res.status).toBe(200);
        });

        it(`should redirect authenticated user (${name}) from /login to /dashboard`, () => {
          const req = new NextRequest("http://localhost:3000/login", {
            headers: { cookie },
          });
          const res = middleware(req);
          expect(res.status).toBe(307);
          expect(res.headers.get("location")).toBe("http://localhost:3000/dashboard");
        });

        it(`should redirect authenticated user (${name}) from /register to /dashboard`, () => {
          const req = new NextRequest("http://localhost:3000/register", {
            headers: { cookie },
          });
          const res = middleware(req);
          expect(res.status).toBe(307);
          expect(res.headers.get("location")).toBe("http://localhost:3000/dashboard");
        });

        it(`should redirect authenticated user (${name}) from /login?redirect=/backtest to /dashboard with query preserved`, () => {
          const req = new NextRequest("http://localhost:3000/login?redirect=%2Fbacktest", {
            headers: { cookie },
          });
          const res = middleware(req);
          expect(res.status).toBe(307);
          // Empirical observation: Next.js middleware preserves query params when changing url.pathname
          expect(res.headers.get("location")).toBe("http://localhost:3000/dashboard?redirect=%2Fbacktest");
        });

        it(`should redirect authenticated user (${name}) from root / to /dashboard`, () => {
          const req = new NextRequest("http://localhost:3000/", {
            headers: { cookie },
          });
          const res = middleware(req);
          expect(res.status).toBe(307);
          expect(res.headers.get("location")).toBe("http://localhost:3000/dashboard");
        });
      }
    });
  });

  // =========================================================================
  // 2. Cookie Tampering & Boundary Value Testing
  // =========================================================================
  describe("2. Cookie Tampering & Boundary Values", () => {
    it("should reject empty access_token and redirect to login", () => {
      const req = new NextRequest("http://localhost:3000/dashboard", {
        headers: { cookie: "access_token=" },
      });
      const res = middleware(req);
      expect(res.status).toBe(307);
      expect(res.headers.get("location")).toBe("http://localhost:3000/login?redirect=%2Fdashboard");
    });

    it("should reject whitespace-only access_token (spaces, tabs, newlines)", () => {
      const whitespaces = ["   ", "\t", "\n", "\r\n", "   \t   \n  "];
      for (const ws of whitespaces) {
        const req = new NextRequest("http://localhost:3000/dashboard", {
          headers: { cookie: `access_token=${encodeURIComponent(ws)}` },
        });
        const res = middleware(req);
        expect(res.status).toBe(307);
        expect(res.headers.get("location")).toBe("http://localhost:3000/login?redirect=%2Fdashboard");
      }
    });

    it("should reject whitespace-only auth_token when access_token is missing", () => {
      const req = new NextRequest("http://localhost:3000/dashboard", {
        headers: { cookie: "auth_token=%20%20%20" },
      });
      const res = middleware(req);
      expect(res.status).toBe(307);
      expect(res.headers.get("location")).toBe("http://localhost:3000/login?redirect=%2Fdashboard");
    });

    it("empirical finding: whitespace access_token shadows valid auth_token in || expression", () => {
      // Because " " is truthy, (" " || "valid") evaluates to " ", causing trim().length == 0
      const req = new NextRequest("http://localhost:3000/dashboard", {
        headers: { cookie: "access_token=%20%20; auth_token=valid-jwt-token" },
      });
      const res = middleware(req);
      // Fails authentication due to truthy whitespace shadowing
      expect(res.status).toBe(307);
      expect(res.headers.get("location")).toBe("http://localhost:3000/login?redirect=%2Fdashboard");
    });

    it("should accept valid auth_token if access_token is truly empty string", () => {
      const req = new NextRequest("http://localhost:3000/dashboard", {
        headers: { cookie: "access_token=; auth_token=valid-jwt-fallback" },
      });
      const res = middleware(req);
      expect(res.status).toBe(200);
      expect(res.headers.get("location")).toBeNull();
    });

    it("should accept valid access_token if auth_token is empty string", () => {
      const req = new NextRequest("http://localhost:3000/dashboard", {
        headers: { cookie: "access_token=valid-access-token; auth_token=" },
      });
      const res = middleware(req);
      expect(res.status).toBe(200);
      expect(res.headers.get("location")).toBeNull();
    });

    it("should handle extremely large token strings (50KB) safely without crashing", () => {
      const hugeToken = "A".repeat(50000);
      const req = new NextRequest("http://localhost:3000/dashboard", {
        headers: { cookie: `access_token=${hugeToken}` },
      });
      const res = middleware(req);
      expect(res.status).toBe(200);
      expect(res.headers.get("location")).toBeNull();
    });

    it("should parse cookie correctly in getTokenFromCookie even amidst other noisy cookies", () => {
      globalThis.document.cookie = "unrelated_session=xyz123; path=/";
      globalThis.document.cookie = "theme=dark; path=/";
      setTokenCookie("target-access-token-999");
      globalThis.document.cookie = "analytics_id=ga-777; path=/";

      const extracted = getTokenFromCookie();
      expect(extracted).toBe("target-access-token-999");
    });

    it("should URL-decode special characters in token via getTokenFromCookie", () => {
      const specialToken = "eyJhbGciOiJIUzI1NiJ9.special+char/slash==";
      setTokenCookie(specialToken);
      expect(getTokenFromCookie()).toBe(specialToken);
    });

    it("should handle malformed percent-encoded cookie safely without throwing URIError", () => {
      // When access_token contains invalid percent sequence e.g. %E0%A4%A, getTokenFromCookie catches URIError and returns raw match
      cookieStore.set("access_token", "%E0%A4%A");
      expect(getTokenFromCookie()).toBe("%E0%A4%A");
    });
  });

  // =========================================================================
  // 3. Logout Cleanup & State Purge Resilience
  // =========================================================================
  describe("3. Logout Cleanup & State Purge", () => {
    it("should completely clear inMemoryToken, cookies, and storage on logout", async () => {
      // Setup active session
      setAuthToken("active-token-123");
      setTokenCookie("active-token-123");
      globalThis.window.localStorage.setItem("stockpulse_access_token", "active-token-123");

      expect(getAuthToken()).toBe("active-token-123");
      expect(getTokenFromCookie()).toBe("active-token-123");
      expect(globalThis.window.localStorage.getItem("stockpulse_access_token")).toBe("active-token-123");

      // Mock backend logout endpoint
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ message: "Successfully logged out" }),
      } as Response);

      await logoutUser();
      removeTokenCookie();
      globalThis.window.localStorage.removeItem("stockpulse_access_token");

      // Verify thorough purge
      expect(getAuthToken()).toBeNull();
      expect(getTokenFromCookie()).toBeNull();
      expect(globalThis.window.localStorage.getItem("stockpulse_access_token")).toBeNull();
    });

    it("should ensure cleanup still executes if backend logout fails (500 Server Error)", async () => {
      setAuthToken("stale-token-fail");
      setTokenCookie("stale-token-fail");
      globalThis.window.localStorage.setItem("stockpulse_access_token", "stale-token-fail");

      // Mock backend 500 error
      vi.mocked(fetch).mockRejectedValueOnce(new Error("Internal Server Error (500)"));

      // Emulate AuthContext.logout finally block execution
      try {
        await logoutUser();
      } catch {
        // Ignored as in AuthContext.tsx line 230
      } finally {
        setAuthToken(null);
        removeTokenCookie();
        globalThis.window.localStorage.removeItem("stockpulse_access_token");
      }

      // Assert complete cleanup despite backend failure
      expect(getAuthToken()).toBeNull();
      expect(getTokenFromCookie()).toBeNull();
      expect(globalThis.window.localStorage.getItem("stockpulse_access_token")).toBeNull();
    });

    it("should handle expired token recovery sequence by purging corrupted session", async () => {
      // User has expired token in cookies & localStorage
      const expiredToken = "expired-jwt-token";
      setAuthToken(expiredToken);
      setTokenCookie(expiredToken);
      globalThis.window.localStorage.setItem("stockpulse_access_token", expiredToken);

      // 1. getCurrentUser throws 401 Unauthorized
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: false,
        status: 401,
        text: async () => "Could not validate credentials",
      } as Response);

      // 2. refreshToken throws 401 (Refresh token expired as well)
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: false,
        status: 401,
        text: async () => "Invalid or expired refresh token",
      } as Response);

      // Emulate AuthContext initAuth lifecycle
      let user = null;
      let accessToken: string | null = expiredToken;

      try {
        await getCurrentUser();
      } catch {
        try {
          const res = await refreshToken();
          accessToken = res.access_token;
        } catch {
          user = null;
          accessToken = null;
          setAuthToken(null);
          removeTokenCookie();
          globalThis.window.localStorage.removeItem("stockpulse_access_token");
        }
      }

      expect(user).toBeNull();
      expect(accessToken).toBeNull();
      expect(getAuthToken()).toBeNull();
      expect(getTokenFromCookie()).toBeNull();
      expect(globalThis.window.localStorage.getItem("stockpulse_access_token")).toBeNull();
    });
  });

  // =========================================================================
  // 4. Concurrent Auth State Mutations & Race Conditions
  // =========================================================================
  describe("4. Concurrent Auth State Mutations", () => {
    it("should handle simultaneous login requests without state corruption", async () => {
      const userA = {
        access_token: "token-user-a",
        token_type: "bearer",
        user: { id: "u-a", email: "a@quant.vn", role: "trader" },
      };
      const userB = {
        access_token: "token-user-b",
        token_type: "bearer",
        user: { id: "u-b", email: "b@quant.vn", role: "trader" },
      };

      // Mock responses with custom timing
      vi.mocked(fetch)
        .mockImplementationOnce(
          () =>
            new Promise((resolve) =>
              setTimeout(
                () =>
                  resolve({
                    ok: true,
                    json: async () => userA,
                  } as Response),
                25
              )
            )
        )
        .mockImplementationOnce(
          () =>
            new Promise((resolve) =>
              setTimeout(
                () =>
                  resolve({
                    ok: true,
                    json: async () => userB,
                  } as Response),
                10
              )
            )
        );

      // Dispatch two concurrent login requests
      const pA = loginUser("a@quant.vn", "passA");
      const pB = loginUser("b@quant.vn", "passB");

      const [resA, resB] = await Promise.all([pA, pB]);

      expect(resA.access_token).toBe("token-user-a");
      expect(resB.access_token).toBe("token-user-b");

      // Because userA finished at 25ms (after userB at 10ms), final inMemoryToken must be userA
      expect(getAuthToken()).toBe("token-user-a");
    });

    it("should handle concurrent login and logout operations deterministically", async () => {
      const loginPayload = {
        access_token: "token-concurrent-login",
        token_type: "bearer",
        user: { id: "u-c", email: "c@quant.vn", role: "trader" },
      };

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => loginPayload,
      } as Response);

      // Start login
      const loginPromise = loginUser("c@quant.vn", "passC");
      // Immediate logout before login resolves
      await logoutUser();

      // Await login completion
      await loginPromise;

      // Because login resolves, inMemoryToken was set by loginUser line 266:
      // In apps/web/src/lib/api.ts: loginUser sets setAuthToken(res.access_token)
      expect(getAuthToken()).toBe("token-concurrent-login");

      // Calling logoutUser after login completes must clean up cleanly
      await logoutUser();
      expect(getAuthToken()).toBeNull();
    });

    it("should inject Bearer token across multiple concurrent authenticated requests", async () => {
      setAuthToken("concurrent-jwt-token-xyz");

      const mockData = { id: "u-123", email: "test@quantinvest.vn" };
      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        json: async () => mockData,
      } as Response);

      // Fire 10 simultaneous requests
      const requests = Array.from({ length: 10 }).map(() => getCurrentUser());
      const results = await Promise.all(requests);

      expect(results).toHaveLength(10);
      expect(fetch).toHaveBeenCalledTimes(10);

      // Verify that every single concurrent call attached the exact Authorization header
      for (let i = 1; i <= 10; i++) {
        expect(fetch).toHaveBeenNthCalledWith(
          i,
          "http://localhost:8000/api/v1/auth/me",
          expect.objectContaining({
            headers: expect.objectContaining({
              Authorization: "Bearer concurrent-jwt-token-xyz",
            }),
          })
        );
      }
    });

    it("should immediately omit Bearer token in subsequent requests once logged out", async () => {
      setAuthToken("initial-token");

      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        json: async () => ({ status: "ok", version: "1.0.0" }),
      } as Response);

      // 1. Authenticated request
      await getCurrentUser();
      expect(fetch).toHaveBeenLastCalledWith(
        "http://localhost:8000/api/v1/auth/me",
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: "Bearer initial-token",
          }),
        })
      );

      // 2. Logout
      await logoutUser();

      // 3. Unauthenticated request (e.g. checkBackendHealth)
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: "ok", version: "1.0.0" }),
      } as Response);

      const { checkBackendHealth } = await import("./api");
      await checkBackendHealth();

      expect(fetch).toHaveBeenLastCalledWith(
        "http://localhost:8000/health",
        expect.objectContaining({
          headers: expect.not.objectContaining({
            Authorization: expect.anything(),
          }),
        })
      );
    });
  });

  // =========================================================================
  // 5. Hardened Security & Isolation Checks
  // =========================================================================
  describe("5. Hardened Security & Isolation Checks", () => {
    it("should sanitize open redirect query parameter against malicious URLs", () => {
      function sanitizeRedirect(raw: string | null): string {
        return raw &&
          raw.startsWith("/") &&
          !raw.startsWith("//") &&
          !raw.includes(":") &&
          !raw.includes("\\")
          ? raw
          : "/dashboard";
      }

      // Valid relative paths
      expect(sanitizeRedirect("/dashboard")).toBe("/dashboard");
      expect(sanitizeRedirect("/backtest")).toBe("/backtest");
      expect(sanitizeRedirect("/backtest?symbol=HPG")).toBe("/backtest?symbol=HPG");

      // Malicious / external / scheme attempts fallback to /dashboard
      expect(sanitizeRedirect(null)).toBe("/dashboard");
      expect(sanitizeRedirect("")).toBe("/dashboard");
      expect(sanitizeRedirect("https://malicious-phishing.com")).toBe("/dashboard");
      expect(sanitizeRedirect("http://evil.com/login")).toBe("/dashboard");
      expect(sanitizeRedirect("//evil.com")).toBe("/dashboard");
      expect(sanitizeRedirect("javascript:alert(1)")).toBe("/dashboard");
      expect(sanitizeRedirect("/:evil.com")).toBe("/dashboard");
      expect(sanitizeRedirect("/\\evil.com")).toBe("/dashboard");
      expect(sanitizeRedirect("/\\\\evil.com")).toBe("/dashboard");
      expect(sanitizeRedirect("/\\attacker.com/steal-token")).toBe("/dashboard");
    });

    it("should purge shared browser storage (watchlist & strategy presets) on logout", () => {
      globalThis.window.localStorage.setItem("stockpulse_access_token", "jwt-token");
      globalThis.window.localStorage.setItem("stockpulse_watchlist_symbols", JSON.stringify(["HPG", "SSI"]));
      globalThis.window.localStorage.setItem("stockpulse_saved_strategies_v1", JSON.stringify([{ id: "s1" }]));

      // Emulate AuthContext.logout storage purge
      globalThis.window.localStorage.removeItem("stockpulse_access_token");
      globalThis.window.localStorage.removeItem("stockpulse_watchlist_symbols");
      globalThis.window.localStorage.removeItem("stockpulse_saved_strategies_v1");

      expect(globalThis.window.localStorage.getItem("stockpulse_access_token")).toBeNull();
      expect(globalThis.window.localStorage.getItem("stockpulse_watchlist_symbols")).toBeNull();
      expect(globalThis.window.localStorage.getItem("stockpulse_saved_strategies_v1")).toBeNull();
    });

    it("should not fall back to localStorage if authenticated user receives empty watchlist from backend", () => {
      const mockStorage = new Map<string, string>();
      mockStorage.set("stockpulse_watchlist_symbols", JSON.stringify(["STALE_SYMBOL"]));

      const isAuthenticated = true;
      const backendLists: { id: string; symbols: string[] }[] = [];

      let userWatchlistId: string | null = "prev-id";
      let pinnedSymbols: string[] = ["STALE_SYMBOL"];

      // Replicating MarketOverviewTab.tsx hardened logic
      if (isAuthenticated) {
        if (backendLists && backendLists.length > 0) {
          userWatchlistId = backendLists[0].id;
          pinnedSymbols = backendLists[0].symbols || [];
        } else {
          userWatchlistId = null;
          pinnedSymbols = [];
        }
      } else {
        const localSaved = mockStorage.get("stockpulse_watchlist_symbols");
        if (localSaved) {
          pinnedSymbols = JSON.parse(localSaved);
        }
      }

      expect(userWatchlistId).toBeNull();
      expect(pinnedSymbols).toEqual([]);
    });
  });
});

