// @vitest-environment jsdom
import React from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";

const authState = vi.hoisted(() => ({
  user: null as { id: string; role: string } | null,
  isLoading: true,
}));

const apiMocks = vi.hoisted(() => ({
  getBatchPrediction: vi.fn(),
  getMarketBoard: vi.fn(),
  getPredictionSignal: vi.fn(),
  getStockHistory: vi.fn(),
  getStockIndicators: vi.fn(),
  getStockSummary: vi.fn(),
  runBacktestSimulation: vi.fn(),
  getAdminStats: vi.fn(),
  getAdminUsers: vi.fn(),
  getAdminActivityLogs: vi.fn(),
}));

vi.mock("@/lib/api", () => apiMocks);
vi.mock("@/context/AuthContext", () => ({
  useAuth: () => authState,
}));
vi.mock("@/components/Sidebar", () => ({ Sidebar: () => null }));
vi.mock("@/components/TopHeader", () => ({ TopHeader: () => null }));
vi.mock("@/components/tabs/MarketOverviewTab", () => ({ MarketOverviewTab: () => <div>market</div> }));
vi.mock("@/components/tabs/BacktestSimulatorTab", () => ({ BacktestSimulatorTab: () => null }));
vi.mock("@/components/tabs/AIPredictionTab", () => ({ AIPredictionTab: () => null }));
vi.mock("@/components/tabs/SystemStatsTab", () => ({
  SystemStatsTab: () => {
    apiMocks.getAdminStats();
    apiMocks.getAdminUsers();
    apiMocks.getAdminActivityLogs();
    return <div>admin-panel</div>;
  },
}));

import { DashboardApp } from "./DashboardApp";

beforeEach(() => {
  vi.clearAllMocks();
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: () => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }),
  });
  apiMocks.getBatchPrediction.mockResolvedValue({ predictions: [] });
  apiMocks.getMarketBoard.mockResolvedValue({});
  apiMocks.getStockHistory.mockResolvedValue({ bars: [] });
  apiMocks.getStockIndicators.mockResolvedValue({ indicators: [] });
  apiMocks.getStockSummary.mockResolvedValue({});
  apiMocks.getPredictionSignal.mockResolvedValue({ symbol: "VIC" });
});

afterEach(cleanup);

describe("DashboardApp Admin Guard", () => {
  it("does not render admin panel or call /api/v1/admin/* while auth is loading", () => {
    authState.isLoading = true;
    authState.user = null;

    render(<DashboardApp initialTab="admin-stats" />);

    expect(screen.queryByText("admin-panel")).toBeNull();
    expect(screen.getByText("Đang xác thực quyền quản trị viên...")).toBeTruthy();
    expect(apiMocks.getAdminStats).not.toHaveBeenCalled();
    expect(apiMocks.getAdminUsers).not.toHaveBeenCalled();
    expect(apiMocks.getAdminActivityLogs).not.toHaveBeenCalled();
  });

  it("does not render admin panel or call /api/v1/admin/* for non-admin trader", () => {
    authState.isLoading = false;
    authState.user = { id: "u1", role: "trader" };

    render(<DashboardApp initialTab="admin-stats" />);

    expect(screen.queryByText("admin-panel")).toBeNull();
    expect(apiMocks.getAdminStats).not.toHaveBeenCalled();
    expect(apiMocks.getAdminUsers).not.toHaveBeenCalled();
    expect(apiMocks.getAdminActivityLogs).not.toHaveBeenCalled();
  });
});
