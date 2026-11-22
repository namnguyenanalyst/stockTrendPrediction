/**
 * API Client kết nối Next.js Frontend với FastAPI Backend.
 * Base URL mặc định: http://localhost:8000 (có thể override qua process.env.NEXT_PUBLIC_API_URL).
 */

import {
  AdminActivityResponse,
  AdminStatsResponse,
  AdminUpdateUserRequest,
  AdminUserItem,
  AdminUserListResponse,
  AdvancedBacktestRequest,
  BacktestHistoryCreateRequest,
  BacktestRequest,
  BacktestResponse,
  BacktestSummaryResponse,
  BatchPredictionResponse,
  LoginRequest,
  LoginResponse,
  MarketBoardResponse,
  MarketSyncStatusResponse,
  PortfolioBacktestResponse,
  PredictionResponse,
  PredictStatusResponse,
  RecentSignalsResponse,
  RefreshTokenResponse,
  RegisterRequest,
  SectorItem,
  StockHistoryResponse,
  StockIndicatorsResponse,
  StockSummaryResponse,
  StockSymbolInfo,
  StrategyPresetsResponse,
  User,
  UserBacktestHistory,
  UserStrategyPreset,
  UserWatchlist,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

let inMemoryToken: string | null = null;
let authGeneration = 0;
const pendingRefreshes = new Map<string, Promise<RefreshTokenResponse>>();
const pendingLogins = new Set<Promise<LoginResponse>>();

export function setAuthToken(token: string | null): void {
  authGeneration += 1;
  inMemoryToken = token;
}

export function getAuthToken(): string | null {
  return inMemoryToken;
}

async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options?.headers as Record<string, string>) || {}),
  };

  if (inMemoryToken && !headers["Authorization"]) {
    headers["Authorization"] = `Bearer ${inMemoryToken}`;
  }

  try {
    const res = await fetch(url, {
      credentials: "include",
      ...options,
      headers,
    });

    if (!res.ok) {
      const errorText = await res.text();
      throw new Error(`API error (${res.status}): ${errorText}`);
    }

    if (res.status === 204) {
      return undefined as T;
    }

    return (await res.json()) as T;
  } catch (error) {
    console.warn(`Fetch failed for ${endpoint}:`, error);
    throw error;
  }
}

// 1. Healthcheck
export async function checkBackendHealth(): Promise<{ status: string; version: string }> {
  return fetchJson<{ status: string; version: string }>("/health");
}

// 2. Dữ liệu cổ phiếu
export async function getStockSymbols(): Promise<StockSymbolInfo[]> {
  try {
    return await fetchJson<StockSymbolInfo[]>("/api/stocks/symbols");
  } catch {
    // Fallback nếu API đang khởi động
    return [
      { symbol: "VIC", name: "Tập đoàn Vingroup", exchange: "HOSE", is_core: true },
      { symbol: "HPG", name: "CTCP Tập đoàn Hòa Phát", exchange: "HOSE", is_core: true },
      { symbol: "FPT", name: "CTCP FPT", exchange: "HOSE", is_core: true },
      { symbol: "VNM", name: "CTCP Sữa Việt Nam", exchange: "HOSE", is_core: true },
      { symbol: "MWG", name: "CTCP Đầu tư Thế Giới Di Động", exchange: "HOSE", is_core: true },
    ];
  }
}

export async function getStockHistory(
  symbol: string,
  startDate?: string,
  limit = 1500
): Promise<StockHistoryResponse> {
  const params = new URLSearchParams();
  params.set("symbol", symbol);
  if (startDate) params.set("start_date", startDate);
  if (limit) params.set("limit", limit.toString());
  return fetchJson<StockHistoryResponse>(`/api/stocks/history?${params.toString()}`);
}

export async function getStockIndicators(
  symbol: string,
  limit = 1500
): Promise<StockIndicatorsResponse> {
  return fetchJson<StockIndicatorsResponse>(
    `/api/stocks/indicators?symbol=${encodeURIComponent(symbol)}&limit=${limit}`
  );
}

