"use client";

import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  ChevronDown,
  LogIn,
  LogOut,
  Shield,
  ShieldAlert,
  ShieldCheck,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";

const RISK_LABELS: Record<
  string,
  { label: string; bg: string; text: string; icon: React.ComponentType<{ className?: string }> }
> = {
  conservative: {
    label: "Thận trọng",
    bg: "bg-sky-500/15 border-sky-500/30",
    text: "text-sky-300",
    icon: ShieldCheck,
  },
  balanced: {
    label: "Cân bằng",
    bg: "bg-emerald-500/15 border-emerald-500/30",
    text: "text-emerald-300",
    icon: Shield,
  },
  aggressive: {
    label: "Tăng trưởng",
    bg: "bg-amber-500/15 border-amber-500/30",
    text: "text-amber-300",
    icon: ShieldAlert,
  },
};

export const UserMenu: React.FC = () => {
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Đóng dropdown khi click ra ngoài
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  if (isLoading) {
    return (
      <div className="flex h-8 w-24 animate-pulse items-center rounded-lg bg-slate-900 border border-slate-800" />
    );
  }

  if (!isAuthenticated || !user) {
    return (
      <div className="flex items-center gap-2">
        <Link
          href="/login"
          className="flex items-center gap-1.5 rounded-lg border border-slate-800 bg-slate-900/80 px-3 py-1.5 text-xs font-semibold text-slate-300 hover:border-slate-700 hover:bg-slate-800 hover:text-white transition-all"
        >
          <LogIn className="h-3.5 w-3.5 text-slate-400" />
          <span>Đăng nhập</span>
        </Link>
        <Link
          href="/register"
          className="hidden sm:inline-flex items-center rounded-lg bg-gradient-to-r from-emerald-500 to-teal-500 px-3 py-1.5 text-xs font-bold text-slate-950 shadow-sm shadow-emerald-500/20 hover:opacity-95 transition-all"
        >
          Đăng ký
        </Link>
      </div>
    );
  }

  const riskInfo = RISK_LABELS[user.risk_profile] || {
    label: user.risk_profile || "Cân bằng",
    bg: "bg-emerald-500/15 border-emerald-500/30",
    text: "text-emerald-300",
    icon: Shield,
  };
  const RiskIcon = riskInfo.icon;
  const displayName = user.full_name || user.email.split("@")[0];
  const initial = displayName.charAt(0).toUpperCase();

  return (
    <div ref={menuRef} className="relative">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900/90 px-2.5 py-1 text-left text-xs text-slate-200 hover:border-slate-700 hover:bg-slate-850 focus:outline-none transition-all"
      >
        {/* Avatar tròn với chữ cái đầu */}
        <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-emerald-500/20 font-bold text-emerald-400 border border-emerald-500/30 text-[11px]">
          {initial}
        </div>

        <div className="hidden sm:flex flex-col text-left">
          <div className="flex items-center gap-1.5">
            <span className="font-semibold text-slate-100 max-w-[110px] truncate leading-tight">
              {displayName}
            </span>
            <span
              className={`rounded border px-1 py-0.2 text-[9px] font-semibold uppercase tracking-wider ${
                user.role === "admin"
                  ? "bg-purple-500/20 border-purple-500/40 text-purple-300"
                  : "bg-slate-800 border-slate-700 text-slate-400"
              }`}
            >
              {user.role}
            </span>
          </div>
          <span className="text-[10px] text-slate-400 truncate max-w-[110px]">
            {user.email}
          </span>
        </div>

        {/* Badge khẩu vị rủi ro */}
        <span
          className={`hidden md:inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-[10px] font-medium ${riskInfo.bg} ${riskInfo.text}`}
        >
          <RiskIcon className="h-3 w-3" />
          <span>{riskInfo.label}</span>
        </span>

        <ChevronDown className="h-3 w-3 text-slate-400 shrink-0" />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-1.5 w-60 rounded-xl border border-slate-800 bg-slate-950 p-2 shadow-2xl backdrop-blur-xl z-50 animate-in fade-in zoom-in-95 duration-100">
          <div className="border-b border-slate-800/80 px-2 py-2 mb-1.5">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/20 text-emerald-400 font-bold text-sm">
                {initial}
              </div>
              <div className="flex flex-col min-w-0">
                <span className="text-xs font-bold text-slate-100 truncate">
                  {user.full_name || "Nhà đầu tư"}
                </span>
                <span className="text-[11px] text-slate-400 truncate">
                  {user.email}
                </span>
              </div>
            </div>

            <div className="mt-2.5 flex flex-wrap items-center gap-1.5">
              <span
                className={`rounded border px-1.5 py-0.5 text-[10px] font-semibold ${
                  user.role === "admin"
                    ? "bg-purple-500/20 border-purple-500/40 text-purple-300"
                    : "bg-slate-800 border-slate-700 text-slate-300"
                }`}
              >
                Vai trò: {user.role === "admin" ? "Quản trị viên" : "Trader"}
              </span>
              <span
                className={`flex items-center gap-1 rounded border px-1.5 py-0.5 text-[10px] font-medium ${riskInfo.bg} ${riskInfo.text}`}
              >
                <RiskIcon className="h-2.5 w-2.5" />
                <span>{riskInfo.label}</span>
              </span>
            </div>
          </div>

          <button
            type="button"
            onClick={async () => {
              setIsOpen(false);
              await logout();
            }}
            className="flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-xs font-medium text-rose-400 hover:bg-rose-500/10 hover:text-rose-300 transition-colors"
          >
            <LogOut className="h-3.5 w-3.5" />
            <span>Đăng xuất tài khoản</span>
          </button>
        </div>
      )}
    </div>
  );
};
