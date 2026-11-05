"use client";

import React, { useEffect, useState, useCallback } from "react";
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  Clock,
  Filter,
  Lock,
  RefreshCw,
  Search,
  Shield,
  ShieldAlert,
  ShieldCheck,
  TrendingUp,
  Unlock,
  UserCheck,
  UserPlus,
  Users,
} from "lucide-react";
import {
  getAdminActivityLogs,
  getAdminStats,
  getAdminUsers,
  updateAdminUser,
} from "@/lib/api";
import {
  AdminActivityItem,
  AdminStatsResponse,
  AdminUserItem,
} from "@/lib/types";

export const SystemStatsTab: React.FC = () => {
  // Thống kê tổng hợp (KPIs)
  const [stats, setStats] = useState<AdminStatsResponse | null>(null);
  const [statsLoading, setStatsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefreshedAt, setLastRefreshedAt] = useState<string>("");

  // Quản trị người dùng
  const [users, setUsers] = useState<AdminUserItem[]>([]);
  const [totalUsersCount, setTotalUsersCount] = useState<number>(0);
  const [usersLoading, setUsersLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [roleFilter, setRoleFilter] = useState<string>("");
  const [updatingUserId, setUpdatingUserId] = useState<string | null>(null);
  const [actionSuccessMsg, setActionSuccessMsg] = useState<string | null>(null);

  // Nhật ký hoạt động & Kiểm toán AI
  const [activities, setActivities] = useState<AdminActivityItem[]>([]);
  const [activitiesLoading, setActivitiesLoading] = useState<boolean>(true);

  // Debounce tìm kiếm để tránh giật lag khi gõ
  const [debouncedSearch, setDebouncedSearch] = useState<string>("");
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchTerm);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  // Tải thống kê
  const fetchStats = async () => {
    setStatsLoading(true);
    try {
      const data = await getAdminStats();
      setStats(data);
      setLastRefreshedAt(new Date().toLocaleTimeString("vi-VN"));
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Không thể tải số liệu thống kê.";
      setError(message);
    } finally {
      setStatsLoading(false);
    }
  };

  // Tải danh sách người dùng
  const fetchUsers = useCallback(async () => {
    setUsersLoading(true);
    try {
      const data = await getAdminUsers({
        search: debouncedSearch.trim() || undefined,
        role: roleFilter || undefined,
        page_size: 50,
      });
      setUsers(data.items);
      setTotalUsersCount(data.total);
    } catch (err: unknown) {
      console.error("Lỗi tải danh sách người dùng:", err);
    } finally {
      setUsersLoading(false);
    }
  }, [debouncedSearch, roleFilter]);

  // Tải nhật ký hoạt động
  const fetchActivities = async () => {
    setActivitiesLoading(true);
    try {
      const data = await getAdminActivityLogs(50);
      setActivities(data.items);
    } catch (err: unknown) {
      console.error("Lỗi tải nhật ký hoạt động:", err);
    } finally {
      setActivitiesLoading(false);
    }
  };

  // Tải toàn bộ dữ liệu
  const refreshAll = () => {
    setError(null);
    setActionSuccessMsg(null);
    fetchStats();
    fetchUsers();
    fetchActivities();
  };

  useEffect(() => {
    fetchStats();
    fetchActivities();
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  // Xử lý bật/tắt khóa tài khoản
  const handleToggleUserStatus = async (user: AdminUserItem) => {
    const nextStatus = !user.is_active;
    const confirmText = nextStatus
      ? `Bạn có chắc muốn MỞ KHÓA tài khoản ${user.email}?`
      : `Bạn có chắc muốn KHÓA tài khoản ${user.email}? Người dùng sẽ không thể đăng nhập.`;

    if (!window.confirm(confirmText)) return;

    setUpdatingUserId(user.id);
    setActionSuccessMsg(null);
    setError(null);
    try {
      const updated = await updateAdminUser(user.id, { is_active: nextStatus });
      setUsers((prev) =>
        prev.map((u) => (u.id === user.id ? { ...u, is_active: updated.is_active } : u))
      );
      setActionSuccessMsg(
        `Đã ${updated.is_active ? "mở khóa" : "khóa"} tài khoản ${updated.email} thành công.`
      );
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Thao tác cập nhật thất bại.";
      setError(msg);
    } finally {
      setUpdatingUserId(null);
    }
  };

  // Xử lý thay đổi vai trò (ADMIN / TRADER)
  const handleToggleUserRole = async (user: AdminUserItem) => {
    const nextRole = user.role === "admin" ? "trader" : "admin";
    const confirmText =
      nextRole === "admin"
        ? `Nâng quyền người dùng ${user.email} thành QUẢN TRỊ VIÊN (ADMIN)?`
        : `Hạ quyền người dùng ${user.email} xuống TRADER?`;

    if (!window.confirm(confirmText)) return;

    setUpdatingUserId(user.id);
    setActionSuccessMsg(null);
    setError(null);
    try {
      const updated = await updateAdminUser(user.id, { role: nextRole });
      setUsers((prev) =>
        prev.map((u) => (u.id === user.id ? { ...u, role: updated.role } : u))
      );
      setActionSuccessMsg(
        `Đã chuyển vai trò của ${updated.email} thành ${updated.role.toUpperCase()} thành công.`
      );
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Thao tác cập nhật thất bại.";
      setError(msg);
    } finally {
      setUpdatingUserId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* 1. Header & Tiêu đề Tab */}
      <div className="flex flex-col gap-3 rounded-2xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg backdrop-blur-sm sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-slate-100 sm:text-xl">
              Phòng kiểm soát của Quản trị viên
            </h1>
            <p className="text-xs text-slate-400">
              Quản trị tài khoản người dùng và giám sát lưu lượng hoạt động hệ thống
            </p>
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
            onClick={refreshAll}
            disabled={statsLoading || usersLoading || activitiesLoading}
            className="inline-flex items-center gap-2 rounded-xl bg-slate-800 px-3.5 py-2 text-xs font-semibold text-slate-200 transition-all hover:bg-slate-700 hover:text-white disabled:opacity-50 border border-slate-700/60 focus:outline-none focus:ring-2 focus:ring-emerald-500/40"
          >
            <RefreshCw
              className={`h-3.5 w-3.5 ${statsLoading || usersLoading || activitiesLoading
                  ? "animate-spin text-emerald-400"
                  : ""
                }`}
            />
            <span>
              {statsLoading || usersLoading || activitiesLoading
                ? "Đang cập nhật..."
                : "Làm mới dữ liệu"}
            </span>
          </button>
        </div>
      </div>

      {/* Thông báo Thành công hoặc Thất bại */}
      {actionSuccessMsg && (
        <div className="flex items-center gap-3 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3.5 text-xs text-emerald-300">
          <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />
          <span>{actionSuccessMsg}</span>
        </div>
      )}
      {error && (
        <div className="flex items-center gap-3 rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-xs text-rose-300">
          <AlertCircle className="h-5 w-5 shrink-0 text-rose-400" />
          <div className="flex-1">
            <strong className="font-semibold">Lỗi hệ thống: </strong>
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* 2. Lưới 3 Thẻ Chỉ số Tổng hợp (Summary KPI Cards) - Cân bằng 3 cột */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
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
              {statsLoading && !stats ? "—" : stats?.total_users.toLocaleString("vi-VN")}
            </div>
            <p className="mt-1 text-[11px] text-slate-500">Đã đăng ký trong hệ thống</p>
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
              {statsLoading && !stats ? "—" : stats?.new_users_today.toLocaleString("vi-VN")}
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
                {statsLoading && !stats ? "—" : stats?.online_users.toLocaleString("vi-VN")}
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
      </div>

      {/* 3. PHẦN 1: BẢNG QUẢN TRỊ NGƯỜI DÙNG THỰC TẾ (USER MANAGEMENT) */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5 shadow-lg">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-800 pb-4">
          <div>
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <Users className="h-4 w-4 text-emerald-400" />
              Danh sách Người dùng Hệ thống
              <span className="ml-2 rounded-full bg-slate-800 px-2 py-0.5 text-xs font-medium text-slate-400">
                {totalUsersCount} tài khoản
              </span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Tra cứu thông tin, phân quyền ADMIN/TRADER và khóa tài khoản khi cần
            </p>
          </div>

          {/* Thanh công cụ tìm kiếm và lọc */}
          <div className="flex flex-wrap items-center gap-2.5">
            <div className="relative min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-500" />
              <input
                type="text"
                placeholder="Tìm email, tên..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full rounded-xl border border-slate-700/60 bg-slate-800/80 pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:border-emerald-500/50 focus:outline-none focus:ring-1 focus:ring-emerald-500/50"
              />
            </div>

            <div className="flex items-center gap-1.5 rounded-xl border border-slate-700/60 bg-slate-800/80 px-2.5 py-1.5 text-xs text-slate-300">
              <Filter className="h-3.5 w-3.5 text-slate-500" />
              <select
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
                className="bg-transparent text-xs text-slate-200 focus:outline-none cursor-pointer"
              >
                <option value="" className="bg-slate-900 text-slate-200">
                  Tất cả vai trò
                </option>
                <option value="trader" className="bg-slate-900 text-slate-200">
                  TRADER
                </option>
                <option value="admin" className="bg-slate-900 text-slate-200">
                  ADMIN
                </option>
              </select>
            </div>
          </div>
        </div>

        {/* Bảng dữ liệu người dùng: Chiều cao vừa vặn ~5 dòng, cuộn dọc mượt mà khi danh sách dài */}
        <div className="mt-4 overflow-x-auto max-h-[310px] overflow-y-auto rounded-xl border border-slate-800/80 pr-1 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-slate-900">
          {usersLoading ? (
            <div className="flex h-32 items-center justify-center text-xs text-slate-500">
              <RefreshCw className="h-4 w-4 animate-spin mr-2 text-emerald-400" />
              Đang tải danh sách người dùng...
            </div>
          ) : users.length === 0 ? (
            <div className="flex h-32 flex-col items-center justify-center text-xs text-slate-500">
              <p>Không tìm thấy người dùng nào phù hợp với bộ lọc.</p>
            </div>
          ) : (
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="sticky top-0 z-10 border-b border-slate-800 bg-slate-950 text-[11px] font-semibold text-slate-400 uppercase tracking-wider shadow-sm">
                <tr>
                  <th className="px-4 py-3">Tài khoản / Email</th>
                  <th className="px-4 py-3">Họ tên</th>
                  <th className="px-4 py-3">Vai trò</th>
                  <th className="px-4 py-3">Lượt Backtest</th>
                  <th className="px-4 py-3">Hoạt động</th>
                  <th className="px-4 py-3 text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {users.map((u) => {
                  const isBusy = updatingUserId === u.id;
                  const formattedDate = new Date(u.created_at).toLocaleDateString("vi-VN");
                  
                  // Tính toán thời gian hoạt động thực tế (trong 5 phút qua được tính là Online)
                  const isActuallyOnline = Boolean(
                    u.last_seen_at &&
                    new Date().getTime() - new Date(u.last_seen_at).getTime() < 5 * 60 * 1000
                  );

                  const lastSeenTimeStr = u.last_seen_at
                    ? new Date(u.last_seen_at).toLocaleTimeString("vi-VN", {
                        hour: "2-digit",
                        minute: "2-digit",
                        day: "2-digit",
                        month: "2-digit",
                      })
                    : "Chưa từng online";

                  return (
                    <tr key={u.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-4 py-3">
                        <div className="font-semibold text-slate-100">{u.email}</div>
                        <div className="text-[10px] text-slate-500">Tham gia: {formattedDate}</div>
                      </td>
                      <td className="px-4 py-3 text-slate-300">
                        {u.full_name || <span className="text-slate-600 italic">Chưa đặt</span>}
                      </td>
                      <td className="px-4 py-3">
                        {u.role === "admin" ? (
                          <span className="inline-flex items-center gap-1 rounded-md bg-purple-500/10 px-2 py-0.5 text-[11px] font-medium text-purple-300 border border-purple-500/20">
                            <Shield className="h-3 w-3" />
                            ADMIN
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 rounded-md bg-blue-500/10 px-2 py-0.5 text-[11px] font-medium text-blue-300 border border-blue-500/20">
                            TRADER
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 font-semibold text-slate-200">
                        {u.total_backtests}
                      </td>
                      <td className="px-4 py-3">
                        {!u.is_active ? (
                          <span className="inline-flex items-center gap-1.5 text-[11px] text-rose-400 font-medium">
                            <span className="h-1.5 w-1.5 rounded-full bg-rose-400" />
                            Bị khóa
                          </span>
                        ) : isActuallyOnline ? (
                          <span className="inline-flex items-center gap-1.5 text-[11px] text-emerald-400 font-medium">
                            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                            Đang trực tuyến
                          </span>
                        ) : (
                          <span className="text-[11px] text-slate-400 font-normal">
                            {lastSeenTimeStr}
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="inline-flex items-center gap-1.5">
                          {/* Nút Đổi Role */}
                          <button
                            onClick={() => handleToggleUserRole(u)}
                            disabled={isBusy}
                            title={u.role === "admin" ? "Hạ xuống Trader" : "Nâng lên Admin"}
                            className="inline-flex items-center gap-1 rounded-lg border border-slate-700 bg-slate-800/80 px-2.5 py-1 text-[11px] font-medium text-slate-300 hover:bg-slate-700 hover:text-white transition-all disabled:opacity-50"
                          >
                            <ShieldAlert className="h-3 w-3 text-amber-400" />
                            <span>{u.role === "admin" ? "Hạ quyền" : "Cấp Admin"}</span>
                          </button>

                          {/* Nút Khóa / Mở khóa */}
                          <button
                            onClick={() => handleToggleUserStatus(u)}
                            disabled={isBusy}
                            title={u.is_active ? "Khóa tài khoản" : "Mở khóa tài khoản"}
                            className={`inline-flex items-center gap-1 rounded-lg px-2.5 py-1 text-[11px] font-medium transition-all disabled:opacity-50 ${u.is_active
                                ? "border border-rose-500/30 bg-rose-500/10 text-rose-300 hover:bg-rose-500/20"
                                : "border border-emerald-500/30 bg-emerald-500/10 text-emerald-300 hover:bg-emerald-500/20"
                              }`}
                          >
                            {u.is_active ? (
                              <>
                                <Lock className="h-3 w-3 text-rose-400" />
                                <span>Khóa</span>
                              </>
                            ) : (
                              <>
                                <Unlock className="h-3 w-3 text-emerald-400" />
                                <span>Mở</span>
                              </>
                            )}
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* 4. PHẦN 3: NHẬT KÝ HOẠT ĐỘNG & KIỂM TOÁN HỆ THỐNG / AI (ACTIVITY & AUDIT STREAM) */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5 shadow-lg">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div>
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <Activity className="h-4 w-4 text-emerald-400" />
              Nhật ký Hoạt động &amp; Giám sát Kiểm toán Hệ thống
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Ghi nhận các tác vụ Backtest của người dùng và các phiên kiểm toán dự báo AI mới nhất
            </p>
          </div>
          <button
            onClick={fetchActivities}
            disabled={activitiesLoading}
            className="text-xs text-slate-400 hover:text-slate-200 transition-colors inline-flex items-center gap-1.5"
          >
            <RefreshCw className={`h-3 w-3 ${activitiesLoading ? "animate-spin text-emerald-400" : ""}`} />
            Làm mới log
          </button>
        </div>

        {/* Khối nhật ký hoạt động: Chiều cao vừa vặn ~5 dòng, cuộn dọc mượt mà khi danh sách dài */}
        <div className="mt-4 space-y-2.5 max-h-[340px] overflow-y-auto pr-1.5 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-slate-900">
          {activitiesLoading ? (
            <div className="flex h-24 items-center justify-center text-xs text-slate-500">
              <RefreshCw className="h-4 w-4 animate-spin mr-2 text-emerald-400" />
              Đang tải nhật ký hoạt động...
            </div>
          ) : activities.length === 0 ? (
            <div className="flex h-20 items-center justify-center text-xs text-slate-500">
              Chưa có dữ liệu hoạt động nào được ghi nhận.
            </div>
          ) : (
            activities.map((item) => {
              const timeStr = new Date(item.timestamp).toLocaleTimeString("vi-VN", {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
                day: "2-digit",
                month: "2-digit",
              });

              return (
                <div
                  key={item.id}
                  className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 rounded-xl border border-slate-800/80 bg-slate-950/40 p-3 text-xs hover:border-slate-700 transition-colors"
                >
                  <div className="flex items-start gap-3">
                    <div
                      className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg ${item.event_type === "backtest"
                          ? "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                          : item.event_type === "ai_audit"
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            : "bg-purple-500/10 text-purple-400 border border-purple-500/20"
                        }`}
                    >
                      {item.event_type === "backtest" ? (
                        <TrendingUp className="h-3.5 w-3.5" />
                      ) : item.event_type === "ai_audit" ? (
                        <ShieldCheck className="h-3.5 w-3.5" />
                      ) : (
                        <UserPlus className="h-3.5 w-3.5" />
                      )}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-200">{item.title}</span>
                        {item.actor && (
                          <span className="rounded bg-slate-800/80 px-1.5 py-0.2 text-[10px] text-slate-400">
                            {item.actor}
                          </span>
                        )}
                      </div>
                      <p className="mt-0.5 text-slate-400 text-[11px]">{item.description}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 sm:shrink-0 self-end sm:self-center">
                    <span
                      className={`inline-flex items-center rounded-md px-2 py-0.5 text-[10px] font-medium ${item.status === "success"
                          ? "bg-emerald-500/10 text-emerald-300 border border-emerald-500/20"
                          : item.status === "warning"
                            ? "bg-amber-500/10 text-amber-300 border border-amber-500/20"
                            : "bg-slate-800 text-slate-300"
                        }`}
                    >
                      {item.status.toUpperCase()}
                    </span>
                    <span className="text-[10px] text-slate-500 flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {timeStr}
                    </span>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
