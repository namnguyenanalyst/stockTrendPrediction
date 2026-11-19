// @vitest-environment jsdom
import React, { useState } from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { AuthProvider, useAuth } from "./AuthContext";
const m = vi.hoisted(() => ({ register: vi.fn(), login: vi.fn(), refresh: vi.fn(), logout: vi.fn(), setToken: vi.fn(), router: { push: vi.fn() } }));
vi.mock("next/navigation", () => ({ useRouter: () => m.router }));
vi.mock("@/lib/api", () => ({ registerUser: m.register, loginUser: m.login, refreshToken: m.refresh, logoutUser: m.logout, setAuthToken: m.setToken, getCurrentUser: vi.fn() }));
function Consumer() {
  const auth = useAuth(); const [result, setResult] = useState("");
  return <><button onClick={async () => { try { const response = await auth.register("user@example.com", "password-one"); setResult(response.status); } catch { setResult("failed"); } }}>Register</button><p role="status">{result}</p></>;
}
afterEach(cleanup);
beforeEach(() => {
  vi.clearAllMocks(); localStorage.clear();
  for (const key of ["access_token", "auth_token"]) document.cookie = `${key}=; max-age=0; path=/`;
  m.refresh.mockRejectedValue(new Error("No session")); m.logout.mockResolvedValue(undefined);
});
it("preserves account creation when automatic login fails", async () => {
  m.register.mockResolvedValue({ id: "new-user" }); m.login.mockRejectedValue(new Error("offline"));
  render(<AuthProvider><Consumer /></AuthProvider>); fireEvent.click(screen.getByRole("button", { name: "Register" }));
  expect(await screen.findByText("created")).toBeTruthy(); expect(m.register).toHaveBeenCalledTimes(1);
  expect(localStorage.getItem("stockpulse_access_token")).toBeNull();
});
it("does not attempt login if account creation fails", async () => {
  m.register.mockRejectedValue(new Error("API error (400): Email already registered"));
  render(<AuthProvider><Consumer /></AuthProvider>); fireEvent.click(screen.getByRole("button", { name: "Register" }));
  expect(await screen.findByText("failed")).toBeTruthy(); expect(m.login).not.toHaveBeenCalled();
});
it("returns authenticated on successful automatic login", async () => {
  m.register.mockResolvedValue({ id: "new-user" }); m.login.mockResolvedValue({ access_token: "test-token", user: { id: "new-user", email: "user@example.com" } });
  render(<AuthProvider><Consumer /></AuthProvider>); fireEvent.click(screen.getByRole("button", { name: "Register" }));
  expect(await screen.findByText("authenticated")).toBeTruthy(); expect(m.login).toHaveBeenCalledWith("user@example.com", "password-one");
});
