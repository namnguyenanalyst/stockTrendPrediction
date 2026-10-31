import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  createUserPreset,
  createUserWatchlist,
  deleteUserPreset,
  deleteUserWatchlist,
  getUserBacktests,
  getUserPresets,
  getUserWatchlists,
  saveUserBacktest,
  setAuthToken,
} from "./api";
import { BacktestHistoryCreateRequest } from "./types";

describe("Frontend Personalization Suite (src/lib/personalization.test.ts)", () => {
  beforeEach(() => {
    setAuthToken("test-bearer-token");
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.restoreAllMocks();
    setAuthToken(null);
  });

  describe("Watchlist Personalization Endpoints", () => {
    it("getUserWatchlists should fetch /api/v1/user/watchlists with credentials and auth", async () => {
      const mockWatchlists = [
        {
          id: "wl-1",
          user_id: "u-1",
          name: "Mục theo dõi",
          symbols: ["HPG", "VIC", "FPT"],
          created_at: "2026-10-30T10:00:00Z",
          updated_at: "2026-10-30T10:00:00Z",
        },
      ];

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockWatchlists,
      } as Response);

      const result = await getUserWatchlists();

      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/v1/user/watchlists",
        expect.objectContaining({
          credentials: "include",
          headers: expect.objectContaining({
            Authorization: "Bearer test-bearer-token",
          }),
        })
      );
      expect(result).toHaveLength(1);
      expect(result[0].symbols).toEqual(["HPG", "VIC", "FPT"]);
    });

    it("createUserWatchlist should POST /api/v1/user/watchlists with name and symbols", async () => {
      const newWatchlist = {
        id: "wl-2",
        name: "Cổ phiếu Thép",
        symbols: ["HPG", "NKG", "HSG"],
        created_at: "2026-10-30T10:00:00Z",
        updated_at: "2026-10-30T10:00:00Z",
      };

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => newWatchlist,
      } as Response);

      const result = await createUserWatchlist("Cổ phiếu Thép", ["HPG", "NKG", "HSG"]);

      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/v1/user/watchlists",
        expect.objectContaining({
          method: "POST",
          credentials: "include",
          body: JSON.stringify({ name: "Cổ phiếu Thép", symbols: ["HPG", "NKG", "HSG"] }),
        })
      );
      expect(result.name).toBe("Cổ phiếu Thép");
    });

    it("deleteUserWatchlist should DELETE /api/v1/user/watchlists/:id and handle 204 No Content", async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        status: 204,
        json: async () => null,
      } as Response);

      await expect(deleteUserWatchlist("wl-1")).resolves.toBeUndefined();

      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/v1/user/watchlists/wl-1",
        expect.objectContaining({
          method: "DELETE",
          credentials: "include",
        })
      );
    });
  });

  describe("Strategy Preset Personalization Endpoints", () => {
    it("getUserPresets should fetch /api/v1/user/presets", async () => {
      const mockPresets = [
        {
          id: "pre-1",
          name: "Trend Following HPG",
          description: "Chiến lược bám xu hướng MA & RSI",
          parameters: {
            scope_type: "stock",
            symbol: "HPG",
            model_type: "lightgbm",
            initial_capital: 100_000_000,
          },
          created_at: "2026-10-30T10:00:00Z",
          updated_at: "2026-10-30T10:00:00Z",
        },
      ];

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockPresets,
      } as Response);

      const result = await getUserPresets();

      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/v1/user/presets",
        expect.objectContaining({
          credentials: "include",
        })
      );
      expect(result).toHaveLength(1);
      expect(result[0].name).toBe("Trend Following HPG");
    });

    it("createUserPreset should POST /api/v1/user/presets with name, description, parameters", async () => {
      const mockCreated = {
        id: "pre-2",
        name: "Breakout VN30",
        description: "Phá vỡ kháng cự",
        parameters: { scope_type: "index", selectedIndex: "VN30" },
        created_at: "2026-10-30T10:00:00Z",
        updated_at: "2026-10-30T10:00:00Z",
      };

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockCreated,
      } as Response);

      const result = await createUserPreset(
        "Breakout VN30",
        "Phá vỡ kháng cự",
        { scope_type: "index", selectedIndex: "VN30" }
      );

      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/v1/user/presets",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({
            name: "Breakout VN30",
            description: "Phá vỡ kháng cự",
            parameters: { scope_type: "index", selectedIndex: "VN30" },
          }),
        })
      );
      expect(result.id).toBe("pre-2");
    });

    it("deleteUserPreset should DELETE /api/v1/user/presets/:id", async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        status: 204,
      } as Response);

      await expect(deleteUserPreset("pre-2")).resolves.toBeUndefined();
      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/v1/user/presets/pre-2",
        expect.objectContaining({
          method: "DELETE",
        })
      );
    });
  });

  describe("Backtest History Endpoints", () => {
    it("getUserBacktests should fetch /api/v1/user/backtests and return historical runs", async () => {
      const mockHistory = [
        {
          id: "hist-1",
          symbol: "VIC",
          strategy_name: "Chiến lược AI LSTM",
          strategy_type: "AI (LSTM)",
          start_date: "2023-01-01",
          end_date: "2024-01-01",
          initial_capital: 100_000_000,
          total_return: 28.5,
          sharpe_ratio: 1.85,
          max_drawdown: 9.2,
          win_rate: 62.5,
          equity_curve: [
            { date: "2023-01-03", total_equity: 100_000_000 },
            { date: "2024-01-01", total_equity: 128_500_000 },
          ],
          executed_at: "2026-10-30T10:00:00Z",
        },
      ];

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockHistory,
      } as Response);

      const result = await getUserBacktests();

      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/v1/user/backtests",
        expect.objectContaining({
          credentials: "include",
        })
      );
      expect(result).toHaveLength(1);
      expect(result[0].total_return).toBe(28.5);
      expect(result[0].equity_curve).toHaveLength(2);
    });

    it("saveUserBacktest should POST /api/v1/user/backtests with metrics and equity curve", async () => {
      const payload: BacktestHistoryCreateRequest = {
        symbol: "FPT",
        strategy_name: "LightGBM Trend",
        strategy_type: "AI (LIGHTGBM)",
        start_date: "2023-01-01",
        end_date: "2024-01-01",
        initial_capital: 100_000_000,
        total_return: 35.4,
        sharpe_ratio: 2.1,
        max_drawdown: 7.8,
        win_rate: 66.7,
        equity_curve: [
          {
            date: "2023-01-03",
            total_equity: 100_000_000,
            benchmark_equity: 100_000_000,
            drawdown_pct: 0,
            daily_return: 0,
          },
          {
            date: "2024-01-01",
            total_equity: 135_400_000,
            benchmark_equity: 110_000_000,
            drawdown_pct: 0,
            daily_return: 0.02,
          },
        ],
      };

      const mockSaved = {
        id: "hist-2",
        ...payload,
        executed_at: "2026-10-30T10:05:00Z",
      };

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockSaved,
      } as Response);

      const result = await saveUserBacktest(payload);

      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/v1/user/backtests",
        expect.objectContaining({
          method: "POST",
          credentials: "include",
          body: JSON.stringify(payload),
        })
      );
      expect(result.id).toBe("hist-2");
      expect(result.symbol).toBe("FPT");
    });
  });
});
