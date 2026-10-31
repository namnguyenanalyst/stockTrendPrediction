import React from "react";
import Link from "next/link";
import { Terminal, TrendingUp } from "lucide-react";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="relative min-h-screen flex flex-col justify-between bg-slate-950 text-slate-100 overflow-hidden">
      {/* Hiệu ứng nền Gradient Ambient */}
      <div className="pointer-events-none absolute -top-40 left-1/2 -translate-x-1/2 h-[500px] w-[800px] rounded-full bg-gradient-to-tr from-emerald-600/15 via-teal-500/10 to-indigo-600/15 blur-3xl opacity-70" />
      <div className="pointer-events-none absolute -bottom-40 right-10 h-[400px] w-[600px] rounded-full bg-gradient-to-tl from-emerald-500/10 to-sky-600/10 blur-3xl opacity-50" />

      {/* Header thương hiệu tối giản */}
      <header className="relative z-10 mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 flex items-center justify-between">
        <Link
          href="/"
          className="flex items-center gap-3 transition-opacity hover:opacity-90"
        >
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 text-slate-950 shadow-md shadow-emerald-500/20">
            <TrendingUp className="h-6 w-6 stroke-[2.5]" />
          </div>
          <div className="flex flex-col">
            <span className="text-lg font-black tracking-tight text-slate-100">
              STOCK<span className="text-emerald-400">PULSE</span>
            </span>
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
              Định Lượng &amp; Dự Báo Xu Hướng VN
            </span>
          </div>
        </Link>

        <div className="hidden sm:flex items-center gap-2 rounded-full border border-slate-800 bg-slate-900/60 px-3 py-1 text-xs text-slate-400 backdrop-blur-md">
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>Hệ Thống Đa Người Dùng Chuẩn Production</span>
        </div>
      </header>

      {/* Vùng Form Trung tâm */}
      <main className="relative z-10 flex-1 flex items-center justify-center px-4 py-8 sm:px-6">
        <div className="w-full max-w-md">{children}</div>
      </main>

      {/* Chân trang bản quyền */}
      <footer className="relative z-10 border-t border-slate-800/80 bg-slate-950/80 py-4 text-xs text-slate-500 backdrop-blur-sm">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-2 px-4 sm:flex-row sm:px-6">
          <div className="flex items-center gap-2">
            <Terminal className="h-3.5 w-3.5 text-emerald-500" />
            <span>
              ĐATN: <strong>Dự báo Xu hướng &amp; Đánh giá Chiến lược Đầu tư</strong>
            </span>
          </div>
          <div className="text-[11px] text-slate-500">
            Trường Đại học Mỏ - Địa chất &bull; Tin học Kinh tế
          </div>
        </div>
      </footer>
    </div>
  );
}
