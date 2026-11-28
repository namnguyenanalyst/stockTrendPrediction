"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Eye, EyeOff } from "lucide-react";
import { AccountApiError, requestPasswordReset, resetAccountPassword, verifyAccountEmail, setAuthToken } from "@/lib/api";
import { removeTokenCookie, useAuth } from "@/context/AuthContext";

type Mode = "forgot" | "reset" | "verify";
const field = "mt-2 min-h-11 w-full rounded-md border border-slate-700 bg-slate-950 px-3 text-base text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-400";
const button = "min-h-11 rounded-md bg-emerald-400 px-4 py-2 font-semibold text-slate-950 hover:bg-emerald-300 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-emerald-300 disabled:opacity-50";

export default function AccountActionForm({ mode }: { mode: Mode }) {
  const { refreshUser } = useAuth();
  const token = useRef("");
  const [ready, setReady] = useState(mode === "forgot");
  const [validToken, setValidToken] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [visible, setVisible] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [waitUntil, setWaitUntil] = useState(0);
  const [remaining, setRemaining] = useState(0);
  const title = mode === "forgot" ? "Quên mật khẩu" : mode === "reset" ? "Đặt lại mật khẩu" : "Xác minh email";

  useEffect(() => {
    if (mode === "forgot") return;
    // Ref survives the Strict Mode effect replay after the fragment is removed.
    if (!token.current) token.current = new URLSearchParams(window.location.hash.slice(1)).get("token") || "";
    window.history.replaceState(null, "", window.location.pathname);
    setValidToken(Boolean(token.current));
    setReady(true);
  }, [mode]);

  useEffect(() => {
    const update = () => setRemaining(Math.max(0, Math.ceil((waitUntil - Date.now()) / 1000)));
    update();
    const id = window.setInterval(update, 1000);
    return () => window.clearInterval(id);
  }, [waitUntil]);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (busy || remaining || done) return;
    const next: Record<string, string> = {};
    if (mode === "reset") {
      if (password.length < 8 || password.length > 1024) next.password = "Mật khẩu phải từ 8 đến 1024 ký tự.";
      if (password !== confirm) next.confirm = "Mật khẩu xác nhận không khớp.";
    }
    setErrors(next);
    if (Object.keys(next).length) return;
    setBusy(true);
    setMessage("");
    try {
      if (mode === "forgot") {
        const result = await requestPasswordReset(email.trim().toLowerCase());
        setMessage(result.message);
        setWaitUntil(Date.now() + 60_000);
      } else if (mode === "reset") {
        await resetAccountPassword(token.current, password);
        setPassword(""); setConfirm("");
        setAuthToken(null); removeTokenCookie();
        window.localStorage.removeItem("stockpulse_access_token");
        window.localStorage.removeItem("stockpulse_watchlist_symbols");
        window.localStorage.removeItem("stockpulse_saved_strategies_v1");
        window.location.replace("/login?reset=success");
      } else {
        const result = await verifyAccountEmail(token.current);
        setMessage(result.message); setDone(true);
        try {
          if (typeof window !== "undefined") {
            window.localStorage.setItem("stockpulse_email_verified_at", String(Date.now()));
          }
          if (typeof BroadcastChannel !== "undefined") {
            const channel = new BroadcastChannel("stockpulse_auth_sync");
            channel.postMessage({ type: "email_verified" });
            channel.close();
          }
        } catch {
          // Ignore storage/BroadcastChannel restrictions
        }
        await refreshUser();
      }
    } catch (error) {
      setErrors({ form: error instanceof Error ? error.message : "Chưa thể xử lý. Vui lòng thử lại." });
      if (error instanceof AccountApiError && error.retryAfter) setWaitUntil(Date.now() + error.retryAfter * 1000);
      if (error instanceof AccountApiError && error.code === "INVALID_OR_EXPIRED_TOKEN") setValidToken(false);
    } finally { setBusy(false); }
  }

  return <section className="rounded-lg border border-slate-800 bg-slate-900 p-6 sm:p-8">
    <h1 className="text-2xl font-semibold text-slate-100">{title}</h1>
    <p className="mt-3 text-sm leading-6 text-slate-300">{mode === "forgot" ? "Nhập email tài khoản để nhận liên kết đặt lại mật khẩu." : mode === "reset" ? "Chọn mật khẩu mới. Các phiên đăng nhập cũ sẽ được thu hồi." : "Bấm xác nhận để xác minh email của bạn. Bạn vẫn có thể sử dụng hệ thống khi chưa xác minh."}</p>
    {message && <p role="status" className="mt-4 text-sm text-emerald-300">{message}</p>}
    {errors.form && <p role="alert" className="mt-4 text-sm text-rose-300">{errors.form}</p>}
    {!ready ? <p role="status" className="mt-4">Đang đọc liên kết...</p> : mode !== "forgot" && !validToken ? <div className="mt-4 space-y-3 text-sm">
      <p>Liên kết không hợp lệ hoặc không còn sử dụng được. Vui lòng yêu cầu liên kết mới.</p>
      <Link className="inline-flex min-h-11 items-center text-emerald-300 underline" href={mode === "reset" ? "/forgot-password" : "/dashboard"}>{mode === "reset" ? "Yêu cầu đặt lại mật khẩu" : "Vào dashboard để gửi lại thư xác minh"}</Link>
    </div> : !done && <form onSubmit={submit} className="mt-6 space-y-5" aria-busy={busy}>
      {mode === "forgot" && <label className="block text-sm" htmlFor="recovery-email">Địa chỉ email<input id="recovery-email" name="email" className={field} type="email" autoComplete="email" required maxLength={255} value={email} onChange={e => setEmail(e.target.value)} /></label>}
      {mode === "reset" && <>
        <div><label className="text-sm" htmlFor="new-password">Mật khẩu mới (8–1024 ký tự)</label><input id="new-password" name="password" className={field} type={visible ? "text" : "password"} autoComplete="new-password" required minLength={8} maxLength={1024} value={password} onChange={e => setPassword(e.target.value)} aria-invalid={Boolean(errors.password)} aria-describedby={errors.password ? "password-error" : undefined} />{errors.password && <p id="password-error" role="alert" className="mt-2 text-sm text-rose-300">{errors.password}</p>}</div>
        <div><label className="text-sm" htmlFor="confirm-password">Xác nhận mật khẩu</label><input id="confirm-password" name="confirm" className={field} type={visible ? "text" : "password"} autoComplete="new-password" required minLength={8} maxLength={1024} value={confirm} onChange={e => setConfirm(e.target.value)} aria-invalid={Boolean(errors.confirm)} aria-describedby={errors.confirm ? "confirm-error" : undefined} />{errors.confirm && <p id="confirm-error" role="alert" className="mt-2 text-sm text-rose-300">{errors.confirm}</p>}</div>
        <button type="button" aria-pressed={visible} onClick={() => setVisible(!visible)} className="flex min-h-11 items-center gap-2 text-sm text-slate-200 focus-visible:outline-2 focus-visible:outline-emerald-300">{visible ? <EyeOff size={18} /> : <Eye size={18} />}{visible ? "Ẩn mật khẩu" : "Hiện mật khẩu"}</button>
      </>}
      <button type="submit" className={`${button} w-full`} disabled={busy || remaining > 0}>{busy ? "Đang xử lý..." : remaining ? `Thử lại sau ${remaining} giây` : mode === "forgot" ? "Gửi liên kết đặt lại" : mode === "reset" ? "Lưu mật khẩu mới" : "Xác minh email"}</button>
    </form>}
    <div className="mt-6 flex flex-wrap gap-x-5 text-sm"><Link className="inline-flex min-h-11 items-center text-emerald-300 underline" href="/login">Về đăng nhập</Link>{mode === "verify" && <Link className="inline-flex min-h-11 items-center text-emerald-300 underline" href="/dashboard">Vào dashboard</Link>}</div>
  </section>;
}