export async function getStockSummary(symbol: string): Promise<StockSummaryResponse> {
  return fetchJson<StockSummaryResponse>(
    `/api/stocks/summary?symbol=${encodeURIComponent(symbol)}`
  );
}

export async function getMarketBoard(): Promise<MarketBoardResponse> {
  return fetchJson<MarketBoardResponse>("/api/stocks/board");
}

export async function getMarketSyncStatus(): Promise<MarketSyncStatusResponse> {
  return fetchJson<MarketSyncStatusResponse>("/api/stocks/sync-status");
}

export async function triggerMarketSync(): Promise<{
  status: string;
  target_date?: string;
  session_type?: string;
  total_symbols?: number;
}> {
  return fetchJson<{
    status: string;
    target_date?: string;
    session_type?: string;
    total_symbols?: number;
  }>("/api/stocks/sync", {
    method: "POST",
  });
}

// 3. Dự báo xu hướng AI
export async function getPredictionSignal(
  symbol: string,
  modelType: "lightgbm" | "lstm" = "lightgbm"
): Promise<PredictionResponse> {
  return fetchJson<PredictionResponse>(
    `/api/predict/signal?symbol=${encodeURIComponent(symbol)}&model_type=${encodeURIComponent(modelType)}`
  );
}

export async function getBatchPrediction(
  modelType: "lightgbm" | "lstm" = "lightgbm"
): Promise<BatchPredictionResponse> {
  return fetchJson<BatchPredictionResponse>(
    `/api/predict/batch?model_type=${encodeURIComponent(modelType)}`
  );
}

export async function syncLivePrediction(
  symbol: string,
  modelType: "lightgbm" | "lstm" = "lightgbm"
): Promise<PredictionResponse> {
  return fetchJson<PredictionResponse>("/api/predict/live", {
    method: "POST",
    body: JSON.stringify({ symbol, model_type: modelType }),
  });
}

