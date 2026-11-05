import { describe, it, expect, vi } from "vitest";
import React from "react";
import { renderToString } from "react-dom/server";
import { IndexRibbon } from "./IndexRibbon";
import { IndexOverview, StockBoardItem } from "@/lib/types";

describe("IndexRibbon Component", () => {
  const mockIndices = [
    {
      symbol: "VNINDEX",
      name: "VN-INDEX",
      value: 1733.02,
      change: 33.4,
      change_pct: 1.97,
      volume_str: "947.79 Triệu CP",
      value_str: "20,290.59 Tỷ",
      advancing: 246,
      ceiling: 16,
      unchanged: 54,
      declining: 78,
      floor: 3,
      sparkline: [1700, 1720, 1733.02],
    },
    {
      symbol: "VN30",
      name: "VN30",
      value: 2006.41,
      change: -23.95,
      change_pct: -1.18,
      volume_str: "333.31 Triệu CP",
      value_str: "10,350.85 Tỷ",
      advancing: 25,
      ceiling: 3,
      unchanged: 4,
      declining: 1,
      floor: 0,
      sparkline: [2030, 2010, 2006.41],
    },
    {
      symbol: "HNX",
      name: "HNX-INDEX",
      value: 247.48,
      change: 4.77,
      change_pct: 1.97,
      volume_str: "85.20 Triệu CP",
      value_str: "1,450.20 Tỷ",
      advancing: 112,
      ceiling: 8,
      unchanged: 58,
      declining: 65,
      floor: 2,
      sparkline: [242, 245, 247.48],
    },
    {
      symbol: "HNX30",
      name: "HNX30",
      value: 442.27,
      change: 8.53,
      change_pct: 1.97,
      volume_str: "61.51 Triệu CP",
      value_str: "954.83 Tỷ",
      advancing: 16,
      ceiling: 4,
      unchanged: 9,
      declining: 0,
      floor: 0,
      sparkline: [433, 438, 442.27],
    },
    {
      symbol: "UPCOM",
      name: "UPCOM-INDEX",
      value: 98.78,
      change: 1.9,
      change_pct: 1.96,
      volume_str: "45.10 Triệu CP",
      value_str: "620.50 Tỷ",
      advancing: 150,
      ceiling: 12,
      unchanged: 90,
      declining: 85,
      floor: 4,
      sparkline: [96, 97, 98.78],
    },
  ] as unknown as IndexOverview[];

  const mockStocks = [
    {
      symbol: "ACB",
      name: "Ngân hàng Á Châu",
      close: 21.0,
      change: -0.3,
      change_pct: -1.41,
      volume: 8084100,
      sector: "Ngân hàng",
      sparkline: [21.3, 21.1, 21.0],
    },
  ] as unknown as StockBoardItem[];

  it("should render 5 standard cards without wrapping grid", () => {
    const html = renderToString(
      React.createElement(IndexRibbon, {
        indices: mockIndices,
        stocks: mockStocks,
        activeSymbols: ["VNINDEX", "VN30", "HNX", "HNX30", "UPCOM"],
        isCollapsed: false,
        onToggleCollapse: vi.fn(),
        onOpenManageModal: vi.fn(),
        onSelectCard: vi.fn(),
      })
    );

    expect(html).toContain("VN-INDEX");
    expect(html).toContain("VN30");
    expect(html).toContain("HNX-INDEX");
    expect(html).toContain("HNX30");
    expect(html).toContain("UPCOM-INDEX");
    // Should NOT have the rigid wrap-breaking grid class
    expect(html).not.toContain("grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-5");
    // Should use horizontal flex scroll track
    expect(html).toContain("overflow-x-auto");
  });

  it("should render >5 cards in single horizontal swipeable track", () => {
    const html = renderToString(
      React.createElement(IndexRibbon, {
        indices: mockIndices,
        stocks: mockStocks,
        activeSymbols: ["VNINDEX", "VN30", "HNX", "HNX30", "UPCOM", "ACB"],
        isCollapsed: false,
        onToggleCollapse: vi.fn(),
        onOpenManageModal: vi.fn(),
        onSelectCard: vi.fn(),
      })
    );

    // Both all 5 indices and the 6th stock ACB must be rendered
    expect(html).toContain("VN-INDEX");
    expect(html).toContain("Ngân hàng Á Châu");
    // Must use proportional 5-card width class so 5 cards fit on screen and 6th is swipable
    expect(html).toContain("w-[calc((100%-32px)/5)]");
    expect(html).toContain("shrink-0");
    // Displays badge with count 6
    expect(html).toContain(">6<");
  });

  it("should render collapsed state with DNSE style horizontal strip", () => {
    const html = renderToString(
      React.createElement(IndexRibbon, {
        indices: mockIndices,
        stocks: mockStocks,
        activeSymbols: ["VNINDEX", "VN30", "HNX", "HNX30", "UPCOM", "ACB"],
        isCollapsed: true,
        onToggleCollapse: vi.fn(),
        onOpenManageModal: vi.fn(),
        onSelectCard: vi.fn(),
      })
    );

    expect(html).toContain("Mở");
    expect(html).toContain("ACB");
    expect(html).toContain("VNINDEX");
  });
});

