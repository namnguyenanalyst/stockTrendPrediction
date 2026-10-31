"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
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
} from "@/lib/api";
import { RiskProfile, User } from "@/lib/types";

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
    riskProfile?: RiskProfile | string
  ) => Promise<User>;
  logout: () => Promise<void>;
  clearError: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_STORAGE_KEY = "stockpulse_access_token";

export function setTokenCookie(token: string): void {
  if (typeof document !== "undefined") {
    const maxAge = 60 * 60 * 24 * 7; // 7 days
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
            const currentPath = window.location.pathname;
            const isProtectedRoute =
              currentPath === "/dashboard" ||
              currentPath === "/backtest" ||
              currentPath.startsWith("/dashboard/") ||
              currentPath.startsWith("/backtest/");
            if (isProtectedRoute) {
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
        const message =
          errMessage.includes("401") ||
          errMessage.includes("Incorrect email")
            ? "Email hoặc mật khẩu không chính xác."
            : errMessage || "Đăng nhập thất bại. Vui lòng thử lại.";
        setError(message);
        throw new Error(message);
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const register = useCallback(
    async (
      email: string,
      password: string,
      fullName?: string | null,
      riskProfile?: RiskProfile | string
    ): Promise<User> => {
      setIsLoading(true);
      setError(null);
      try {
        await registerUser(email, password, fullName, riskProfile);
        // Tự động đăng nhập sau khi đăng ký thành công
        const loggedInUser = await login(email, password);
        return loggedInUser;
      } catch (err: unknown) {
        const errMessage = err instanceof Error ? err.message : String(err);
        const message =
          errMessage.includes("400") ||
          errMessage.includes("already registered")
            ? "Email này đã được sử dụng. Vui lòng chọn email khác."
            : errMessage || "Đăng ký không thành công. Vui lòng kiểm tra lại.";
        setError(message);
        throw new Error(message);
      } finally {
        setIsLoading(false);
      }
    },
    [login]
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
