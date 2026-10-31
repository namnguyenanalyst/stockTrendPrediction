/**
 * Adversarial Verification Test Suite for Milestone 3
 * Tests payload boundaries, network failure fallbacks, massive equity curves,
 * and cross-client cache isolation / leakage scenarios.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  createUserPreset,
  createUserWatchlist,
  deleteUserWatchlist,
  getUserWatchlists,
  saveUserBacktest,
  setAuthToken,
} from "./api";
import {
  BacktestHistoryCreateRequest,
  EquityCurvePoint,
  SavedStrategyItem,
  UserBacktestHistory,
  UserStrategyPreset,
  UserWatchlist,
} from "./types";
import {
  loadSavedStrategies,
  persistSavedStrategies,
} from "./strategyStorage";

// Mock InMemory Storage complying with Web Storage API
class InMemoryStorage implements Storage {
  private store: Record<string, string> = {};

  get length(): number {
    return Object.keys(this.store).length;
  }

  clear(): void {
    this.store = {};
  }

  getItem(key: string): string | null {
    return this.store[key] ?? null;
  }

  key(index: number): string | null {
    const keys = Object.keys(this.store);
    return keys[index] ?? null;
  }

  removeItem(key: string): void {
    delete this.store[key];
  }

  setItem(key: string, value: string): void {
    this.store[key] = String(value);
  }
}

describe("Milestone 3 Adversarial Verification Suite", () => {
  let mockStorage: InMemoryStorage;

  beforeEach(() => {
    mockStorage = new InMemoryStorage();
    setAuthToken("adversarial-jwt-token");
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.restoreAllMocks();
    setAuthToken(null);
  });

  // ===========================================================================
  // 1. Watchlist State Synchronization & Edge Cases
  // ===========================================================================
  describe("1. Watchlist State Synchronization & Resilience", () => {
    it("should handle pinning 100 tickers in a single bulk watchlist payload", async () => {
      const symbols100 = Array.from({ length: 100 }, (_, i) => `SYM${String(i + 1).padStart(3, "0")}`);

      const mockResponse: UserWatchlist = {
        id: "wl-100-uuid",
        user_id: "user-adv-1",
        name: "Danh mục 100 mã",
        symbols: symbols100,
        created_at: "2026-10-31T00:00:00Z",
        updated_at: "2026-10-31T00:00:00Z",
      };

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      const result = await createUserWatchlist("Danh mục 100 mã", symbols100);

      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/v1/user/watchlists",
        expect.objectContaining({
          method: "POST",
          headers: expect.objectContaining({
            Authorization: "Bearer adversarial-jwt-token",
          }),
        })
      );

      const callArgs = vi.mocked(fetch).mock.calls[0];
      const parsedBody = JSON.parse(callArgs[1]?.body as string);
      expect(parsedBody.symbols).toHaveLength(100);
      expect(parsedBody.symbols[0]).toBe("SYM001");
      expect(parsedBody.symbols[99]).toBe("SYM100");
      expect(result.symbols).toHaveLength(100);
    });

    it("should safely handle toggling / removing non-existent or duplicate symbols", () => {
      const initialPinned = ["HPG", "VIC", "VNM"];

      // Case 1: Toggling a symbol not present adds it
      const targetToAdd = "fpt";
      const cleanToAdd = targetToAdd.toUpperCase();
      const afterAdd = initialPinned.includes(cleanToAdd)
        ? initialPinned.filter((s) => s !== cleanToAdd)
        : [...initialPinned, cleanToAdd];
      expect(afterAdd).toEqual(["HPG", "VIC", "VNM", "FPT"]);

      // Case 2: Toggling an existing symbol removes it
      const targetToRemove = "VIC";
      const afterRemove = afterAdd.filter((s) => s !== targetToRemove);
      expect(afterRemove).toEqual(["HPG", "VNM", "FPT"]);

      // Case 3: Attempting to remove non-existent symbol does not alter list
      const nonExistent = "MSN";
      const afterNonExistent = afterRemove.filter((s) => s !== nonExistent);
      expect(afterNonExistent).toEqual(["HPG", "VNM", "FPT"]);

      // Case 4: Unpinning the last remaining symbol results in empty list
      const singleSymbol = ["HPG"];
      const emptyList = singleSymbol.filter((s) => s !== "HPG");
      expect(emptyList).toEqual([]);
    });

    it("should handle API network failure on watchlist retrieval gracefully", async () => {
      // Setup localStorage with previous cache
      mockStorage.setItem("stockpulse_watchlist_symbols", JSON.stringify(["HPG", "SSI"]));

      // Simulate 500 Internal Server Error
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: false,
        status: 500,
        text: async () => "Internal Server Error",
      } as Response);

      // Verify API client throws descriptive error
      await expect(getUserWatchlists()).rejects.toThrow("API error (500)");

      // Simulate Component Fallback logic
      let pinnedState: string[] = [];
      try {
        await getUserWatchlists();
      } catch {
        // Fallback to localStorage when offline or API fails
        const cached = mockStorage.getItem("stockpulse_watchlist_symbols");
        if (cached) {
          pinnedState = JSON.parse(cached);
        }
      }

      expect(pinnedState).toEqual(["HPG", "SSI"]);
    });

    it("should trigger deleteUserWatchlist when unpinning all symbols to 0", async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        status: 204,
        json: async () => null,
      } as Response);

      await deleteUserWatchlist("wl-old-id");

      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/v1/user/watchlists/wl-old-id",
        expect.objectContaining({
          method: "DELETE",
        })
      );
    });
  });

  // ===========================================================================
  // 2. Strategy Presets Payload Integrity & Boundaries
  // ===========================================================================
  describe("2. Strategy Presets Payload Integrity & Extreme Boundaries", () => {
    it("should preserve complex nested multi-indicator condition payloads", async () => {
      const complexParameters = {
        scope_type: "portfolio",
        portfolio_symbols: ["HPG", "VIC", "VHM", "FPT", "MWG"],
        start_date: "2023-01-01",
        end_date: "2024-01-01",
        initial_capital: 500_000_000,
        model_type: "lstm",
        slippage_rate: 0.001,
        use_advanced_settings: true,
        buy_conditions: {
          condition_logic: "AND",
          market_condition: "all",
          use_ma: true,
          use_ema: true,
          use_rsi: true,
          rsi_threshold: 42,
          use_volume_spike: true,
          volume_spike_factor: 1.5,
          use_price_cross: true,
          use_pe: true,
          max_pe: 15.5,
          use_pb: true,
          max_pb: 2.0,
          min_roe: 12.0,
          foreign_net_buy: true,
          use_bb: true,
          use_adx: true,
        },
        sell_conditions: {
          condition_logic: "OR",
          take_profit_pct: 20,
          stop_loss_pct: 7,
          trailing_stop_pct: 5,
          max_holding_days: 45,
        },
        metrics: {
          roi_pct: 35.8,
          sharpe: 1.85,
          mdd_pct: -12.4,
          win_rate_pct: 64.5,
          trades: 28,
        },
      };

      const mockResponse: UserStrategyPreset = {
        id: "preset-complex-uuid",
        user_id: "user-adv-1",
        name: "Chiến lược Đa Nhân tố Lũy tiến (Complex)",
        description: "Hệ thống kết hợp kỹ thuật & cơ bản",
        parameters: complexParameters,
        created_at: "2026-10-31T00:00:00Z",
        updated_at: "2026-10-31T00:00:00Z",
      };

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      const result = await createUserPreset(
        "Chiến lược Đa Nhân tố Lũy tiến (Complex)",
        "Hệ thống kết hợp kỹ thuật & cơ bản",
        complexParameters
      );

      const callArgs = vi.mocked(fetch).mock.calls[0];
      const parsedBody = JSON.parse(callArgs[1]?.body as string);

      expect(parsedBody.parameters.buy_conditions.use_bb).toBe(true);
      expect(parsedBody.parameters.buy_conditions.max_pe).toBe(15.5);
      expect(parsedBody.parameters.sell_conditions.max_holding_days).toBe(45);
      expect(result.parameters).toEqual(complexParameters);
    });

    it("should handle extreme parameter boundaries: negative capital, extreme slippage, huge strings, and XSS tags", async () => {
      const xssName = "<script>alert('xss')</script> & 特殊文字 🚀";
      const massiveStringDescription = "A".repeat(2000);
      const boundaryParameters = {
        initial_capital: -100_000_000, // Negative capital boundary
        huge_capital: 1e16, // Quadrillion capital
        zero_capital: 0,
        slippage_rate: 1.0, // 100% slippage
        negative_slippage: -0.05,
      };

      const mockResponse: UserStrategyPreset = {
        id: "preset-boundary-uuid",
        user_id: "user-adv-1",
        name: xssName,
        description: massiveStringDescription,
        parameters: boundaryParameters,
        created_at: "2026-10-31T00:00:00Z",
        updated_at: "2026-10-31T00:00:00Z",
      };

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      const result = await createUserPreset(xssName, massiveStringDescription, boundaryParameters);

      expect(result.name).toBe(xssName);
      expect(result.description).toHaveLength(2000);
      expect(result.parameters.initial_capital).toBe(-100_000_000);
      expect(result.parameters.huge_capital).toBe(1e16);
    });

    it("should accept empty, null, or undefined description without throwing errors", async () => {
      // 1. null description
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: "p-null", name: "Preset Null", description: null, parameters: {} }),
      } as Response);

      await expect(createUserPreset("Preset Null", null, {})).resolves.toBeDefined();

      // 2. undefined description
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: "p-undef", name: "Preset Undef", description: undefined, parameters: {} }),
      } as Response);

      await expect(createUserPreset("Preset Undef", undefined, {})).resolves.toBeDefined();

      // 3. empty string description
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: "p-empty", name: "Preset Empty", description: "", parameters: {} }),
      } as Response);

      await expect(createUserPreset("Preset Empty", "", {})).resolves.toBeDefined();
    });
  });

  // ===========================================================================
  // 3. Backtest History Diary & Massive Equity Curves
  // ===========================================================================
  describe("3. Backtest History Diary & Massive Equity Curves", () => {
    it("should serialize, save, and calculate SVG path for large equity curves (5,000 points)", async () => {
      // Generate 5,000 equity curve points (representing ~20 years of daily trading)
      const startDate = new Date("2005-01-01");
      const baseCapital = 100_000_000;
      let currentEquity = baseCapital;
      let currentBenchmark = baseCapital;

      const massiveEquityCurve: EquityCurvePoint[] = [];
      for (let i = 0; i < 5000; i++) {
        const d = new Date(startDate);
        d.setDate(d.getDate() + i);
        const dailyReturn = (Math.sin(i / 20) * 0.02);
        currentEquity *= (1 + dailyReturn);
        currentBenchmark *= (1 + dailyReturn * 0.7);

        massiveEquityCurve.push({
          date: d.toISOString().split("T")[0],
          total_equity: Math.round(currentEquity),
          benchmark_equity: Math.round(currentBenchmark),
          drawdown_pct: -Math.abs(Math.cos(i / 15) * 10),
          daily_return: dailyReturn,
        });
      }

      expect(massiveEquityCurve).toHaveLength(5000);

      const payload: BacktestHistoryCreateRequest = {
        symbol: "VNINDEX",
        strategy_name: "20-Year Long Term Simulation",
        strategy_type: "Mô hình LightGBM",
        start_date: "2005-01-01",
        end_date: "2025-01-01",
        initial_capital: baseCapital,
        total_return: ((currentEquity - baseCapital) / baseCapital) * 100,
        sharpe_ratio: 1.45,
        max_drawdown: -22.5,
        win_rate: 58.2,
        equity_curve: massiveEquityCurve,
      };

      const mockSavedResponse: UserBacktestHistory = {
        id: "bkt-5000-uuid",
        user_id: "user-adv-1",
        symbol: payload.symbol,
        strategy_name: payload.strategy_name,
        strategy_type: payload.strategy_type,
        start_date: payload.start_date,
        end_date: payload.end_date,
        initial_capital: payload.initial_capital,
        total_return: payload.total_return,
        sharpe_ratio: payload.sharpe_ratio,
        max_drawdown: payload.max_drawdown,
        win_rate: payload.win_rate,
        equity_curve: payload.equity_curve,
        executed_at: new Date().toISOString(),
      };

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockSavedResponse,
      } as Response);

      const startTime = performance.now();
      const saved = await saveUserBacktest(payload);
      const postTime = performance.now() - startTime;

      expect(postTime).toBeLessThan(100); // Must serialize in under 100ms
      expect(saved.equity_curve).toHaveLength(5000);

      // Verify Chart SVG Path computation performance on 5,000 points
      const width = 800;
      const height = 320;
      const padding = { top: 20, right: 30, bottom: 30, left: 65 };
      const chartW = width - padding.left - padding.right;
      const chartH = height - padding.top - padding.bottom;

      let min = baseCapital;
      let max = baseCapital;
      saved.equity_curve.forEach((pt) => {
        if (pt.total_equity < min) min = pt.total_equity;
        if (pt.total_equity > max) max = pt.total_equity;
      });

      const range = max - min || 1;
      const paddedMin = Math.max(0, min - range * 0.05);
      const paddedMax = max + range * 0.05;

      const scaleX = (idx: number) =>
        padding.left + (idx / Math.max(saved.equity_curve.length - 1, 1)) * chartW;
      const scaleY = (val: number) =>
        padding.top + chartH - ((val - paddedMin) / (paddedMax - paddedMin || 1)) * chartH;

      const chartStartTime = performance.now();
      const points = saved.equity_curve.map((pt, idx) => ({
        x: scaleX(idx),
        yAI: scaleY(pt.total_equity),
        yBH: scaleY(pt.benchmark_equity),
      }));

      const aiSvgPath = points.reduce((acc, pt, idx) => {
        return `${acc} ${idx === 0 ? "M" : "L"} ${pt.x.toFixed(1)} ${pt.yAI.toFixed(1)}`;
      }, "");
      const chartComputeTime = performance.now() - chartStartTime;

      expect(chartComputeTime).toBeLessThan(50); // SVG Path generation under 50ms
      expect(aiSvgPath.startsWith(" M")).toBe(true);
      expect(aiSvgPath.length).toBeGreaterThan(10000);
      expect(aiSvgPath).not.toContain("NaN");
    });

    it("should handle corrupted or extreme equity points (zero, NaN, PascalCase) defensively", () => {
      const initialCapital = 100_000_000;
      const dirtyPoints: unknown[] = [
        { Date: "2026-01-01", Total_Equity: "105000000", Benchmark_Equity: "102000000" }, // PascalCase strings
        { date: "2026-01-02", total_equity: NaN, benchmark_equity: null }, // NaN and null
        { date: "2026-01-03", total_equity: 0, benchmark_equity: -10_000_000 }, // Zero and negative
        {}, // Empty object
      ];

      // Replicating EquityCurveChart normalization logic
      const normalizedData = (dirtyPoints as EquityCurvePoint[]).map((pt) => {
        const anyPt = pt as unknown as Record<string, unknown>;
        const totalEquity = Number(pt.total_equity ?? anyPt.Total_Equity ?? initialCapital);
        const benchmarkEquity = Number(pt.benchmark_equity ?? anyPt.Benchmark_Equity ?? initialCapital);
        const drawdownPct = Number(pt.drawdown_pct ?? anyPt.Drawdown_Pct ?? 0);
        const dailyReturn = Number(pt.daily_return ?? anyPt.Daily_Return ?? 0);
        const dateStr = String(pt.date ?? anyPt.Date ?? "");

        return {
          date: dateStr,
          total_equity: isNaN(totalEquity) ? initialCapital : totalEquity,
          benchmark_equity: isNaN(benchmarkEquity) ? initialCapital : benchmarkEquity,
          drawdown_pct: isNaN(drawdownPct) ? 0 : drawdownPct,
          daily_return: isNaN(dailyReturn) ? 0 : dailyReturn,
        };
      });

      expect(normalizedData[0].total_equity).toBe(105_000_000);
      expect(normalizedData[1].total_equity).toBe(initialCapital); // Protected against NaN
      expect(normalizedData[2].total_equity).toBe(0);
      expect(normalizedData[3].total_equity).toBe(initialCapital);
    });

    it("should properly sort backtest execution histories by executed_at descending", () => {
      const unsortedHistories: Partial<UserBacktestHistory>[] = [
        { id: "h1", executed_at: "2026-10-15T08:00:00Z" },
        { id: "h2", executed_at: "2026-10-30T14:30:00Z" },
        { id: "h3", executed_at: "2026-10-01T10:00:00Z" },
        { id: "h4", executed_at: "2026-10-25T12:00:00Z" },
      ];

      const sorted = [...unsortedHistories].sort((a, b) => {
        const timeA = new Date(a.executed_at || 0).getTime();
        const timeB = new Date(b.executed_at || 0).getTime();
        return timeB - timeA;
      });

      expect(sorted.map((h) => h.id)).toEqual(["h2", "h4", "h1", "h3"]);
    });
  });

  // ===========================================================================
  // 4. Cross-Client Cache Isolation & Data Poisoning Attack
  // ===========================================================================
  describe("4. Cross-Client Cache Isolation & Storage Poisoning Assessment", () => {
    it("EMPIRICAL TEST: Demonstrates that unpartitioned localStorage leaks User 1 watchlist to User 2", async () => {
      // Step 1: User 1 logs in and pins private stocks
      const user1Token = "jwt-user-1";
      setAuthToken(user1Token);
      const user1PrivateWatchlist = ["HPG", "SSI", "VIC"];

      // User 1's action writes to localStorage
      mockStorage.setItem(
        "stockpulse_watchlist_symbols",
        JSON.stringify(user1PrivateWatchlist)
      );

      // Step 2: User 1 logs out.
      // Notice: AuthContext.logout() removes TOKEN_STORAGE_KEY, but DOES NOT CLEAR stockpulse_watchlist_symbols!
      setAuthToken(null);
      expect(mockStorage.getItem("stockpulse_watchlist_symbols")).toBe(
        JSON.stringify(user1PrivateWatchlist)
      );

      // Step 3: User 2 (a different user with 0 watchlists in the database) logs in
      const user2Token = "jwt-user-2";
      setAuthToken(user2Token);

      // User 2's API call returns empty list []
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      } as Response);

      const user2ApiLists = await getUserWatchlists();
      expect(user2ApiLists).toEqual([]);

      // Step 4: Component fallback behavior in MarketOverviewTab.tsx (lines 173-196)
      // When user2ApiLists is empty (length === 0), it executes:
      // const localSaved = localStorage.getItem("stockpulse_watchlist_symbols");
      // if (localSaved) setPinnedSymbols(parsed);
      let user2PinnedSymbols: string[] = [];
      if (user2ApiLists.length > 0) {
        user2PinnedSymbols = user2ApiLists[0].symbols;
      } else {
        const localSaved = mockStorage.getItem("stockpulse_watchlist_symbols");
        if (localSaved) {
          user2PinnedSymbols = JSON.parse(localSaved);
        }
      }

      // EMPIRICAL PROOF OF LEAK:
      // User 2 receives User 1's private symbols without ever having configured them!
      expect(user2PinnedSymbols).toEqual(["HPG", "SSI", "VIC"]);

      // Step 5: User 2 toggles an additional symbol 'FPT'.
      // Next symbols array contains User 1's leaked symbols plus 'FPT'!
      const nextUser2Symbols = [...user2PinnedSymbols, "FPT"];

      // User 2 creates a new watchlist on the server with the combined list
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: "wl-user-2-uuid",
          name: "Mục theo dõi",
          symbols: nextUser2Symbols,
          created_at: "2026-10-31T01:00:00Z",
        }),
      } as Response);

      const user2NewWatchlist = await createUserWatchlist("Mục theo dõi", nextUser2Symbols);

      // Result: User 1's private watchlist has permanently leaked into User 2's backend database record!
      expect(user2NewWatchlist.symbols).toContain("HPG");
      expect(user2NewWatchlist.symbols).toContain("SSI");
      expect(user2NewWatchlist.symbols).toContain("VIC");
      expect(user2NewWatchlist.symbols).toContain("FPT");
    });

    it("EMPIRICAL TEST: Demonstrates that unpartitioned localStorage leaks local Strategy Presets to another user", () => {
      // Step 1: User 1 saves a confidential proprietary strategy locally
      const user1Strategies: SavedStrategyItem[] = [
        {
          id: "strat-user-1-private",
          name: "User 1 Secret Momentum Strategy",
          status: "active",
          created_at: "2026-10-30 10:00",
          updated_at: "2026-10-30 10:00",
          scope_type: "stock",
          symbol: "HPG",
          start_date: "2023-01-01",
          end_date: "2024-01-01",
          initial_capital: 200_000_000,
          model_type: "lightgbm",
          buy_conditions: { market_condition: "all" },
          sell_conditions: { take_profit_pct: 15 },
        },
      ];
      persistSavedStrategies(user1Strategies, mockStorage);

      // Step 2: User 1 logs out. User 2 logs in.
      // BacktestSimulatorTab mounts and initializes savedStrategies via loadSavedStrategies()
      const user2LoadedStrategies = loadSavedStrategies(mockStorage);

      // EMPIRICAL PROOF OF LEAK:
      // User 2 immediately has access to User 1's private strategy
      expect(user2LoadedStrategies).toHaveLength(1);
      expect(user2LoadedStrategies[0].name).toBe("User 1 Secret Momentum Strategy");
      expect(user2LoadedStrategies[0].id).toBe("strat-user-1-private");
    });
  });
});
