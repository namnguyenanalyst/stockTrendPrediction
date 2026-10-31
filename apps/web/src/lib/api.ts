/**
 * API Client kết nối Next.js Frontend với FastAPI Backend.
 * Base URL mặc định: http://localhost:8000 (có thể override qua process.env.NEXT_PUBLIC_API_URL).
 */

import {
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
  RecentSignalsResponse,
  RefreshTokenResponse,
  RegisterRequest,
  RetrainResponse,
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

export function setAuthToken(token: string | null): void {
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

export async function retrainProductionModel(
  horizon = 3,
  threshold = 0.02,
  valBufferDays = 40,
  scope: "CORE" | "VN30" = "VN30"
): Promise<RetrainResponse> {
  return fetchJson<RetrainResponse>("/api/predict/retrain", {
    method: "POST",
    body: JSON.stringify({
      horizon,
      threshold,
      val_buffer_days: valBufferDays,
      scope,
    }),
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
  const res = await fetchJson<LoginResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify(data),
  });
  if (res.access_token) {
    setAuthToken(res.access_token);
  }
  return res;
}

export async function registerUser(
  email: string,
  password: string,
  fullName?: string | null,
  riskProfile?: string
): Promise<User> {
  const data: RegisterRequest = {
    email,
    password,
    full_name: fullName,
    risk_profile: riskProfile,
  };
  return fetchJson<User>("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function refreshToken(token?: string): Promise<RefreshTokenResponse> {
  const body = token ? JSON.stringify({ refresh_token: token }) : JSON.stringify({});
  const res = await fetchJson<RefreshTokenResponse>("/api/v1/auth/refresh", {
    method: "POST",
    body,
  });
  if (res.access_token) {
    setAuthToken(res.access_token);
  }
  return res;
}

export async function getCurrentUser(): Promise<User> {
  return fetchJson<User>("/api/v1/auth/me");
}

export async function logoutUser(): Promise<void> {
  setAuthToken(null);
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
  return fetchJson<UserStrategyPreset[]>("/api/v1/user/presets");
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


