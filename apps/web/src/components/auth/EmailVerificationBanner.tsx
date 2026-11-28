"use client";
import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { AccountApiError, resendVerification } from "@/lib/api";

export default function EmailVerificationBanner() {
  const { user } = useAuth();
  const [message, setMessage] = useState("");
  const [error, setError] = useState(false);
  const [busy, setBusy] = useState(false);
  const [until, setUntil] = useState(0);
  const [remaining, setRemaining] = useState(0);
  useEffect(() => {
    const update = () => setRemaining(Math.max(0, Math.ceil((until - Date.now()) / 1000)));
    update(); const id = window.setInterval(update, 1000);
    return () => window.clearInterval(id);
  }, [until]);
  if (!user || user.email_verified_at) return null;
  async function resend() {
    if (busy || remaining) return;
    setBusy(true); setError(false);
    try {
      const result = await resendVerification(); setMessage(result.message); setUntil(Date.now() + 60_000);
    } catch (err) {
      setError(true); setMessage(err instanceof Error ? err.message : "Chưa thể gửi thư. Vui lòng thử lại.");
      if (err instanceof AccountApiError && err.retryAfter) setUntil(Date.now() + err.retryAfter * 1000);
    } finally { setBusy(false); }
  }
  return <aside aria-label="Xác minh email" className="relative z-10 border-b border-slate-700 bg-slate-900 px-4 py-3 text-sm text-slate-200 sm:px-6">
    <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3"><p>Email của bạn chưa được xác minh. Bạn vẫn có thể sử dụng hệ thống.</p><button type="button" onClick={resend} disabled={busy || remaining > 0} className="min-h-11 rounded-md border border-slate-600 px-4 text-emerald-300 hover:bg-slate-800 focus-visible:outline-2 focus-visible:outline-emerald-300 disabled:opacity-60">{busy ? "Đang gửi..." : remaining ? `Gửi lại sau ${remaining} giây` : "Gửi lại thư xác minh"}</button></div>
    {message && <p role={error ? "alert" : "status"} className={`mx-auto mt-2 max-w-7xl ${error ? "text-rose-300" : "text-emerald-300"}`}>{message}</p>}
  </aside>;
}
