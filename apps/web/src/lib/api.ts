/**
 * API Client kết nối Next.js Frontend với FastAPI Backend.
 * Base URL mặc định: http://localhost:8000 (có thể override qua process.env.NEXT_PUBLIC_API_URL).
 */

import {
  AdvancedBacktestRequest,
  BacktestRequest,
  BacktestResponse,
  BacktestSummaryResponse,
  BatchPredictionResponse,
  MarketBoardResponse,
  MarketSyncStatusResponse,
  PortfolioBacktestResponse,
  PredictionResponse,
  RecentSignalsResponse,
  RetrainResponse,
  SectorItem,
  StockHistoryResponse,
  StockIndicatorsResponse,
  StockSummaryResponse,
  StockSymbolInfo,
  StrategyPresetsResponse,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options?.headers || {}),
      },
    });

    if (!res.ok) {
      const errorText = await res.text();
      throw new Error(`API error (${res.status}): ${errorText}`);
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
  valBufferDays = 40
): Promise<RetrainResponse> {
  return fetchJson<RetrainResponse>("/api/predict/retrain", {
    method: "POST",
    body: JSON.stringify({
      horizon,
      threshold,
      val_buffer_days: valBufferDays,
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

