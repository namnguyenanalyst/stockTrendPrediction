"use client";

import React, { useState, useEffect } from "react";
import {
  X,
  BookmarkCheck,
  AlertTriangle,
  CheckCircle,
  Copy,
} from "lucide-react";
import { SavedStrategyItem } from "@/lib/types";

interface SaveStrategyModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentStrategyName: string;
  savedStrategies: SavedStrategyItem[];
  onSave: (strategyData: {
    name: string;
    status: "active" | "draft";
    overwriteExistingId?: string;
  }) => void;
}

export const SaveStrategyModal: React.FC<SaveStrategyModalProps> = ({
  isOpen,
  onClose,
  currentStrategyName,
  savedStrategies,
  onSave,
}) => {
  const [name, setName] = useState<string>(currentStrategyName);
  const [status, setStatus] = useState<"active" | "draft">("draft");

  useEffect(() => {
    if (isOpen) {
      const timer = setTimeout(() => {
        setName(currentStrategyName);
      }, 0);
      return () => clearTimeout(timer);
    }
  }, [isOpen, currentStrategyName]);

  if (!isOpen) return null;

  // Kiểm tra trùng tên chiến lược
  const existingStrategy = savedStrategies.find(
    (s) => s.name.trim().toLowerCase() === name.trim().toLowerCase()
  );

  const handleSaveNew = () => {
    if (!name.trim()) return;
    onSave({
      name: name.trim(),
      status,
    });
    onClose();
  };

  const handleOverwrite = () => {
    if (!existingStrategy) return;
    onSave({
      name: name.trim(),
      status,
      overwriteExistingId: existingStrategy.id,
    });
    onClose();
  };

  const handleSaveAsCopy = () => {
    if (!name.trim()) return;
    let copyName = `${name.trim()} (Bản sao)`;
    let counter = 2;
    while (savedStrategies.some((s) => s.name.toLowerCase() === copyName.toLowerCase())) {
      copyName = `${name.trim()} (Bản sao ${counter})`;
      counter++;
    }
    onSave({
      name: copyName,
      status,
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 animate-fade-in">
      <div className="w-full max-w-lg rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl shadow-emerald-500/10">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500/20 text-emerald-400">
              <BookmarkCheck className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-100">Lưu chiến lược giao dịch</h3>
              <p className="text-xs text-slate-400">
                Lưu lại toàn bộ thông số, điều kiện Mua/Bán và cấu hình kiểm thử
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Body */}
        <div className="mt-4 space-y-4">
          {/* Tên chiến lược */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Tên chiến lược <span className="text-rose-400">*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="VD: Chiến lược Đa mã & Rổ VN30..."
              className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3.5 py-2.5 text-sm font-medium text-slate-100 placeholder-slate-500 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
          </div>

          {/* Cảnh báo nếu chiến lược đã tồn tại */}
          {existingStrategy && (
            <div className="rounded-xl border border-amber-500/40 bg-amber-500/10 p-3.5 text-xs text-amber-300 space-y-2">
              <div className="flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold text-amber-200">
                    Chiến lược &ldquo;{existingStrategy.name}&rdquo; đã tồn tại trong danh sách!
                  </span>
                  <p className="mt-0.5 text-amber-300/90 text-[11px]">
                    Chiến lược này đã được lưu vào lúc{" "}
                    <strong>{existingStrategy.updated_at || existingStrategy.created_at}</strong>.
                    Bạn có thể chọn <strong>Cập nhật ghi đè</strong> hoặc <strong>Lưu thành bản sao mới</strong>.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Lựa chọn trạng thái: Triển khai vs Chưa triển khai (Chuẩn DNSE) */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Trạng thái chiến lược
            </label>
            <div className="grid grid-cols-2 gap-3">
              {/* Option Chưa triển khai */}
              <label
                className={`flex cursor-pointer flex-col rounded-xl border p-3 transition-all ${
                  status === "draft"
                    ? "border-emerald-500/60 bg-emerald-500/10 text-slate-100"
                    : "border-slate-800 bg-slate-950 text-slate-400 hover:border-slate-700"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold text-emerald-400">Chưa triển khai</span>
                  <input
                    type="radio"
                    name="strategy_status"
                    checked={status === "draft"}
                    onChange={() => setStatus("draft")}
                    className="accent-emerald-500"
                  />
                </div>
                <p className="text-[11px] text-slate-400">
                  Lưu dưới dạng bản nháp để tiếp tục kiểm định và tinh chỉnh thông số.
                </p>
              </label>

              {/* Option Triển khai */}
              <label
                className={`flex cursor-pointer flex-col rounded-xl border p-3 transition-all ${
                  status === "active"
                    ? "border-emerald-500/60 bg-emerald-500/10 text-slate-100"
                    : "border-slate-800 bg-slate-950 text-slate-400 hover:border-slate-700"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold text-emerald-400">Triển khai</span>
                  <input
                    type="radio"
                    name="strategy_status"
                    checked={status === "active"}
                    onChange={() => setStatus("active")}
                    className="accent-emerald-500"
                  />
                </div>
                <p className="text-[11px] text-slate-400">
                  Kích hoạt theo dõi tín hiệu tự động cho danh mục / cổ phiếu mục tiêu.
                </p>
              </label>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="mt-6 flex flex-col gap-2 sm:flex-row sm:justify-end border-t border-slate-800 pt-4">
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl px-4 py-2.5 text-xs font-semibold text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors"
          >
            Hủy bỏ
          </button>

          {existingStrategy ? (
            <>
              <button
                type="button"
                onClick={handleSaveAsCopy}
                className="flex items-center justify-center gap-1.5 rounded-xl border border-slate-700 bg-slate-800 px-4 py-2.5 text-xs font-semibold text-slate-200 hover:border-slate-600 hover:bg-slate-700 transition-all cursor-pointer"
              >
                <Copy className="h-4 w-4 text-slate-400" />
                <span>Lưu thành bản sao</span>
              </button>
              <button
                type="button"
                onClick={handleOverwrite}
                className="flex items-center justify-center gap-1.5 rounded-xl bg-emerald-500 px-4 py-2.5 text-xs font-bold text-slate-950 shadow-lg shadow-emerald-500/20 hover:bg-emerald-400 transition-all cursor-pointer"
              >
                <CheckCircle className="h-4 w-4 fill-current" />
                <span>Cập nhật chiến lược này</span>
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={handleSaveNew}
              disabled={!name.trim()}
              className="flex items-center justify-center gap-1.5 rounded-xl bg-emerald-500 px-5 py-2.5 text-xs font-bold text-slate-950 shadow-lg shadow-emerald-500/20 hover:bg-emerald-400 disabled:opacity-50 transition-all cursor-pointer"
            >
              <BookmarkCheck className="h-4 w-4" />
              <span>Lưu chiến lược</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
