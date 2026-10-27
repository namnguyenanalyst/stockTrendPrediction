import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  STRATEGY_STORAGE_KEY,
  SaveStrategyInput,
  deleteStrategy,
  filterStrategies,
  generateCopyStrategyName,
  generateStrategyId,
  getCurrentDateTimeString,
  getDynamicDateRange,
  loadSavedStrategies,
  mapPresetToStrategyConfig,
  persistSavedStrategies,
  saveOrUpdateStrategy,
  togglePortfolioSymbolList,
  toggleStrategyStatus,
  validateDateRange,
} from "./strategyStorage";
import {
  BacktestConditionFilter,
  SavedStrategyItem,
  StrategyPresetItem,
} from "./types";

/**
 * Mock InMemory Storage tuân thủ chuẩn Web Storage API
 */
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

describe("Strategy Storage & Laboratory Logic (strategyStorage.ts)", () => {
  let mockStorage: InMemoryStorage;

  const defaultBuyCondition: BacktestConditionFilter = {
    condition_logic: "AND",
    use_ma: true,
    ma_left: "MA 20",
    ma_operator: "Cắt lên",
    ma_right: "MA 50",
  };

  const defaultSellCondition: BacktestConditionFilter = {
    condition_logic: "OR",
    take_profit_pct: 10,
    stop_loss_pct: 5,
  };

  const createDummyStrategy = (
    overrides?: Partial<SavedStrategyItem>
  ): SavedStrategyItem => ({
    id: "strat-test-101",
    name: "Chiến lược Động lượng Cơ bản",
    status: "active",
    created_at: "2026-10-20 09:30",
    updated_at: "2026-10-20 09:30",
    scope_type: "stock",
    symbol: "SSI",
    index_name: undefined,
    sector_name: undefined,
    portfolio_symbols: undefined,
    start_date: "2025-10-20",
    end_date: "2026-10-20",
    initial_capital: 100_000_000,
    model_type: "lightgbm",
    buy_conditions: defaultBuyCondition,
    sell_conditions: defaultSellCondition,
    ...overrides,
  });

  beforeEach(() => {
    mockStorage = new InMemoryStorage();
    vi.stubGlobal("localStorage", mockStorage);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // ==========================================
  // 1. generateStrategyId & Datetime Format
  // ==========================================
  describe("generateStrategyId", () => {
    it("should generate a string ID with default 'strat' prefix and timestamp", () => {
      // Act
      const id = generateStrategyId();

      // Assert
      expect(id).toMatch(/^strat-\d+$/);
    });

    it("should support custom prefix when provided", () => {
      // Act
      const id = generateStrategyId("custom");

      // Assert
      expect(id).toMatch(/^custom-\d+$/);
    });
  });

  describe("getCurrentDateTimeString", () => {
    it("should format dates in Vietnamese locale standard", () => {
      // Arrange
      const fixedDate = new Date("2026-10-25T14:30:00Z");

      // Act
      const formatted = getCurrentDateTimeString(fixedDate);

      // Assert: Chuỗi phải chứa đầy đủ năm 2026 và giờ phút
      expect(formatted).toContain("2026");
      expect(typeof formatted).toBe("string");
    });
  });

  // ==========================================
  // 2. getDynamicDateRange & validateDateRange
  // ==========================================
  describe("getDynamicDateRange", () => {
    it("should rollback 1 day when reference date is Saturday", () => {
      // Arrange: 2026-10-24 là Thứ Bảy
      const saturday = new Date("2026-10-24T10:00:00Z");

      // Act
      const range = getDynamicDateRange(saturday);

      // Assert: Lùi về Thứ Sáu 2026-10-23
      expect(range.end).toBe("2026-10-23");
      expect(range.start).toBe("2025-10-23");
    });

    it("should rollback 2 days when reference date is Sunday", () => {
      // Arrange: 2026-10-25 là Chủ Nhật
      const sunday = new Date("2026-10-25T10:00:00Z");

      // Act
      const range = getDynamicDateRange(sunday);

      // Assert: Lùi về Thứ Sáu 2026-10-23
      expect(range.end).toBe("2026-10-23");
      expect(range.start).toBe("2025-10-23");
    });

    it("should not rollback when reference date is a weekday (Monday to Friday)", () => {
      // Arrange: 2026-10-21 là Thứ Tư
      const wednesday = new Date("2026-10-21T10:00:00Z");

      // Act
      const range = getDynamicDateRange(wednesday);

      // Assert
      expect(range.end).toBe("2026-10-21");
      expect(range.start).toBe("2025-10-21");
    });
  });

  describe("validateDateRange", () => {
    it("should validate successfully when range is within 365 days", () => {
      // Arrange
      const start = "2026-01-01";
      const end = "2026-06-30";

      // Act
      const result = validateDateRange(start, end);

      // Assert
      expect(result.isValid).toBe(true);
      expect(result.error).toBeUndefined();
      expect(result.diffDays).toBe(180);
    });

    it("should reject when end date is earlier than start date", () => {
      // Arrange
      const start = "2026-06-01";
      const end = "2026-05-01";

      // Act
      const result = validateDateRange(start, end);

      // Assert
      expect(result.isValid).toBe(false);
      expect(result.error).toContain("Ngày kết thúc phải sau ngày bắt đầu");
      expect(result.diffDays).toBeLessThan(0);
    });

    it("should reject when date range exceeds 365 days (DNSE standard rule)", () => {
      // Arrange
      const start = "2025-01-01";
      const end = "2026-02-01"; // ~396 days

      // Act
      const result = validateDateRange(start, end);

      // Assert
      expect(result.isValid).toBe(false);
      expect(result.error).toContain("không quá 1 năm (tối đa 365 ngày)");
      expect(result.diffDays).toBeGreaterThan(365);
    });

    it("should return invalid for malformed date strings", () => {
      // Act
      const result = validateDateRange("invalid-date", "2026-10-25");

      // Assert
      expect(result.isValid).toBe(false);
      expect(result.error).toContain("không hợp lệ");
    });
  });

  // ==========================================
  // 3. Storage I/O: load & persist
  // ==========================================
  describe("loadSavedStrategies", () => {
    it("should return an empty array if storage is empty", () => {
      // Act
      const list = loadSavedStrategies(mockStorage);

      // Assert
      expect(list).toEqual([]);
    });

    it("should parse and return strategies from storage", () => {
      // Arrange
      const dummy = [createDummyStrategy()];
      mockStorage.setItem(STRATEGY_STORAGE_KEY, JSON.stringify(dummy));

      // Act
      const list = loadSavedStrategies(mockStorage);

      // Assert
      expect(list).toHaveLength(1);
      expect(list[0].id).toBe("strat-test-101");
    });

    it("should filter out legacy seed dummy items (strat-seed-1 & strat-seed-2)", () => {
      // Arrange
      const dummyWithSeeds = [
        createDummyStrategy({ id: "strat-seed-1", name: "Seed 1" }),
        createDummyStrategy({ id: "strat-seed-2", name: "Seed 2" }),
        createDummyStrategy({ id: "strat-user-1", name: "User Strategy" }),
      ];
      mockStorage.setItem(STRATEGY_STORAGE_KEY, JSON.stringify(dummyWithSeeds));

      // Act
      const list = loadSavedStrategies(mockStorage);

      // Assert
      expect(list).toHaveLength(1);
      expect(list[0].id).toBe("strat-user-1");

      // Verify that the cleaned list is persisted back
      const rawStored = JSON.parse(mockStorage.getItem(STRATEGY_STORAGE_KEY) || "[]");
      expect(rawStored).toHaveLength(1);
      expect(rawStored[0].id).toBe("strat-user-1");
    });

    it("should safely return empty array if JSON in storage is corrupted", () => {
      // Arrange
      mockStorage.setItem(STRATEGY_STORAGE_KEY, "{ corrupted_json_syntax");

      // Act
      const list = loadSavedStrategies(mockStorage);

      // Assert
      expect(list).toEqual([]);
    });

    it("should return empty array if storage contains non-array JSON", () => {
      // Arrange
      mockStorage.setItem(STRATEGY_STORAGE_KEY, JSON.stringify({ notAnArray: true }));

      // Act
      const list = loadSavedStrategies(mockStorage);

      // Assert
      expect(list).toEqual([]);
    });
  });

  describe("persistSavedStrategies", () => {
    it("should write strategy array to storage as JSON string", () => {
      // Arrange
      const items = [createDummyStrategy()];

      // Act
      const success = persistSavedStrategies(items, mockStorage);

      // Assert
      expect(success).toBe(true);
      expect(mockStorage.getItem(STRATEGY_STORAGE_KEY)).toBe(JSON.stringify(items));
    });

    it("should return false gracefully if storage fails", () => {
      // Arrange
      const failingStorage = {
        setItem: () => {
          throw new Error("QuotaExceeded");
        },
      } as unknown as Storage;

      // Act
      const success = persistSavedStrategies([], failingStorage);

      // Assert
      expect(success).toBe(false);
    });
  });

  // ==========================================
  // 4. saveOrUpdateStrategy (CRUD & Overwrite)
  // ==========================================
  describe("saveOrUpdateStrategy", () => {
    const baseInput: SaveStrategyInput = {
      name: "Chiến thuật Tăng trưởng SSI",
      status: "draft",
      scope_type: "stock",
      symbol: "SSI",
      start_date: "2025-10-01",
      end_date: "2026-10-01",
      initial_capital: 50_000_000,
      model_type: "lstm",
      buy_conditions: defaultBuyCondition,
      sell_conditions: defaultSellCondition,
    };

    it("should prepend a newly created strategy to the list", () => {
      // Arrange
      const currentList = [createDummyStrategy({ id: "strat-existing" })];

      // Act
      const { updatedList, activeId, action } = saveOrUpdateStrategy(
        currentList,
        baseInput,
        mockStorage
      );

      // Assert
      expect(action).toBe("created");
      expect(updatedList).toHaveLength(2);
      expect(updatedList[0].id).toBe(activeId);
      expect(updatedList[0].name).toBe("Chiến thuật Tăng trưởng SSI");
      expect(updatedList[0].status).toBe("draft");
      expect(updatedList[0].symbol).toBe("SSI");
    });

    it("should update existing strategy when name matches case-insensitively with trim", () => {
      // Arrange
      const existing = createDummyStrategy({
        id: "strat-same-name",
        name: "Chiến thuật Tăng trưởng SSI",
        initial_capital: 10_000_000,
      });
      const currentList = [existing];

      // Act: Tên mới có khoảng trắng và chữ hoa thường tương đương
      const { updatedList, activeId, action } = saveOrUpdateStrategy(
        currentList,
        {
          ...baseInput,
          name: "  chiến thuật tăng trưởng ssi  ",
          initial_capital: 200_000_000,
          status: "active",
        },
        mockStorage
      );

      // Assert
      expect(action).toBe("updated");
      expect(activeId).toBe("strat-same-name");
      expect(updatedList).toHaveLength(1);
      expect(updatedList[0].initial_capital).toBe(200_000_000);
      expect(updatedList[0].status).toBe("active");
    });

    it("should explicitly overwrite strategy when overwriteExistingId is provided", () => {
      // Arrange
      const existing = createDummyStrategy({
        id: "strat-target-id",
        name: "Tên ban đầu",
      });
      const currentList = [existing];

      // Act
      const { updatedList, activeId, action } = saveOrUpdateStrategy(
        currentList,
        {
          ...baseInput,
          name: "Tên Đã Đổi",
          overwriteExistingId: "strat-target-id",
        },
        mockStorage
      );

      // Assert
      expect(action).toBe("updated");
      expect(activeId).toBe("strat-target-id");
      expect(updatedList[0].name).toBe("Tên Đã Đổi");
    });

    it("should update performance metrics when provided in input", () => {
      // Arrange
      const currentList = [createDummyStrategy({ id: "strat-perf" })];
      const metrics = {
        roi_pct: 25.4,
        bh_roi_pct: 12.1,
        excess_pct: 13.3,
        sharpe: 1.85,
        mdd_pct: -6.5,
        win_rate_pct: 68.2,
        trades: 22,
      };

      // Act
      const { updatedList } = saveOrUpdateStrategy(
        currentList,
        {
          ...baseInput,
          overwriteExistingId: "strat-perf",
          metrics,
        },
        mockStorage
      );

      // Assert
      expect(updatedList[0].last_metrics?.roi_pct).toBe(25.4);
      expect(updatedList[0].last_metrics?.sharpe).toBe(1.85);
    });
  });

  // ==========================================
  // 5. toggleStrategyStatus & deleteStrategy
  // ==========================================
  describe("toggleStrategyStatus", () => {
    it("should switch status from active to draft", () => {
      // Arrange
      const list = [createDummyStrategy({ id: "strat-1", status: "active" })];

      // Act
      const { updatedList, nextStatus } = toggleStrategyStatus(
        list,
        "strat-1",
        mockStorage
      );

      // Assert
      expect(nextStatus).toBe("draft");
      expect(updatedList[0].status).toBe("draft");
    });

    it("should switch status from draft to active", () => {
      // Arrange
      const list = [createDummyStrategy({ id: "strat-2", status: "draft" })];

      // Act
      const { updatedList, nextStatus } = toggleStrategyStatus(
        list,
        "strat-2",
        mockStorage
      );

      // Assert
      expect(nextStatus).toBe("active");
      expect(updatedList[0].status).toBe("active");
    });

    it("should return unmodified list and null if strategy ID is not found", () => {
      // Arrange
      const list = [createDummyStrategy({ id: "strat-1" })];

      // Act
      const { updatedList, nextStatus } = toggleStrategyStatus(
        list,
        "non-existent-id",
        mockStorage
      );

      // Assert
      expect(nextStatus).toBeNull();
      expect(updatedList).toEqual(list);
    });
  });

  describe("deleteStrategy", () => {
    it("should remove target strategy and persist update", () => {
      // Arrange
      const list = [
        createDummyStrategy({ id: "strat-1" }),
        createDummyStrategy({ id: "strat-2" }),
      ];

      // Act
      const { updatedList, deleted } = deleteStrategy(list, "strat-1", mockStorage);

      // Assert
      expect(deleted).toBe(true);
      expect(updatedList).toHaveLength(1);
      expect(updatedList[0].id).toBe("strat-2");

      const inStorage = JSON.parse(mockStorage.getItem(STRATEGY_STORAGE_KEY) || "[]");
      expect(inStorage).toHaveLength(1);
    });

    it("should return deleted=false when target strategy ID is not found", () => {
      // Arrange
      const list = [createDummyStrategy({ id: "strat-1" })];

      // Act
      const { updatedList, deleted } = deleteStrategy(
        list,
        "strat-unknown",
        mockStorage
      );

      // Assert
      expect(deleted).toBe(false);
      expect(updatedList).toHaveLength(1);
    });
  });

  // ==========================================
  // 6. filterStrategies (Status & Search)
  // ==========================================
  describe("filterStrategies", () => {
    const sampleList: SavedStrategyItem[] = [
      createDummyStrategy({
        id: "s1",
        name: "Breakout HPG Thép",
        status: "active",
        scope_type: "stock",
        symbol: "HPG",
      }),
      createDummyStrategy({
        id: "s2",
        name: "Lướt sóng Ngân hàng",
        status: "draft",
        scope_type: "sector",
        sector_name: "Ngân hàng",
      }),
      createDummyStrategy({
        id: "s3",
        name: "Rổ VN30 Định lượng AI",
        status: "active",
        scope_type: "index",
        index_name: "VN30",
      }),
      createDummyStrategy({
        id: "s4",
        name: "Danh mục Đa mã Bluechip",
        status: "draft",
        scope_type: "portfolio",
        portfolio_symbols: ["FPT", "MWG", "TCB"],
      }),
    ];

    it("should return all items when status is 'all' and search query is empty", () => {
      // Act
      const result = filterStrategies(sampleList, "all", "");

      // Assert
      expect(result).toHaveLength(4);
    });

    it("should filter only active strategies", () => {
      // Act
      const result = filterStrategies(sampleList, "active", "");

      // Assert
      expect(result).toHaveLength(2);
      expect(result.every((s) => s.status === "active")).toBe(true);
    });

    it("should filter only draft strategies", () => {
      // Act
      const result = filterStrategies(sampleList, "draft", "");

      // Assert
      expect(result).toHaveLength(2);
      expect(result.every((s) => s.status === "draft")).toBe(true);
    });

    it("should search strategies by name (case-insensitive)", () => {
      // Act
      const result = filterStrategies(sampleList, "all", "thép");

      // Assert
      expect(result).toHaveLength(1);
      expect(result[0].id).toBe("s1");
    });

    it("should search strategies by symbol", () => {
      // Act
      const result = filterStrategies(sampleList, "all", "HPG");

      // Assert
      expect(result).toHaveLength(1);
      expect(result[0].symbol).toBe("HPG");
    });

    it("should search strategies by index name", () => {
      // Act
      const result = filterStrategies(sampleList, "all", "vn30");

      // Assert
      expect(result).toHaveLength(1);
      expect(result[0].index_name).toBe("VN30");
    });

    it("should search strategies by sector name", () => {
      // Act
      const result = filterStrategies(sampleList, "all", "ngân hàng");

      // Assert
      expect(result).toHaveLength(1);
      expect(result[0].sector_name).toBe("Ngân hàng");
    });

    it("should search strategies by matching any symbol in portfolio_symbols", () => {
      // Act
      const result = filterStrategies(sampleList, "all", "mwg");

      // Assert
      expect(result).toHaveLength(1);
      expect(result[0].id).toBe("s4");
    });

    it("should combine status filter and search query correctly", () => {
      // Act: Tìm 'HPG' trong nhóm 'draft' (HPG là 'active')
      const result = filterStrategies(sampleList, "draft", "HPG");

      // Assert
      expect(result).toHaveLength(0);
    });
  });

  // ==========================================
  // 7. generateCopyStrategyName
  // ==========================================
  describe("generateCopyStrategyName", () => {
    it("should append '(Bản sao)' when no copy exists", () => {
      // Arrange
      const existing = [createDummyStrategy({ name: "Chiến lược A" })];

      // Act
      const copyName = generateCopyStrategyName("Chiến lược A", existing);

      // Assert
      expect(copyName).toBe("Chiến lược A (Bản sao)");
    });

    it("should increment counter to '(Bản sao 2)' if '(Bản sao)' already exists", () => {
      // Arrange
      const existing = [
        createDummyStrategy({ name: "Chiến lược A" }),
        createDummyStrategy({ name: "Chiến lược A (Bản sao)" }),
      ];

      // Act
      const copyName = generateCopyStrategyName("Chiến lược A", existing);

      // Assert
      expect(copyName).toBe("Chiến lược A (Bản sao 2)");
    });

    it("should continue incrementing counter to next available index", () => {
      // Arrange
      const existing = [
        createDummyStrategy({ name: "Chiến lược B" }),
        createDummyStrategy({ name: "Chiến lược B (Bản sao)" }),
        createDummyStrategy({ name: "Chiến lược B (Bản sao 2)" }),
      ];

      // Act
      const copyName = generateCopyStrategyName("Chiến lược B", existing);

      // Assert
      expect(copyName).toBe("Chiến lược B (Bản sao 3)");
    });
  });

  // ==========================================
  // 8. togglePortfolioSymbolList
  // ==========================================
  describe("togglePortfolioSymbolList", () => {
    it("should append symbol when not yet present in portfolio", () => {
      // Arrange
      const current = ["SSI", "VND"];

      // Act
      const updated = togglePortfolioSymbolList(current, "HPG");

      // Assert
      expect(updated).toEqual(["SSI", "VND", "HPG"]);
    });

    it("should remove symbol when present and portfolio has more than 1 item", () => {
      // Arrange
      const current = ["SSI", "VND", "HPG"];

      // Act
      const updated = togglePortfolioSymbolList(current, "VND");

      // Assert
      expect(updated).toEqual(["SSI", "HPG"]);
    });

    it("should NOT remove the last symbol to prevent empty portfolio", () => {
      // Arrange
      const current = ["SSI"];

      // Act
      const updated = togglePortfolioSymbolList(current, "SSI");

      // Assert: Vẫn giữ nguyên 'SSI'
      expect(updated).toEqual(["SSI"]);
    });
  });

  // ==========================================
  // 9. mapPresetToStrategyConfig
  // ==========================================
  describe("mapPresetToStrategyConfig", () => {
    const basePreset: StrategyPresetItem = {
      id: "dnse-01",
      name: "Sóng bùng nổ theo dòng tiền lớn",
      description: "Tín hiệu EMA & Khối lượng đột biến",
      category: "VN30 Tăng trưởng",
      model_type: "lightgbm",
      default_symbol: "HPG",
      target_symbols: ["HPG"],
      conditions_summary: "EMA & Khối lượng",
      win_rate_pct: 71.5,
      cumulative_pnl_pct: 28.5,
      risk_reward_ratio: "1:2.1",
      copy_count: 142,
      timeframe: "1D",
      take_profit_pct: 12,
      stop_loss_pct: 5,
      trailing_stop_pct: 4,
    };

    it("should map preset with VN30 category to index scope", () => {
      // Act
      const config = mapPresetToStrategyConfig(basePreset);

      // Assert
      expect(config.scope_type).toBe("index");
      expect(config.index_name).toBe("VN30");
      expect(config.sell_conditions.take_profit_pct).toBe(12);
      expect(config.sell_conditions.stop_loss_pct).toBe(5);
      expect(config.sell_conditions.trailing_stop_pct).toBe(4);
    });

    it("should map preset with sector category to sector scope", () => {
      // Arrange
      const sectorPreset: StrategyPresetItem = {
        ...basePreset,
        id: "dnse-03",
        category: "Ngân hàng Tích luỹ",
      };

      // Act
      const config = mapPresetToStrategyConfig(sectorPreset);

      // Assert
      expect(config.scope_type).toBe("sector");
      expect(config.sector_name).toBe("Ngân hàng");
      expect(config.buy_conditions.use_pe).toBe(true);
      expect(config.buy_conditions.max_pe).toBe(16);
    });

    it("should map preset with target_symbols > 1 to portfolio scope", () => {
      // Arrange
      const portfolioPreset: StrategyPresetItem = {
        ...basePreset,
        id: "dnse-06",
        category: "Đa mã Tăng trưởng",
        target_symbols: ["FPT", "SSI", "MWG"],
      };

      // Act
      const config = mapPresetToStrategyConfig(portfolioPreset);

      // Assert
      expect(config.scope_type).toBe("portfolio");
      expect(config.portfolio_symbols).toEqual(["FPT", "SSI", "MWG"]);
      expect(config.buy_conditions.use_price_increase).toBe(true);
      expect(config.buy_conditions.use_volume_spike).toBe(true);
    });

    it("should map single stock default symbol when no index/sector/multi-symbol", () => {
      // Arrange
      const stockPreset: StrategyPresetItem = {
        ...basePreset,
        id: "dnse-02",
        category: "Động lượng Cá nhân",
        default_symbol: "VCI",
      };

      // Act
      const config = mapPresetToStrategyConfig(stockPreset);

      // Assert
      expect(config.scope_type).toBe("stock");
      expect(config.symbol).toBe("VCI");
      expect(config.buy_conditions.use_rsi).toBe(true);
      expect(config.buy_conditions.rsi_threshold).toBe(70);
    });

    it("should configure buy conditions for dnse-04 (Giá trị tăng trưởng ROE/EPS)", () => {
      // Arrange
      const preset: StrategyPresetItem = {
        ...basePreset,
        id: "dnse-04",
        category: "Cổ phiếu Cơ bản",
      };

      // Act
      const config = mapPresetToStrategyConfig(preset);

      // Assert
      expect(config.buy_conditions.use_stock_price).toBe(true);
      expect(config.buy_conditions.min_market_cap).toBe(2000);
      expect(config.buy_conditions.min_roe).toBe(5.0);
      expect(config.buy_conditions.growth_eps).toBe(true);
    });

    it("should configure buy conditions for dnse-05 (Định giá rẻ PB)", () => {
      // Arrange
      const preset: StrategyPresetItem = {
        ...basePreset,
        id: "dnse-05",
        category: "Định giá Rẻ",
      };

      // Act
      const config = mapPresetToStrategyConfig(preset);

      // Assert
      expect(config.buy_conditions.use_pb).toBe(true);
      expect(config.buy_conditions.max_pb).toBe(1.0);
      expect(config.buy_conditions.min_avg_trading_val).toBe(10);
    });

    it("should configure buy conditions for dnse-07 (ADX & Bollinger Bands)", () => {
      // Arrange
      const preset: StrategyPresetItem = {
        ...basePreset,
        id: "dnse-07",
        category: "Biến động Bollinger",
      };

      // Act
      const config = mapPresetToStrategyConfig(preset);

      // Assert
      expect(config.buy_conditions.use_adx).toBe(true);
      expect(config.buy_conditions.use_bb).toBe(true);
    });

    it("should configure buy conditions for dnse-08 (Giao cắt RSI)", () => {
      // Arrange
      const preset: StrategyPresetItem = {
        ...basePreset,
        id: "dnse-08",
        category: "Tín hiệu RSI",
      };

      // Act
      const config = mapPresetToStrategyConfig(preset);

      // Assert
      expect(config.buy_conditions.use_price_cross).toBe(true);
      expect(config.buy_conditions.use_rsi).toBe(true);
      expect(config.buy_conditions.rsi_threshold).toBe(57);
    });
  });
});
