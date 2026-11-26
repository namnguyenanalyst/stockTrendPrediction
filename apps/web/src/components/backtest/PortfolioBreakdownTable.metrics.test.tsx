// @vitest-environment jsdom
import React from "react";
import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { PortfolioBreakdownTable } from "./PortfolioBreakdownTable";
import type { SymbolBreakdownItem } from "@/lib/types";
afterEach(cleanup);

it("renders undefined metrics without crashing or fabricating zeros", () => {
  const item: SymbolBreakdownItem = {
    symbol: "VIC", name: "Fixture", sector: "Fixture", roi_pct: 0, bh_roi_pct: 0,
    excess_pct: 0, sharpe: null, sortino: null, mdd_pct: 0, win_rate_pct: null,
    profit_factor: null, trades: 0, costs: 0,
  };
  render(<PortfolioBreakdownTable items={[item]} onSelectSymbol={() => {}} />);
  expect(screen.getAllByText("—")).toHaveLength(2);
  expect(screen.getByText("VIC")).toBeTruthy();
});