// 4. Giả lập Backtest
export async function runBacktestSimulation(
  request: BacktestRequest
): Promise<BacktestResponse> {
  return fetchJson<BacktestResponse>("/api/backtest/run", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function getBacktestSummary(
  modelType: "lightgbm" | "lstm" = "lightgbm"
): Promise<BacktestSummaryResponse> {
  return fetchJson<BacktestSummaryResponse>(
    `/api/backtest/summary?model_type=${modelType}`
  );
}

export async function getStrategyPresets(): Promise<StrategyPresetsResponse> {
  return fetchJson<StrategyPresetsResponse>("/api/backtest/presets");
}

export async function getRecentStrategySignals(): Promise<RecentSignalsResponse> {
  return fetchJson<RecentSignalsResponse>("/api/backtest/signals/recent");
}

export async function getStockSectors(): Promise<SectorItem[]> {
  try {
    return await fetchJson<SectorItem[]>("/api/stocks/sectors");
  } catch {
    return [
      { sector: "Ngân hàng", symbols: ["VCB", "BID", "CTG", "TCB", "MBB", "ACB", "VPB", "SHB", "STB", "TPB", "VIB"], count: 11 },
      { sector: "Bất động sản", symbols: ["VIC", "VHM", "VRE", "BCM"], count: 4 },
      { sector: "Thép & Vật liệu", symbols: ["HPG"], count: 1 },
      { sector: "Bán lẻ", symbols: ["MWG"], count: 1 },
      { sector: "Công nghệ thông tin", symbols: ["FPT"], count: 1 },
      { sector: "Hàng tiêu dùng", symbols: ["VNM", "MSN", "SAB"], count: 3 },
      { sector: "Dịch vụ tài chính", symbols: ["SSI"], count: 1 },
    ];
  }
}

export async function runAdvancedBacktest(
  request: AdvancedBacktestRequest
): Promise<PortfolioBacktestResponse> {
  return fetchJson<PortfolioBacktestResponse>("/api/backtest/run-advanced", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

// =============================================================================
// Auth API Endpoints (/api/v1/auth)
// =============================================================================

export async function loginUser(
  email: string,
  password: string
): Promise<LoginResponse> {
  const data: LoginRequest = { email, password };
  const operation = fetchJson<LoginResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify(data),
  });
  pendingLogins.add(operation);
  try {
    const res = await operation;
    if (res.access_token) setAuthToken(res.access_token);
    return res;
  } finally {
    pendingLogins.delete(operation);
  }
}

export async function registerUser(
  email: string,
  password: string,
  fullName?: string | null,
): Promise<User> {
  const data: RegisterRequest = {
    email,
    password,
    full_name: fullName,
  };
  return fetchJson<User>("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function refreshToken(token?: string): Promise<RefreshTokenResponse> {
  const key = token || "cookie";
  const pending = pendingRefreshes.get(key);
  if (pending) return pending;
  const generation = authGeneration;
  const body = token ? JSON.stringify({ refresh_token: token }) : JSON.stringify({});
  const operation = fetchJson<RefreshTokenResponse>("/api/v1/auth/refresh", {
    method: "POST",
    body,
  }).then((res) => {
    if (res.access_token && generation === authGeneration) setAuthToken(res.access_token);
    return res;
  }).finally(() => { pendingRefreshes.delete(key); });
  pendingRefreshes.set(key, operation);
  return operation;
}

export async function getCurrentUser(): Promise<User> {
  return fetchJson<User>("/api/v1/auth/me");
}

export async function logoutUser(): Promise<void> {
  setAuthToken(null);
  try {
    await Promise.allSettled([...pendingRefreshes.values(), ...pendingLogins]);
    await fetchJson<void>("/api/v1/auth/logout", { method: "POST" });
  } finally {
    setAuthToken(null);
  }
}

// =============================================================================
// Personalization API Endpoints (/api/v1/user)
// =============================================================================

export async function getUserWatchlists(): Promise<UserWatchlist[]> {
  return fetchJson<UserWatchlist[]>("/api/v1/user/watchlists");
}

export async function createUserWatchlist(
  name: string,
  symbols: string[]
): Promise<UserWatchlist> {
  return fetchJson<UserWatchlist>("/api/v1/user/watchlists", {
    method: "POST",
    body: JSON.stringify({ name, symbols }),
  });
}

export async function deleteUserWatchlist(id: string): Promise<void> {
  return fetchJson<void>(`/api/v1/user/watchlists/${id}`, {
    method: "DELETE",
  });
}

export async function getUserPresets(): Promise<UserStrategyPreset[]> {
  const result = await fetchJson<UserStrategyPreset[]>("/api/v1/user/presets");
  let pageSize = result.length;
  while (pageSize === 100) {
    const page = await fetchJson<UserStrategyPreset[]>(`/api/v1/user/presets?limit=100&offset=${result.length}`);
    result.push(...page);
    pageSize = page.length;
  }
  return result;
}

export async function createUserPreset(
  name: string,
  description: string | null | undefined,
  parameters: Record<string, unknown>
): Promise<UserStrategyPreset> {
  return fetchJson<UserStrategyPreset>("/api/v1/user/presets", {
    method: "POST",
    body: JSON.stringify({ name, description, parameters }),
  });
}

export async function deleteUserPreset(id: string): Promise<void> {
  return fetchJson<void>(`/api/v1/user/presets/${id}`, {
    method: "DELETE",
  });
}

export async function getUserBacktests(): Promise<UserBacktestHistory[]> {
  return fetchJson<UserBacktestHistory[]>("/api/v1/user/backtests");
}

export async function saveUserBacktest(
  data: BacktestHistoryCreateRequest
): Promise<UserBacktestHistory> {
  return fetchJson<UserBacktestHistory>("/api/v1/user/backtests", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function deleteUserBacktest(id: string): Promise<void> {
  return fetchJson<void>(`/api/v1/user/backtests/${id}`, {
    method: "DELETE",
  });
}

export async function getAdminStats(): Promise<AdminStatsResponse> {
  return fetchJson<AdminStatsResponse>("/api/v1/admin/stats");
}

export async function getAdminUsers(params?: {
  search?: string;
  role?: string;
  is_active?: boolean;
  page?: number;
  page_size?: number;
}): Promise<AdminUserListResponse> {
  const query = new URLSearchParams();
  if (params?.search) query.set("search", params.search);
  if (params?.role) query.set("role", params.role);
  if (params?.is_active !== undefined) query.set("is_active", String(params.is_active));
  if (params?.page) query.set("page", String(params.page));
  if (params?.page_size) query.set("page_size", String(params.page_size));

  const qs = query.toString();
  return fetchJson<AdminUserListResponse>(`/api/v1/admin/users${qs ? `?${qs}` : ""}`);
}

export async function updateAdminUser(
  userId: string,
  payload: AdminUpdateUserRequest
): Promise<AdminUserItem> {
  return fetchJson<AdminUserItem>(`/api/v1/admin/users/${userId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function getAdminActivityLogs(limit: number = 25): Promise<AdminActivityResponse> {
  return fetchJson<AdminActivityResponse>(`/api/v1/admin/activity-logs?limit=${limit}`);
}

export async function getPredictStatus(): Promise<PredictStatusResponse> {
  return fetchJson<PredictStatusResponse>("/api/v1/predict/status");
}



export async function updateUserPreset(id: string, name: string, description: string | null | undefined, parameters: Record<string, unknown>): Promise<UserStrategyPreset> {
  return fetchJson<UserStrategyPreset>(`/api/v1/user/presets/${encodeURIComponent(id)}`, { method: "PUT", body: JSON.stringify({ name, description, parameters }) });
}


export class AccountApiError extends Error {
  constructor(public code: string, message: string, public retryAfter = 0) {
    super(message);
  }
}

async function accountRequest(path: string, body: object = {}): Promise<{ message: string }> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/v1/auth/${path}`, {
      method: "POST", credentials: "include",
      headers: { "Content-Type": "application/json", ...(inMemoryToken ? { Authorization: `Bearer ${inMemoryToken}` } : {}) },
      body: JSON.stringify(body),
    });
  } catch {
    throw new AccountApiError("NETWORK_ERROR", "Không thể kết nối. Vui lòng thử lại.");
  }
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const code = payload?.detail?.code || "REQUEST_FAILED";
    const retryAfter = Number(response.headers.get("Retry-After")) || 60;
    const message = response.status === 429
      ? `Bạn đã gửi quá nhiều yêu cầu. Vui lòng thử lại sau ${retryAfter} giây.`
      : code === "INVALID_OR_EXPIRED_TOKEN"
        ? "Liên kết không hợp lệ, đã hết hạn hoặc đã được sử dụng. Vui lòng yêu cầu liên kết mới."
        : response.status === 401 ? "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại."
        : response.status === 422 ? "Thông tin chưa hợp lệ. Vui lòng kiểm tra lại."
        : "Chưa thể xử lý yêu cầu. Vui lòng thử lại sau.";
    throw new AccountApiError(code, message, response.status === 429 ? retryAfter : 0);
  }
  return response.json();
}

export const requestPasswordReset = (email: string) => accountRequest("forgot-password", { email });
export const resetAccountPassword = (token: string, new_password: string) => accountRequest("reset-password", { token, new_password });
export const verifyAccountEmail = (token: string) => accountRequest("verify-email", { token });
export const resendVerification = () => accountRequest("resend-verification");

export function getChartIndicators(symbol: string) {
 return fetchJson<import('./chartIndicators').ChartIndicatorsResponse>(`/api/stocks/chart-indicators?symbol=${encodeURIComponent(symbol)}&limit=1500`);
}
