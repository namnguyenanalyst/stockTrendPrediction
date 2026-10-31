"use client";

import React, { Suspense, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  Lock,
  Mail,
  Shield,
  ShieldAlert,
  ShieldCheck,
  User as UserIcon,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { RiskProfile } from "@/lib/types";

const RISK_PROFILES: {
  id: RiskProfile;
  label: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
}[] = [
  {
    id: "conservative",
    label: "Thận trọng",
    description: "Ưu tiên bảo toàn vốn, quản trị rủi ro chặt chẽ",
    icon: ShieldCheck,
  },
  {
    id: "balanced",
    label: "Cân bằng",
    description: "Cân đối giữa tăng trưởng lợi nhuận và kiểm soát sụt giảm",
    icon: Shield,
  },
  {
    id: "aggressive",
    label: "Tăng trưởng",
    description: "Chấp nhận biến động cao để tối đa hóa tỷ suất sinh lời",
    icon: ShieldAlert,
  },
];

function RegisterForm() {
  const router = useRouter();
  const { register } = useAuth();

  const [email, setEmail] = useState<string>("");
  const [fullName, setFullName] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [confirmPassword, setConfirmPassword] = useState<string>("");
  const [riskProfile, setRiskProfile] = useState<RiskProfile>("balanced");

  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSuccess, setIsSuccess] = useState<boolean>(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setErrorMessage(null);

    const cleanEmail = email.trim().toLowerCase();
    if (!cleanEmail) {
      setErrorMessage("Vui lòng nhập địa chỉ email.");
      return;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(cleanEmail)) {
      setErrorMessage("Địa chỉ email không đúng định dạng chuẩn.");
      return;
    }
    if (password.length < 8) {
      setErrorMessage("Mật khẩu phải chứa tối thiểu 8 ký tự.");
      return;
    }
    if (password !== confirmPassword) {
      setErrorMessage("Mật khẩu xác nhận không khớp.");
      return;
    }

    setIsSubmitting(true);
    try {
      await register(cleanEmail, password, fullName.trim() || null, riskProfile);
      setIsSuccess(true);
      setTimeout(() => {
        router.push("/dashboard");
      }, 400);
    } catch (err: unknown) {
      setErrorMessage(
        err instanceof Error
          ? err.message
          : "Đăng ký thất bại. Vui lòng kiểm tra lại thông tin."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-6 sm:p-8 shadow-2xl backdrop-blur-xl">
      <div className="mb-6 text-center">
        <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-100">
          Đăng ký tài khoản
        </h2>
        <p className="mt-1 text-xs sm:text-sm text-slate-400">
          Khởi tạo tài khoản phân tích &amp; cá nhân hóa danh mục đầu tư
        </p>
      </div>

      {errorMessage && (
        <div
          role="alert"
          className="mb-4 flex items-center gap-2.5 rounded-xl border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-300 animate-in fade-in"
        >
          <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
          <span>{errorMessage}</span>
        </div>
      )}

      {isSuccess && (
        <div
          role="status"
          className="mb-4 flex items-center gap-2.5 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-emerald-300"
        >
          <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />
          <span>Đăng ký thành công! Đang chuyển hướng vào Dashboard...</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Họ và tên */}
        <div>
          <label
            htmlFor="fullName"
            className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5"
          >
            Họ và tên
          </label>
          <div className="relative">
            <UserIcon className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
            <input
              id="fullName"
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Nguyễn Văn A"
              className="w-full rounded-xl border border-slate-800 bg-slate-950/70 py-2.5 pl-10 pr-4 text-sm text-slate-100 placeholder:text-slate-600 focus:border-emerald-500 focus:bg-slate-950 focus:outline-none focus:ring-1 focus:ring-emerald-500 transition-all"
            />
          </div>
        </div>

        {/* Email */}
        <div>
          <label
            htmlFor="reg-email"
            className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5"
          >
            Địa chỉ Email <span className="text-rose-400">*</span>
          </label>
          <div className="relative">
            <Mail className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
            <input
              id="reg-email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="trader@quantinvest.vn"
              className="w-full rounded-xl border border-slate-800 bg-slate-950/70 py-2.5 pl-10 pr-4 text-sm text-slate-100 placeholder:text-slate-600 focus:border-emerald-500 focus:bg-slate-950 focus:outline-none focus:ring-1 focus:ring-emerald-500 transition-all"
            />
          </div>
        </div>

        {/* Mật khẩu */}
        <div>
          <label
            htmlFor="reg-password"
            className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5"
          >
            Mật khẩu (tối thiểu 8 ký tự) <span className="text-rose-400">*</span>
          </label>
          <div className="relative">
            <Lock className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
            <input
              id="reg-password"
              type="password"
              required
              minLength={8}
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full rounded-xl border border-slate-800 bg-slate-950/70 py-2.5 pl-10 pr-4 text-sm text-slate-100 placeholder:text-slate-600 focus:border-emerald-500 focus:bg-slate-950 focus:outline-none focus:ring-1 focus:ring-emerald-500 transition-all"
            />
          </div>
        </div>

        {/* Xác nhận mật khẩu */}
        <div>
          <label
            htmlFor="reg-confirm-password"
            className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5"
          >
            Xác nhận mật khẩu <span className="text-rose-400">*</span>
          </label>
          <div className="relative">
            <Lock className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
            <input
              id="reg-confirm-password"
              type="password"
              required
              minLength={8}
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full rounded-xl border border-slate-800 bg-slate-950/70 py-2.5 pl-10 pr-4 text-sm text-slate-100 placeholder:text-slate-600 focus:border-emerald-500 focus:bg-slate-950 focus:outline-none focus:ring-1 focus:ring-emerald-500 transition-all"
            />
          </div>
        </div>

        {/* Khẩu vị rủi ro (Risk Profile) */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
            Khẩu vị rủi ro đầu tư
          </label>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
            {RISK_PROFILES.map((item) => {
              const Icon = item.icon;
              const isSelected = riskProfile === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setRiskProfile(item.id)}
                  className={`flex flex-col items-center p-2.5 rounded-xl border text-center transition-all ${
                    isSelected
                      ? "border-emerald-500 bg-emerald-500/15 text-emerald-300 shadow-sm shadow-emerald-500/20"
                      : "border-slate-800 bg-slate-950/60 text-slate-400 hover:border-slate-700 hover:text-slate-200"
                  }`}
                >
                  <Icon className="h-5 w-5 mb-1 text-emerald-400" />
                  <span className="text-xs font-bold">{item.label}</span>
                  <span className="text-[10px] leading-tight text-slate-500 mt-0.5 line-clamp-2">
                    {item.description}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Nút Submit */}
        <button
          type="submit"
          disabled={isSubmitting || isSuccess}
          className="group relative flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 py-3 text-sm font-bold text-slate-950 shadow-lg shadow-emerald-500/20 transition-all hover:opacity-95 hover:shadow-emerald-500/30 disabled:opacity-50 disabled:cursor-not-allowed mt-2"
        >
          <span>{isSubmitting ? "Đang xử lý đăng ký..." : "Hoàn tất đăng ký"}</span>
          <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
        </button>
      </form>

      {/* Điều hướng Đăng nhập */}
      <div className="mt-6 border-t border-slate-800/80 pt-4 text-center text-xs text-slate-400">
        <span>Đã có tài khoản? </span>
        <Link
          href="/login"
          className="font-semibold text-emerald-400 hover:text-emerald-300 hover:underline transition-colors"
        >
          Đăng nhập ngay
        </Link>
      </div>
    </div>
  );
}

export default function RegisterPage() {
  return (
    <Suspense
      fallback={
        <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-8 text-center text-slate-400">
          Đang nạp màn hình đăng ký...
        </div>
      }
    >
      <RegisterForm />
    </Suspense>
  );
}
