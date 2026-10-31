import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  getCurrentUser,
  getAuthToken,
  loginUser,
  logoutUser,
  refreshToken,
  registerUser,
  setAuthToken,
} from "./api";
import {
  getTokenFromCookie,
  removeTokenCookie,
  setTokenCookie,
} from "../context/AuthContext";
import { middleware } from "../middleware";
import { NextRequest } from "next/server";

describe("Frontend Auth Suite (src/lib/auth.test.ts)", () => {
  beforeEach(() => {
    setAuthToken(null);
    vi.stubGlobal("fetch", vi.fn());
    // Giả lập document.cookie trong môi trường Node/JSDOM
    let cookieStore = "";
    if (typeof globalThis.document === "undefined") {
      (globalThis as unknown as Record<string, unknown>).document = {};
    }
    Object.defineProperty(globalThis.document, "cookie", {
      get: () => cookieStore,
      set: (val: string) => {
        if (val.includes("max-age=0")) {
          cookieStore = "";
        } else {
          cookieStore = val.split(";")[0];
        }
      },
      configurable: true,
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
    setAuthToken(null);
    delete (globalThis as unknown as Record<string, unknown>).document;
  });

  describe("API Client Auth Methods", () => {
    it("loginUser should POST /api/v1/auth/login, set inMemoryToken and return TokenResponse", async () => {
      const mockResponse = {
        access_token: "jwt-test-access-token",
        token_type: "bearer",
        user: {
          id: "u-123",
          email: "trader@quantinvest.vn",
          role: "trader",
          risk_profile: "balanced",
          is_active: true,
        },
      };

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      const res = await loginUser("trader@quantinvest.vn", "SecretPass123");

      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/v1/auth/login",
        expect.objectContaining({
          method: "POST",
          credentials: "include",
          body: JSON.stringify({
            email: "trader@quantinvest.vn",
            password: "SecretPass123",
          }),
        })
      );

      expect(res.access_token).toBe("jwt-test-access-token");
      expect(getAuthToken()).toBe("jwt-test-access-token");
      expect(res.user?.email).toBe("trader@quantinvest.vn");
    });

    it("loginUser should reject and throw error on invalid credentials (401)", async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: false,
        status: 401,
        text: async () => "Incorrect email or password",
      } as Response);

      await expect(
        loginUser("wrong@quantinvest.vn", "badpass")
      ).rejects.toThrow("API error (401): Incorrect email or password");
    });

    it("registerUser should POST /api/v1/auth/register and return User profile", async () => {
      const mockUser = {
        id: "u-456",
        email: "newtrader@quantinvest.vn",
        full_name: "Nguyen Van A",
        role: "trader",
        risk_profile: "aggressive",
        is_active: true,
        created_at: "2026-10-30T10:00:00Z",
      };

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUser,
      } as Response);

      const res = await registerUser(
        "newtrader@quantinvest.vn",
        "ValidPass123",
        "Nguyen Van A",
        "aggressive"
      );

      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/v1/auth/register",
        expect.objectContaining({
          method: "POST",
          credentials: "include",
          body: JSON.stringify({
            email: "newtrader@quantinvest.vn",
            password: "ValidPass123",
            full_name: "Nguyen Van A",
            risk_profile: "aggressive",
          }),
        })
      );

      expect(res.email).toBe("newtrader@quantinvest.vn");
      expect(res.risk_profile).toBe("aggressive");
    });

    it("refreshToken should call /api/v1/auth/refresh and update inMemoryToken", async () => {
      const mockRefresh = {
        access_token: "refreshed-access-token",
        token_type: "bearer",
      };

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockRefresh,
      } as Response);

      const res = await refreshToken();

      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/v1/auth/refresh",
        expect.objectContaining({
          method: "POST",
          credentials: "include",
        })
      );

      expect(res.access_token).toBe("refreshed-access-token");
      expect(getAuthToken()).toBe("refreshed-access-token");
    });

    it("getCurrentUser should attach Authorization header when token is set", async () => {
      setAuthToken("bearer-token-xyz");

      const mockUser = {
        id: "u-789",
        email: "active@quant.vn",
        role: "admin",
        risk_profile: "conservative",
        is_active: true,
      };

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUser,
      } as Response);

      const res = await getCurrentUser();

      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/v1/auth/me",
        expect.objectContaining({
          credentials: "include",
          headers: expect.objectContaining({
            Authorization: "Bearer bearer-token-xyz",
          }),
        })
      );
      expect(res.role).toBe("admin");
    });

    it("logoutUser should clear inMemoryToken", async () => {
      setAuthToken("some-token");
      expect(getAuthToken()).toBe("some-token");

      await logoutUser();
      expect(getAuthToken()).toBeNull();
    });
  });

  describe("Cookie Helpers (AuthContext)", () => {
    it("setTokenCookie, getTokenFromCookie, and removeTokenCookie should manage browser cookie", () => {
      removeTokenCookie();
      expect(getTokenFromCookie()).toBeNull();

      setTokenCookie("test-token-123");
      expect(getTokenFromCookie()).toBe("test-token-123");

      removeTokenCookie();
      expect(getTokenFromCookie()).toBeNull();
    });
  });

  describe("Edge Middleware Route Protection", () => {
    it("should redirect root / to /dashboard", () => {
      const req = new NextRequest("http://localhost:3000/");
      const res = middleware(req);

      expect(res.status).toBe(307);
      expect(res.headers.get("location")).toBe("http://localhost:3000/dashboard");
    });

    it("should redirect unauthenticated user from /dashboard to /login?redirect=/dashboard", () => {
      const req = new NextRequest("http://localhost:3000/dashboard");
      const res = middleware(req);

      expect(res.status).toBe(307);
      expect(res.headers.get("location")).toBe(
        "http://localhost:3000/login?redirect=%2Fdashboard"
      );
    });

    it("should redirect unauthenticated user from /backtest to /login?redirect=/backtest", () => {
      const req = new NextRequest("http://localhost:3000/backtest");
      const res = middleware(req);

      expect(res.status).toBe(307);
      expect(res.headers.get("location")).toBe(
        "http://localhost:3000/login?redirect=%2Fbacktest"
      );
    });

    it("should allow authenticated user to access /dashboard", () => {
      const req = new NextRequest("http://localhost:3000/dashboard", {
        headers: {
          cookie: "access_token=valid-jwt-token",
        },
      });
      const res = middleware(req);

      // Cho phép tiếp tục luồng request (x-middleware-next: 1)
      expect(res.headers.get("location")).toBeNull();
      expect(res.status).toBe(200);
    });

    it("should redirect authenticated user from /login to /dashboard", () => {
      const req = new NextRequest("http://localhost:3000/login", {
        headers: {
          cookie: "auth_token=valid-token",
        },
      });
      const res = middleware(req);

      expect(res.status).toBe(307);
      expect(res.headers.get("location")).toBe("http://localhost:3000/dashboard");
    });

    it("should redirect authenticated user from /register to /dashboard", () => {
      const req = new NextRequest("http://localhost:3000/register", {
        headers: {
          cookie: "access_token=valid-token",
        },
      });
      const res = middleware(req);

      expect(res.status).toBe(307);
      expect(res.headers.get("location")).toBe("http://localhost:3000/dashboard");
    });
  });
});
