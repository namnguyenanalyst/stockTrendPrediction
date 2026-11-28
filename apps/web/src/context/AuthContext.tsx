"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import { useRouter } from "next/navigation";
import {
  getCurrentUser,
  loginUser,
  logoutUser,
  refreshToken,
  registerUser,
  setAuthToken,
  setOnSessionExpired,
  setOnTokenRefreshed,
} from "@/lib/api";
import { User } from "@/lib/types";

export type RegistrationResult = { status: "authenticated"; user: User } | { status: "created" };

interface AuthContextType {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<User>;
  register: (
    email: string,
    password: string,
    fullName?: string | null,
  ) => Promise<RegistrationResult>;
  logout: () => Promise<void>;
  clearError: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_STORAGE_KEY = "stockpulse_access_token";

function isProtectedPath(pathname: string): boolean {
  return (
    pathname === "/dashboard" ||
    pathname === "/backtest" ||
    pathname === "/admin" ||
    pathname.startsWith("/dashboard/") ||
    pathname.startsWith("/backtest/") ||
    pathname.startsWith("/admin/")
  );
}

function getTokenMaxAgeSeconds(token: string): number {
  const defaultSeconds = 60 * 30;
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return defaultSeconds;
    const base64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const payload = JSON.parse(atob(base64)) as { exp?: unknown };
    if (typeof payload.exp !== "number") return defaultSeconds;
    return Math.max(0, Math.min(defaultSeconds, Math.floor(payload.exp - Date.now() / 1000)));
  } catch {
    return defaultSeconds;
  }
}

export function setTokenCookie(token: string): void {
  if (typeof document !== "undefined") {
    const maxAge = getTokenMaxAgeSeconds(token);
    document.cookie = `access_token=${encodeURIComponent(
      token
    )}; path=/; max-age=${maxAge}; SameSite=Lax`;
    document.cookie = `auth_token=${encodeURIComponent(
      token
    )}; path=/; max-age=${maxAge}; SameSite=Lax`;
  }
}

export function removeTokenCookie(): void {
  if (typeof document !== "undefined") {
    document.cookie = "access_token=; path=/; max-age=0; SameSite=Lax";
    document.cookie = "auth_token=; path=/; max-age=0; SameSite=Lax";
  }
}

