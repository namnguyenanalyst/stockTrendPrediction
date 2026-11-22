"use client";
import { useEffect, useId, useRef, useState } from "react";
import { Search, Check, X } from "lucide-react";
import { CHART_INDICATORS, searchIndicators } from "@/lib/chartIndicators";
export function IndicatorSearch({
  selected,
  onChange,
}: {
  selected: string[];
  onChange: (ids: string[]) => void;
}) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const root = useRef<HTMLDivElement>(null);
  const id = useId();
  const results = searchIndicators(query);
  const toggle = (key: string) =>
    onChange(
      selected.includes(key)
        ? selected.filter((x) => x !== key)
        : [...selected, key],
    );
  useEffect(() => {
    const close = (e: PointerEvent) => {
      if (!root.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("pointerdown", close);
    return () => document.removeEventListener("pointerdown", close);
  }, []);
  return (
    <div ref={root} className="relative w-full sm:w-80">
      <div className="flex items-center gap-2 rounded-md border border-slate-700 bg-slate-900 px-3 focus-within:border-emerald-400">
        <Search size={16} className="shrink-0 text-slate-400" />
        <input
          role="combobox"
          aria-label="Tìm chỉ báo"
          aria-expanded={open}
          aria-controls={id}
          aria-autocomplete="list"
          aria-activedescendant={
            open && results[active] ? `${id}-${active}` : undefined
          }
          value={query}
          placeholder="Tìm chỉ báo…"
          className="h-9 min-w-0 w-full bg-transparent text-sm text-slate-100 outline-none placeholder:text-slate-400"
          onFocus={() => setOpen(true)}
          onChange={(e) => {
            setQuery(e.target.value);
            setActive(0);
            setOpen(true);
          }}
          onKeyDown={(e) => {
            if (e.key === "Escape" && open) {
              e.stopPropagation();
              setOpen(false);
            }
            if (e.key === "ArrowDown" || e.key === "ArrowUp") {
              e.preventDefault();
              setOpen(true);
              setActive(
                (i) =>
                  (i +
                    (e.key === "ArrowDown" ? 1 : -1) +
                    Math.max(1, results.length)) %
                  Math.max(1, results.length),
              );
            }
            if (e.key === "Enter" && open && results[active]) {
              e.preventDefault();
              toggle(results[active].id);
            }
          }}
        />
      </div>
      {open && (
        <div
          id={id}
          role="listbox"
          aria-label="Chỉ báo hỗ trợ"
          aria-multiselectable="true"
          className="absolute top-10 z-50 max-h-64 w-full overflow-y-auto rounded-md border border-slate-700 bg-slate-900 p-1 shadow-lg"
        >
          {results.length ? (
            results.map((d, i) => (
              <div
                key={d.id}
                id={`${id}-${i}`}
                role="option"
                aria-selected={selected.includes(d.id)}
                onMouseDown={(e) => e.preventDefault()}
                onMouseEnter={() => setActive(i)}
                onClick={() => toggle(d.id)}
                className={`flex cursor-pointer items-center gap-2 rounded px-2 py-2 ${active === i ? "bg-slate-800" : ""}`}
              >
                <span
                  style={{ backgroundColor: d.color }}
                  className="h-2 w-2 shrink-0 rounded-full"
                />
                <span className="flex-1 text-slate-100">
                  {d.name}
                  <span className="block text-xs text-slate-400">
                    {d.description}
                  </span>
                </span>
                {selected.includes(d.id) && (
                  <Check size={16} className="text-emerald-400" />
                )}
              </div>
            ))
          ) : (
            <p className="p-3 text-sm text-slate-300">
              Không tìm thấy chỉ báo phù hợp
            </p>
          )}
        </div>
      )}
      <div className="mt-2 flex max-h-20 flex-wrap gap-1 overflow-y-auto">
        {CHART_INDICATORS.filter((d) => selected.includes(d.id)).map((d) => (
          <button
            key={d.id}
            onClick={() => toggle(d.id)}
            aria-label={`Gỡ ${d.name}`}
            className="flex min-h-9 items-center gap-1 rounded border border-slate-700 px-2 text-xs text-slate-200 hover:bg-slate-800"
          >
            <span style={{ color: d.color }}>{d.name}</span>
            <X size={12} />
          </button>
        ))}
      </div>
    </div>
  );
}
