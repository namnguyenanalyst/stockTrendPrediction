/**
 * API Client kết nối Next.js Frontend với FastAPI Backend.
 * Base URL mặc định: http://localhost:8000 (có thể override qua process.env.NEXT_PUBLIC_API_URL).
 */

import {
  BacktestRequest,
  BacktestResponse,
  BacktestSummaryResponse,
  BatchPredictionResponse,
  PredictionResponse,
  StockHistoryResponse,
  StockIndicatorsResponse,
  StockSummaryResponse,
  StockSymbolInfo,
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
    console.error(`Fetch failed for ${endpoint}:`, error);
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
      { symbol: "VHM", name: "CTCP Vinhomes", exchange: "HOSE", is_core: true },
      { symbol: "VNM", name: "CTCP Sữa Việt Nam", exchange: "HOSE", is_core: true },
      { symbol: "HPG", name: "CTCP Tập đoàn Hòa Phát", exchange: "HOSE", is_core: true },
      { symbol: "SSI", name: "CTCP Chứng khoán SSI", exchange: "HOSE", is_core: true },
    ];
  }
}

export async function getStockHistory(
  symbol: string,
  startDate = "2023-01-01"
): Promise<StockHistoryResponse> {
  return fetchJson<StockHistoryResponse>(
    `/api/stocks/history?symbol=${symbol}&start_date=${startDate}`
  );
}

export async function getStockIndicators(symbol: string): Promise<StockIndicatorsResponse> {
  return fetchJson<StockIndicatorsResponse>(`/api/stocks/indicators?symbol=${symbol}`);
}

export async function getStockSummary(symbol: string): Promise<StockSummaryResponse> {
  return fetchJson<StockSummaryResponse>(`/api/stocks/summary?symbol=${symbol}`);
}

// 3. Dự báo xu hướng AI
export async function getPredictionSignal(
  symbol: string,
  modelType: "lightgbm" | "lstm" = "lightgbm"
): Promise<PredictionResponse> {
  return fetchJson<PredictionResponse>("/api/predict/signal", {
    method: "POST",
    body: JSON.stringify({ symbol, model_type: modelType }),
  });
}

export async function getBatchPrediction(
  modelType: "lightgbm" | "lstm" = "lightgbm"
): Promise<BatchPredictionResponse> {
  return fetchJson<BatchPredictionResponse>("/api/predict/batch", {
    method: "POST",
    body: JSON.stringify({ model_type: modelType }),
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