export function getTokenFromCookie(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(
    /(?:^|;\s*)(?:access_token|auth_token)=([^;]+)/
  );
  if (!match) return null;
  try {
    return decodeURIComponent(match[1]);
  } catch (err) {
    if (err instanceof URIError) {
      return match[1];
    }
    return match[1];
  }
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const userRef = useRef<User | null>(null);
  userRef.current = user;
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => setError(null), []);

  const refreshUser = useCallback(async () => {
    try {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
    } catch (err) {
      console.warn("Không thể đồng bộ hồ sơ người dùng:", err);
    }
  }, []);

  // Đăng ký callback đồng bộ token khi auto-refresh / hết phiên
  useEffect(() => {
    if (typeof setOnTokenRefreshed === "function") {
      setOnTokenRefreshed((newToken: string) => {
        setAccessToken(newToken);
        setTokenCookie(newToken);
        if (typeof window !== "undefined") {
          window.localStorage.setItem(TOKEN_STORAGE_KEY, newToken);
        }
      });
    }
    if (typeof setOnSessionExpired === "function") {
      setOnSessionExpired(() => {
        setUser(null);
        setAccessToken(null);
        removeTokenCookie();
        if (typeof window !== "undefined") {
          window.localStorage.removeItem(TOKEN_STORAGE_KEY);
          if (isProtectedPath(window.location.pathname)) {
            router.push("/login");
          }
        }
      });
    }
    return () => {
      if (typeof setOnTokenRefreshed === "function") setOnTokenRefreshed(null);
      if (typeof setOnSessionExpired === "function") setOnSessionExpired(null);
    };
  }, [router]);

  // Đồng bộ trạng thái xác minh email giữa các tab trình duyệt
  useEffect(() => {
    if (typeof window === "undefined") return;

    const syncIfUnverified = () => {
      if (userRef.current && !userRef.current.email_verified_at) {
        void refreshUser();
      }
    };

    const handleStorage = (event: StorageEvent) => {
      if (event.key === "stockpulse_email_verified_at" && event.newValue) {
        syncIfUnverified();
      }
    };

    const handleVisibility = () => {
      if (typeof document !== "undefined" && document.visibilityState === "visible") {
        syncIfUnverified();
      }
    };

    window.addEventListener("storage", handleStorage);
    document.addEventListener("visibilitychange", handleVisibility);

    let channel: BroadcastChannel | null = null;
    try {
      if (typeof BroadcastChannel !== "undefined") {
        channel = new BroadcastChannel("stockpulse_auth_sync");
        channel.onmessage = (event: MessageEvent<{ type?: string }>) => {
          if (event.data?.type === "email_verified") {
            syncIfUnverified();
          }
        };
      }
    } catch {
      channel = null;
    }

    return () => {
      window.removeEventListener("storage", handleStorage);
      document.removeEventListener("visibilitychange", handleVisibility);
      channel?.close();
    };
  }, [refreshUser]);

  // Khởi tạo phiên làm việc khi mount
  useEffect(() => {
    let ignore = false;

    async function initAuth() {
      setIsLoading(true);
      const savedToken =
        getTokenFromCookie() ||
        (typeof window !== "undefined"
          ? window.localStorage.getItem(TOKEN_STORAGE_KEY)
          : null);

      if (savedToken) {
        setAuthToken(savedToken);
        setAccessToken(savedToken);
        try {
          const currentUser = await getCurrentUser();
          if (!ignore) {
            setUser(currentUser);
            setIsLoading(false);
            return;
          }
        } catch {
          // Token có thể đã hết hạn, thử refresh âm thầm
        }
      }

      // Thử refresh token qua HTTP-only cookie
      try {
        const refreshRes = await refreshToken();
        if (!ignore && refreshRes.access_token) {
          setAuthToken(refreshRes.access_token);
          setAccessToken(refreshRes.access_token);
          setTokenCookie(refreshRes.access_token);
          if (typeof window !== "undefined") {
            window.localStorage.setItem(
              TOKEN_STORAGE_KEY,
              refreshRes.access_token
            );
          }
          const currentUser = await getCurrentUser();
          if (!ignore) {
            setUser(currentUser);
          }
        }
      } catch {
        // Chưa đăng nhập hoặc refresh token không hợp lệ
        if (!ignore) {
          setUser(null);
          setAccessToken(null);
          setAuthToken(null);
          removeTokenCookie();
          if (typeof window !== "undefined") {
            window.localStorage.removeItem(TOKEN_STORAGE_KEY);
            if (isProtectedPath(window.location.pathname)) {
              router.push("/login");
            }
          }
        }
      } finally {
        if (!ignore) {
          setIsLoading(false);
        }
      }
    }

    initAuth();

    return () => {
      ignore = true;
    };
  }, [router]);

  const login = useCallback(
    async (email: string, password: string): Promise<User> => {
      setIsLoading(true);
      setError(null);
      try {
        const res = await loginUser(email, password);
        const token = res.access_token;
        setAccessToken(token);
        setAuthToken(token);
        setTokenCookie(token);
        if (typeof window !== "undefined") {
          window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
          window.localStorage.removeItem("stockpulse_saved_strategies_v1");
        }

        let userData = res.user;
        if (!userData) {
          userData = await getCurrentUser();
        }
        setUser(userData);
        return userData;
      } catch (err: unknown) {
        const errMessage = err instanceof Error ? err.message : String(err);
        const message = errMessage.includes("Inactive user account")
          ? "Tài khoản của bạn đã bị khóa hoặc vô hiệu hóa. Vui lòng liên hệ quản trị viên."
          : errMessage.includes("429") || errMessage.includes("RATE_LIMITED")
            ? "Bạn đã thử đăng nhập quá nhiều lần. Vui lòng thử lại sau ít phút."
            : errMessage.includes("401") || errMessage.includes("Incorrect email")
              ? "Email hoặc mật khẩu không chính xác."
              : "Chưa thể đăng nhập. Vui lòng thử lại sau.";
        setError(message);
        throw new Error(message);
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const register = useCallback(
    async (email: string, password: string, fullName?: string | null): Promise<RegistrationResult> => {
      setIsLoading(true);
      setError(null);
      try {
        await registerUser(email, password, fullName);
      } catch (err: unknown) {
        const raw = err instanceof Error ? err.message : "";
        const message =
          raw.includes("already registered") || raw.includes("409")
            ? "Email này đã được sử dụng. Vui lòng đăng nhập hoặc khôi phục mật khẩu."
            : raw.includes("429") || raw.includes("RATE_LIMITED")
              ? "Bạn đã gửi quá nhiều yêu cầu đăng ký. Vui lòng thử lại sau ít phút."
              : raw.includes("422")
                ? "Thông tin đăng ký chưa hợp lệ (email chỉ hỗ trợ ký tự ASCII chuẩn và mật khẩu tối thiểu 8 ký tự)."
                : "Chưa thể tạo tài khoản. Vui lòng kiểm tra kết nối và thông tin đăng ký.";
        setError(message);
        setIsLoading(false);
        throw new Error(message);
      }
      try {
        return { status: "authenticated", user: await login(email, password) };
      } catch {
        // Account creation succeeded; discard any partially initialized session.
        try { await logoutUser(); } catch { /* The API may be offline. */ }
        setUser(null);
        setAccessToken(null);
        setAuthToken(null);
        removeTokenCookie();
        if (typeof window !== "undefined") window.localStorage.removeItem(TOKEN_STORAGE_KEY);
        setError(null);
        return { status: "created" };
      } finally {
        setIsLoading(false);
      }
    }, [login]
  );

  const logout = useCallback(async (): Promise<void> => {
    setIsLoading(true);
    try {
      await logoutUser();
    } catch {
      // Ignored
    } finally {
      setUser(null);
      setAccessToken(null);
      setAuthToken(null);
      removeTokenCookie();
      if (typeof window !== "undefined") {
        window.localStorage.removeItem(TOKEN_STORAGE_KEY);
        window.localStorage.removeItem("stockpulse_watchlist_symbols");
        window.localStorage.removeItem("stockpulse_saved_strategies_v1");
      }
      setIsLoading(false);
      router.push("/login");
    }
  }, [router]);

  return (
    <AuthContext.Provider
      value={{
        user,
        accessToken,
        isAuthenticated: !!user && !!accessToken,
        isLoading,
        error,
        login,
        register,
        logout,
        clearError,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
