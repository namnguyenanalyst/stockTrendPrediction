// @vitest-environment jsdom
import React from "react";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { IndicatorSearch } from "./IndicatorSearch";
afterEach(cleanup);
it("filters, toggles with keyboard, and consumes Escape", () => {
  const change = vi.fn();
  const parent = vi.fn();
  render(
    <div onKeyDown={parent}>
      <IndicatorSearch selected={["RSI"]} onChange={change} />
    </div>,
  );
  const input = screen.getByRole("combobox");
  fireEvent.focus(input);
  fireEvent.change(input, { target: { value: "macd" } });
  expect(screen.getAllByRole("option")).toHaveLength(1);
  fireEvent.keyDown(input, { key: "Enter" });
  expect(change).toHaveBeenCalledWith(["RSI", "MACD"]);
  parent.mockClear();
  fireEvent.keyDown(input, { key: "Escape" });
  expect(parent).not.toHaveBeenCalled();
  expect(screen.queryByRole("listbox")).toBeNull();
});
it("removes selected entries and shows no matches", () => {
  const change = vi.fn();
  render(<IndicatorSearch selected={["RSI"]} onChange={change} />);
  fireEvent.click(screen.getByRole("button", { name: "Gỡ RSI (14)" }));
  expect(change).toHaveBeenCalledWith([]);
  fireEvent.change(screen.getByRole("combobox"), { target: { value: "xxxx" } });
  expect(screen.getByText("Không tìm thấy chỉ báo phù hợp")).toBeTruthy();
});
