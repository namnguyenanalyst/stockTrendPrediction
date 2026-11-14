"use client";

import { useEffect, useId, useRef, useState } from "react";
import { createExclusiveAction } from "@/lib/exclusiveAction";

export function DeleteStrategyDialog({ name, onDelete, onClose }: {
  name: string; onDelete: () => Promise<boolean>; onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const once = useRef(createExclusiveAction());
  const [pending, setPending] = useState(false);
  const [error, setError] = useState(false);
  const titleId = useId();
  useEffect(() => {
    const element = dialog.current;
    element?.showModal();
    return () => element?.close();
  }, []);
  const confirm = async () => {
    const deleted = await once.current(async () => {
      setPending(true); setError(false);
      try { return await onDelete(); }
      catch { return false; }
      finally { setPending(false); }
    });
    if (deleted) onClose(); else setError(true);
  };
  return (
    <dialog ref={dialog} aria-labelledby={titleId} aria-busy={pending}
      onCancel={event => { event.preventDefault(); if (!pending) onClose(); }}
      className="m-auto w-[calc(100%_-_2rem)] max-w-md rounded-xl border border-slate-700 bg-slate-900 p-5 text-slate-100 backdrop:bg-black/70">
      <h2 id={titleId} className="text-base font-semibold">Xóa chiến lược?</h2>
      <p className="mt-3 text-sm text-slate-300">Bạn sẽ xóa bản lưu “{name}” khỏi tài khoản. Thao tác này không thể hoàn tác.</p>
      {error && <p role="alert" className="mt-3 text-sm text-amber-300">Chưa xóa được. Bản lưu vẫn được giữ; hãy thử lại.</p>}
      <div className="mt-5 flex justify-end gap-3">
        <button type="button" disabled={pending} onClick={onClose} className="rounded-md border border-slate-600 px-4 py-2 text-sm disabled:opacity-50">Hủy</button>
        <button type="button" disabled={pending} onClick={() => void confirm()} className="rounded-md bg-rose-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">{pending ? "Đang xóa…" : "Xác nhận xóa"}</button>
      </div>
    </dialog>
  );
}
