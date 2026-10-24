import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  checkBackendHealth,
  getBacktestSummary,
  getBatchPrediction,
  getMarketBoard,
  getMarketSyncStatus,
  getPredictionSignal,
  getRecentStrategySignals,
  getStockHistory,
  getStockIndicators,
  getStockSectors,
  getStockSummary,
  getStockSymbols,
  getStrategyPresets,
  retrainProductionModel,
  runAdvancedBacktest,
  runBacktestSimulation,
  syncLivePrediction,
  triggerMarketSync,
} from "./api";
import { AdvancedBacktestRequest, BacktestRequest } from "./types";

describe("Web API Client (src/lib/api.ts)", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("checkBackendHealth", () => {
    it("should fetch /health and return backend status", async () => {
      const mockData = { status: "healthy", version: "1.0.0" };
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      } as Response);

      const result = await checkBackendHealth();
      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/health",
        expect.objectContaining({
          headers: expect.objectContaining({ "Content-Type": "application/json" }),
        })
      );
      expect(result).toEqual(mockData);
    });

    it("should throw an error when API response is not ok", async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: false,
        status: 500,
        text: async () => "Internal Server Error",
      } as Response);

      await expect(checkBackendHealth()).rejects.toThrow("API error (500): Internal Server Error");
    });
  });

  describe("getStockSymbols", () => {
    it("should return symbols list when fetch succeeds", async () => {
      const mockSymbols = [
        { symbol: "VIC", name: "Vingroup", exchange: "HOSE", is_core: true },
      ];
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockSymbols,
      } as Response);

      const result = await getStockSymbols();
      expect(result).toEqual(mockSymbols);
    });

    it("should fallback to default 5 core symbols when fetch fails", async () => {
      vi.mocked(fetch).mockRejectedValueOnce(new Error("Network Error"));

      const result = await getStockSymbols();
      expect(result).toHaveLength(5);
      expect(result.map((s) => s.symbol)).toEqual(["VIC", "HPG", "FPT", "VNM", "MWG"]);
    });
  });

  describe("getStockHistory", () => {
    it("should construct query parameters correctly", async () => {
      const mockHistory = { symbol: "VIC", total_bars: 1, bars: [] };
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockHistory,
      } as Response);

      const result = await getStockHistory("VIC", "2024-01-01", 100);
      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/stocks/history?symbol=VIC&start_date=2024-01-01&limit=100",
        expect.anything()
      );
      expect(result).toEqual(mockHistory);
    });
  });

  describe("getStockIndicators", () => {
    it("should call /api/stocks/indicators with encoded symbol", async () => {
      const mockIndicators = { symbol: "HPG", indicators: [] };
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockIndicators,
      } as Response);

      const result = await getStockIndicators("HPG", 50);
      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/stocks/indicators?symbol=HPG&limit=50",
        expect.anything()
      );
      expect(result).toEqual(mockIndicators);
    });
  });

  describe("getStockSummary", () => {
    it("should call /api/stocks/summary with symbol", async () => {
      const mockSummary = { symbol: "FPT", latest_close: 130.5 };
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockSummary,
      } as Response);

      const result = await getStockSummary("FPT");
      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/stocks/summary?symbol=FPT",
        expect.anything()
      );
      expect(result).toEqual(mockSummary);
    });
  });

  describe("getMarketBoard and MarketSyncStatus", () => {
    it("should call getMarketBoard", async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ indices: [], stocks: [] }),
      } as Response);

      const result = await getMarketBoard();
      expect(fetch).toHaveBeenCalledWith("http://localhost:8000/api/stocks/board", expect.anything());
      expect(result).toBeDefined();
    });

    it("should call getMarketSyncStatus", async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ is_market_closed: true, status_label: "Đã đóng cửa" }),
      } as Response);

      const result = await getMarketSyncStatus();
      expect(fetch).toHaveBeenCalledWith("http://localhost:8000/api/stocks/sync-status", expect.anything());
      expect(result.status_label).toBe("Đã đóng cửa");
    });

    it("should trigger market sync via POST", async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: "completed" }),
      } as Response);

      const result = await triggerMarketSync();
      expect(fetch).toHaveBeenCalledWith("http://localhost:8000/api/stocks/sync", expect.objectContaining({ method: "POST" }));
      expect(result.status).toBe("completed");
    });
  });

  describe("AI Prediction Endpoints", () => {
    it("should fetch prediction signal with modelType", async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ symbol: "VIC", class_name: "TĂNG" }),
      } as Response);

      const res = await getPredictionSignal("VIC", "lstm");
      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/predict/signal?symbol=VIC&model_type=lstm",
        expect.anything()
      );
      expect(res.class_name).toBe("TĂNG");
    });

    it("should call batch prediction", async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ total_symbols: 5, predictions: [] }),
      } as Response);

      const res = await getBatchPrediction("lightgbm");
      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/predict/batch?model_type=lightgbm",
        expect.anything()
      );
      expect(res.total_symbols).toBe(5);
    });

    it("should trigger live prediction sync via POST", async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ symbol: "VIC", horizon: "T+3" }),
      } as Response);

      const res = await syncLivePrediction("VIC", "lightgbm");
      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/predict/live",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ symbol: "VIC", model_type: "lightgbm" }),
        })
      );
      expect(res.horizon).toBe("T+3");
    });

    it("should call retrainProductionModel with custom hyperparameters", async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: "success", horizon: "T+3" }),
      } as Response);

      const res = await retrainProductionModel(3, 0.02, 40, "VN30");
      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/predict/retrain",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({
            horizon: 3,
            threshold: 0.02,
            val_buffer_days: 40,
            scope: "VN30",
          }),
        })
      );
      expect(res.status).toBe("success");
    });
  });

  describe("Backtest Endpoints", () => {
    it("should execute runBacktestSimulation via POST", async () => {
      const mockReq: BacktestRequest = {
        symbol: "VIC",
        model_type: "lightgbm",
        initial_capital: 100_000_000,
        slippage_rate: 0.0005,
      };
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ symbol: "VIC", metrics: { total_return_pct: 12.5 } }),
      } as Response);

      const res = await runBacktestSimulation(mockReq);
      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/backtest/run",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify(mockReq),
        })
      );
      expect(res.symbol).toBe("VIC");
    });

    it("should fetch getBacktestSummary", async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ model_type: "LIGHTGBM", summary: [] }),
      } as Response);

      const res = await getBacktestSummary("lightgbm");
      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/backtest/summary?model_type=lightgbm",
        expect.anything()
      );
      expect(res.model_type).toBe("LIGHTGBM");
    });

    it("should fetch presets and recent signals", async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ presets: [] }),
      } as Response);

      const presets = await getStrategyPresets();
      expect(fetch).toHaveBeenCalledWith("http://localhost:8000/api/backtest/presets", expect.anything());
      expect(presets).toHaveProperty("presets");

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ signals: [] }),
      } as Response);

      const signals = await getRecentStrategySignals();
      expect(fetch).toHaveBeenCalledWith("http://localhost:8000/api/backtest/signals/recent", expect.anything());
      expect(signals).toHaveProperty("signals");
    });

    it("should fetch getStockSectors with fallback on failure", async () => {
      // Success case
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => [{ sector: "Ngân hàng", symbols: ["VCB"], count: 1 }],
      } as Response);

      const secRes = await getStockSectors();
      expect(secRes).toHaveLength(1);

      // Fallback case
      vi.mocked(fetch).mockRejectedValueOnce(new Error("Network Down"));
      const fallbackRes = await getStockSectors();
      expect(fallbackRes.length).toBeGreaterThanOrEqual(5);
      expect(fallbackRes[0].sector).toBe("Ngân hàng");
    });

    it("should execute runAdvancedBacktest via POST", async () => {
      const mockReq: AdvancedBacktestRequest = {
        scope_type: "portfolio",
        portfolio_symbols: ["VIC", "HPG"],
        start_date: "2024-01-01",
        end_date: "2024-06-01",
        initial_capital: 100_000_000,
        model_type: "lightgbm",
        slippage_rate: 0.0005,
        use_advanced_settings: false,
        buy_conditions: {},
        sell_conditions: {},
      };

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          scope_type: "portfolio",
          aggregate_metrics: { total_return_pct: 15.0 },
        }),
      } as Response);

      const res = await runAdvancedBacktest(mockReq);
      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/backtest/run-advanced",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify(mockReq),
        })
      );
      expect(res.scope_type).toBe("portfolio");
    });
  });
});
