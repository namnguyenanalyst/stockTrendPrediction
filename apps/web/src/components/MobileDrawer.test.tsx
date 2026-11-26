// @vitest-environment jsdom
import React, { useState } from "react";
import { afterEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";

vi.mock("@/context/AuthContext", () => ({ useAuth: () => ({ user: null }) }));
vi.mock("@/lib/api", () => ({ getStockSymbols: async () => [] }));
vi.mock("@/components/auth/UserMenu", () => ({ UserMenu: () => <div>UserMenu</div> }));

import { DashboardTab, Sidebar } from "./Sidebar";
import { TopHeader } from "./TopHeader";

afterEach(cleanup);

function DrawerHarness() {
  const [activeTab, setActiveTab] = useState<DashboardTab>("prediction");
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  return (
    <div>
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isCollapsed={false}
        setIsCollapsed={() => {}}
        isMobileOpen={isMobileMenuOpen}
        onCloseMobile={() => setIsMobileMenuOpen(false)}
      />
      <TopHeader
        activeTab={activeTab}
        selectedSymbol="VIC"
        setSelectedSymbol={() => {}}
        isMobileMenuOpen={isMobileMenuOpen}
        onOpenMobileMenu={() => setIsMobileMenuOpen(true)}
      />
      <output data-testid="active-tab">{activeTab}</output>
    </div>
  );
}

it("opens mobile drawer, switches tab on selection, and closes on Escape", () => {
  render(<DrawerHarness />);
  expect(screen.queryByRole("dialog", { name: "Menu điều hướng" })).toBeNull();

  fireEvent.click(screen.getByRole("button", { name: "Mở menu điều hướng" }));
  const dialog = screen.getByRole("dialog", { name: "Menu điều hướng" });
  expect(dialog).toBeTruthy();

  fireEvent.click(screen.getAllByRole("tab", { name: /Kiểm thử chiến lược/ })[1]);
  expect(screen.getByTestId("active-tab").textContent).toBe("backtest");
  expect(screen.queryByRole("dialog", { name: "Menu điều hướng" })).toBeNull();

  fireEvent.click(screen.getByRole("button", { name: "Mở menu điều hướng" }));
  expect(screen.getByRole("dialog", { name: "Menu điều hướng" })).toBeTruthy();
  fireEvent.keyDown(window, { key: "Escape" });
  expect(screen.queryByRole("dialog", { name: "Menu điều hướng" })).toBeNull();
});
