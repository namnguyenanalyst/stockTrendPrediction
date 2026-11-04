"use client";

import React, { useEffect, useState } from "react";
import {
  Activity,
  AlertCircle,
  Clock,
  RefreshCw,
  ShieldCheck,
  UserCheck,
  UserPlus,
  Users,
} from "lucide-react";
import { getAdminStats } from "@/lib/api";
import { AdminStatsResponse } from "@/lib/types";

export const SystemStatsTab: React.FC = () => {
  const [stats, setStats] = useState<AdminStatsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefreshedAt, setLastRefreshedAt] = useState<string>("");

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getAdminStats();
      setStats(data);
      setLastRefreshedAt(new Date().toLocaleTimeString("vi-VN"));
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Không thể tải số liệu thống kê hệ thống.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  return (
    <div className="space-y-6">
      {/* 1. Header & Tiêu đề Tab */}
      <div className="flex flex-col gap-3 rounded-2xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg backdrop-blur-sm sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-slate-100 sm:text-xl">
                Bảng Điều khiển Giám sát Định danh &amp; Thống kê Hệ thống
              </h1>
              <p className="text-xs text-slate-400 mt-0.5">
                Nguyên tắc Đặc quyền Tối thiểu (PoLP): Chỉ tổng hợp dữ liệu vĩ mô, tuyệt đối không hiển thị thông tin hay chiến lược của người dùng khác.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {lastRefreshedAt && (
            <span className="flex items-center gap-1.5 text-xs text-slate-400">
              <Clock className="h-3.5 w-3.5 text-slate-500" />
              Cập nhật lúc: <strong className="text-slate-300">{lastRefreshedAt}</strong>
            </span>
          )}
          <button
            onClick={fetchStats}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-xl bg-slate-800 px-3.5 py-2 text-xs font-semibold text-slate-200 transition-all hover:bg-slate-700 hover:text-white disabled:opacity-50 border border-slate-700/60 focus:outline-none focus:ring-2 focus:ring-emerald-500/40"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin text-emerald-400" : ""}`} />
            <span>{loading ? "Đang cập nhật..." : "Làm mới"}</span>
          </button>
        </div>
      </div>

      {/* 2. Thông báo Lỗi nếu có */}
      {error && (
        <div className="flex items-center gap-3 rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-xs text-rose-300">
          <AlertCircle className="h-5 w-5 shrink-0 text-rose-400" />
          <div className="flex-1">
            <strong className="font-semibold">Lỗi truy vấn thống kê: </strong>
            <span>{error}</span>
          </div>
          <button
            onClick={fetchStats}
            className="rounded-lg bg-rose-500/20 px-3 py-1 font-semibold text-rose-200 hover:bg-rose-500/30"
          >
            Thử lại
          </button>
        </div>
      )}

      {/* 3. Lưới 4 Thẻ Chỉ số Tổng hợp (Summary KPI Cards) */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Card 1: Tổng số người dùng */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5 shadow-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Tổng tài khoản</span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/10 text-blue-400">
              <Users className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3">
            <div className="text-3xl font-extrabold tracking-tight text-slate-100">
              {loading && !stats ? "—" : stats?.total_users.toLocaleString("vi-VN")}
            </div>
            <p className="mt-1 text-[11px] text-slate-500">
              Tất cả tài khoản trong cơ sở dữ liệu
            </p>
          </div>
        </div>

        {/* Card 2: Người dùng đăng ký mới hôm nay */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5 shadow-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Đăng ký mới hôm nay</span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-400">
              <UserPlus className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3">
            <div className="text-3xl font-extrabold tracking-tight text-emerald-400">
              {loading && !stats ? "—" : stats?.new_users_today.toLocaleString("vi-VN")}
            </div>
            <div className="mt-2 flex items-center gap-2 text-[10px] text-slate-400">
              <span className="rounded bg-slate-800 px-1.5 py-0.5">
                7 ngày: <strong className="text-slate-200">{stats?.new_users_7d ?? 0}</strong>
              </span>
              <span className="rounded bg-slate-800 px-1.5 py-0.5">
                30 ngày: <strong className="text-slate-200">{stats?.new_users_30d ?? 0}</strong>
              </span>
            </div>
          </div>
        </div>

        {/* Card 3: Người dùng đang trực tuyến (Online) */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5 shadow-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Đang trực tuyến (Online)</span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/10 text-amber-400">
              <Activity className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3">
            <div className="flex items-baseline gap-2">
              <div className="text-3xl font-extrabold tracking-tight text-amber-400">
                {loading && !stats ? "—" : stats?.online_users.toLocaleString("vi-VN")}
              </div>
              <span className="flex items-center gap-1 text-[11px] text-emerald-400">
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                Live
              </span>
            </div>
            <p className="mt-1 text-[11px] text-slate-500">
              Hoạt động trong 5 phút gần nhất
            </p>
          </div>
        </div>

        {/* Card 4: Tuân thủ Bảo mật & Phân quyền IAM */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5 shadow-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Trạng thái Phân quyền</span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-teal-500/10 text-teal-400">
              <UserCheck className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3">
            <div className="text-base font-bold text-teal-300">
              PoLP Enforced
            </div>
            <p className="mt-1 text-[11px] text-slate-500 leading-relaxed">
              Dữ liệu danh mục &amp; chiến lược được cô lập 100% cấp CSDL theo user_id.
            </p>
          </div>
        </div>
      </div>

      {/* 4. Khối Giải thích Nguyên tắc Kiến trúc & Bảo mật ĐATN */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/30 p-6">
        <h2 className="text-sm font-bold text-slate-200">
          Quy chuẩn Bảo mật &amp; Kiến trúc Độc lập Định lượng
        </h2>
        <div className="mt-3 grid grid-cols-1 gap-4 text-xs text-slate-400 md:grid-cols-3">
          <div className="rounded-xl border border-slate-800/80 bg-slate-950/40 p-4">
            <strong className="block font-semibold text-slate-300 mb-1">
              1. Nguyên tắc Đặc quyền Tối thiểu (PoLP)
            </strong>
            <span>
              Quản trị viên (Admin) chỉ thực hiện các tác vụ IAM và quan sát thống kê vĩ mô. Tuyệt đối không có giao diện hoặc API cho phép xem hay thao túng danh mục đầu tư, mẫu tham số hoặc kết quả backtest của người dùng khác.
            </span>
          </div>

          <div className="rounded-xl border border-slate-800/80 bg-slate-950/40 p-4">
            <strong className="block font-semibold text-slate-300 mb-1">
              2. Chuẩn hóa Mốc thời gian UTC+7
            </strong>
            <span>
              Mốc &quot;Hôm nay&quot; được quy đổi theo 0h00 giờ Việt Nam (UTC+7, tương ứng 17:00 UTC hôm trước), đảm bảo thống kê chính xác tuyệt đối ngay cả khi tài khoản đăng ký lúc 23h30 đêm tại Việt Nam.
            </span>
          </div>

          <div className="rounded-xl border border-slate-800/80 bg-slate-950/40 p-4">
            <strong className="block font-semibold text-slate-300 mb-1">
              3. Giới hạn Tần suất CSDL (Throttle 60s)
            </strong>
            <span>
              Cột thời điểm hoạt động (last_seen_at) được cập nhật có điều kiện trực tiếp tại tầng CSDL (WHERE last_seen_at IS NULL OR last_seen_at &lt; now - 60s), loại trừ nguy cơ tắc nghẽn I/O khi lưu lượng truy cập cao.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
