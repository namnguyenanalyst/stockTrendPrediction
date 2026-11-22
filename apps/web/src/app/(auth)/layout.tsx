import React from "react";
import Link from "next/link";
import { TrendingUp } from "lucide-react";

export const metadata = { referrer: "no-referrer" as const, robots: { index: false, follow: false } };

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
          </div>
        </Link>
      </header>

      {/* Vùng Form Trung tâm */}
      <main className="relative z-10 flex-1 flex items-center justify-center px-4 py-8 sm:px-6">
        <div className="w-full max-w-md">{children}</div>
      </main>
    </div>
  );
}
