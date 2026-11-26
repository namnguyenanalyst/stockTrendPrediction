"use client";

import React, { useEffect } from "react";
import {
  BarChart3,
  BrainCircuit,
  History,
  ShieldCheck,
  TrendingUp,
  PanelLeftClose,
  PanelLeftOpen,
  X,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";

export type DashboardTab = "market" | "prediction" | "backtest" | "admin-stats";

export interface SidebarProps {
  activeTab: DashboardTab;
  setActiveTab: (tab: DashboardTab) => void;
  isCollapsed: boolean;
  setIsCollapsed: (collapsed: boolean | ((prev: boolean) => boolean)) => void;
  isMobileOpen?: boolean;
  onCloseMobile?: () => void;
}

const BASE_NAV_ITEMS = [
  {
    id: "market" as const,
    label: "Thị trường & bảng điện",
    shortLabel: "Bảng giá",
    icon: BarChart3,
  },
  {
    id: "prediction" as const,
    label: "Dự báo xu hướng",
    shortLabel: "Dự báo",
    icon: BrainCircuit,
  },
  {
    id: "backtest" as const,
    label: "Kiểm thử chiến lược",
    shortLabel: "Kiểm thử",
    icon: History,
  },
];

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  isCollapsed,
  setIsCollapsed,
  isMobileOpen = false,
  onCloseMobile,
}) => {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  const navItems = [
    ...BASE_NAV_ITEMS,
    ...(isAdmin
      ? [
        {
          id: "admin-stats" as const,
          label: "Phòng kiểm soát của QTV",
          shortLabel: "Thống kê",
          description: "Theo dõi hệ thống",
          icon: ShieldCheck,
        },
      ]
      : []),
  ];
  // Kích hoạt dispatch sự kiện resize để các biểu đồ Lightweight Charts tự động cập nhật độ rộng mượt mà
  useEffect(() => {
    window.dispatchEvent(new Event("resize"));
    const timer = setTimeout(() => {
      window.dispatchEvent(new Event("resize"));
    }, 320);
    return () => clearTimeout(timer);
  }, [isCollapsed]);

  useEffect(() => {
    if (!isMobileOpen || !onCloseMobile) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onCloseMobile();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [isMobileOpen, onCloseMobile]);

  return (
    <>
      <aside
        aria-label="Thanh điều hướng chính"
        className={`sticky top-0 h-screen hidden md:flex flex-col border-r border-slate-800 bg-slate-950/95 backdrop-blur-md z-40 transition-all duration-300 ease-in-out shrink-0 select-none ${isCollapsed ? "w-20" : "w-64"
          }`}
      >
        {/* 1. Phần Đầu: Branding & Nút Đóng/Mở Xổ ra vào */}
        <div
          className={`flex items-center border-b border-slate-800/80 h-[73px] transition-all duration-300 ${isCollapsed ? "justify-center px-2" : "justify-between px-4"
            }`}
        >
          {!isCollapsed ? (
            <>
              <div className="flex items-center gap-3 overflow-hidden">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 text-slate-950 shadow-md shadow-emerald-500/20">
                  <TrendingUp className="h-6 w-6 stroke-[2.5]" />
                </div>
                <div className="flex flex-col overflow-hidden transition-opacity duration-300">
                  <span className="text-base font-extrabold tracking-tight text-slate-100 whitespace-nowrap">
                    STOCK<span className="text-emerald-400">PULSE</span>
                  </span>
                </div>
              </div>

              <button
                onClick={() => setIsCollapsed(true)}
                title="Thu gọn thanh điều hướng"
                aria-label="Thu gọn thanh điều hướng"
                className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-800 bg-slate-900/80 text-slate-400 hover:border-slate-700 hover:bg-slate-800 hover:text-slate-100 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
              >
                <PanelLeftClose className="h-4 w-4" />
              </button>
            </>
          ) : (
            <button
              onClick={() => setIsCollapsed(false)}
              title="Mở rộng thanh điều hướng"
              aria-label="Mở rộng thanh điều hướng"
              className="flex h-10 w-10 items-center justify-center rounded-lg border border-slate-800 bg-slate-900/80 text-slate-300 hover:border-emerald-500/50 hover:bg-slate-800 hover:text-emerald-400 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
            >
              <PanelLeftOpen className="h-5 w-5 text-emerald-400" />
            </button>
          )}
        </div>

        {/* 2. Danh sách Menu Tabs (Dạng Cột Dọc) */}
        <div className="flex-1 px-3 py-4 overflow-y-auto">
          <nav className="flex flex-col space-y-1.5" role="tablist">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;

              return (
                <button
                  key={item.id}
                  role="tab"
                  aria-selected={isActive}
                  onClick={() => setActiveTab(item.id)}
                  title={isCollapsed ? item.label : undefined}
                  className={`group relative flex items-center gap-3 rounded-xl px-3 py-3 text-left transition-all ${isActive
                    ? "bg-emerald-500/10 text-emerald-400 font-semibold shadow-sm shadow-emerald-500/5 border border-emerald-500/30"
                    : "text-slate-400 hover:bg-slate-900 hover:text-slate-200 border border-transparent"
                    } ${isCollapsed ? "justify-center px-0" : ""}`}
                >
                  <Icon
                    className={`h-5 w-5 shrink-0 transition-transform group-hover:scale-110 ${isActive ? "text-emerald-400" : "text-slate-400 group-hover:text-slate-200"
                      }`}
                  />

                  {!isCollapsed && (
                    <div className="flex flex-col overflow-hidden">
                      <span className="text-xs font-medium leading-tight truncate">
                        {item.label}
                      </span>
                    </div>
                  )}

                  {/* Vạch chỉ báo kích hoạt (Active Indicator) */}
                  {isActive && (
                    <span className="absolute left-0 top-1/2 -translate-y-1/2 h-6 w-1 rounded-r-full bg-emerald-400" />
                  )}
                </button>
              );
            })}
          </nav>
        </div>
      </aside>

      {isMobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div
            className="fixed inset-0 bg-slate-950/75 backdrop-blur-sm"
            onClick={onCloseMobile}
            aria-hidden="true"
          />
          <aside
            role="dialog"
            aria-modal="true"
            aria-label="Menu điều hướng"
            className="fixed inset-y-0 left-0 z-50 flex w-[min(16rem,calc(100vw-3rem))] max-w-[85vw] flex-col border-r border-slate-800 bg-slate-950 shadow-2xl select-none"
          >
            <div className="flex items-center justify-between border-b border-slate-800/80 h-[73px] px-4">
              <div className="flex items-center gap-3 overflow-hidden">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 text-slate-950 shadow-md shadow-emerald-500/20">
                  <TrendingUp className="h-6 w-6 stroke-[2.5]" />
                </div>
                <span className="text-base font-extrabold tracking-tight text-slate-100 whitespace-nowrap">
                  STOCK<span className="text-emerald-400">PULSE</span>
                </span>
              </div>
              <button
                type="button"
                onClick={onCloseMobile}
                aria-label="Đóng menu điều hướng"
                className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-800 bg-slate-900/80 text-slate-400 hover:border-slate-700 hover:bg-slate-800 hover:text-slate-100 transition-all"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="flex-1 px-3 py-4 overflow-y-auto">
              <nav className="flex flex-col space-y-1.5" role="tablist">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = activeTab === item.id;
                  return (
                    <button
                      key={item.id}
                      type="button"
                      role="tab"
                      aria-selected={isActive}
                      onClick={() => {
                        setActiveTab(item.id);
                        onCloseMobile?.();
                      }}
                      className={`group relative flex items-center gap-3 rounded-xl px-3 py-3 text-left transition-all ${isActive
                          ? "bg-emerald-500/10 text-emerald-400 font-semibold shadow-sm shadow-emerald-500/5 border border-emerald-500/30"
                          : "text-slate-400 hover:bg-slate-900 hover:text-slate-200 border border-transparent"
                        }`}
                    >
                      <Icon
                        className={`h-5 w-5 shrink-0 ${isActive ? "text-emerald-400" : "text-slate-400 group-hover:text-slate-200"
                          }`}
                      />
                      <span className="text-xs font-medium leading-tight truncate">
                        {item.label}
                      </span>
                      {isActive && (
                        <span className="absolute left-0 top-1/2 -translate-y-1/2 h-6 w-1 rounded-r-full bg-emerald-400" />
                      )}
                    </button>
                  );
                })}
              </nav>
            </div>
          </aside>
        </div>
      )}
    </>
  );
};
