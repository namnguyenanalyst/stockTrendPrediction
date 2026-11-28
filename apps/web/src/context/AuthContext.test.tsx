// @vitest-environment jsdom
import React, { useState } from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { AuthProvider, useAuth } from "./AuthContext";
import EmailVerificationBanner from "@/components/auth/EmailVerificationBanner";
const m = vi.hoisted(() => ({ register: vi.fn(), login: vi.fn(), refresh: vi.fn(), logout: vi.fn(), setToken: vi.fn(), getCurrentUser: vi.fn(), router: { push: vi.fn() } }));
vi.mock("next/navigation", () => ({ useRouter: () => m.router }));
vi.mock("@/lib/api", () => ({ registerUser: m.register, loginUser: m.login, refreshToken: m.refresh, logoutUser: m.logout, setAuthToken: m.setToken, setOnTokenRefreshed: vi.fn(), setOnSessionExpired: vi.fn(), getCurrentUser: m.getCurrentUser }));
function Consumer() {
  const auth = useAuth();
  const [result, setResult] = useState("");
  const [loginErr, setLoginErr] = useState("");
  return (
    <>
      <button onClick={async () => { try { const response = await auth.register("user@example.com", "password-one"); setResult(response.status); } catch { setResult("failed"); } }}>Register</button>
      <button onClick={async () => { try { await auth.login("locked@example.com", "password-one"); } catch (e) { setLoginErr(e instanceof Error ? e.message : ""); } }}>Login</button>
      <p role="status">{result}</p>
      {loginErr && <p role="alert">{loginErr}</p>}
    </>
  );
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
it("shows explicit message when login fails due to inactive account", async () => {
  m.login.mockRejectedValue(new Error('API error (400): {"detail":"Inactive user account"}'));
  render(<AuthProvider><Consumer /></AuthProvider>); fireEvent.click(screen.getByRole("button", { name: "Login" }));
  expect((await screen.findByRole("alert")).textContent).toContain("Tài khoản của bạn đã bị khóa hoặc vô hiệu hóa");
});
it("hides EmailVerificationBanner across tabs when storage sync event fires", async () => {
  localStorage.setItem("stockpulse_access_token", "valid-token");
  m.getCurrentUser
    .mockResolvedValueOnce({ id: "u1", email: "user@example.com", role: "trader", is_active: true, email_verified_at: null })
    .mockResolvedValueOnce({ id: "u1", email: "user@example.com", role: "trader", is_active: true, email_verified_at: "2026-11-28T10:00:00Z" });

  render(<AuthProvider><EmailVerificationBanner /></AuthProvider>);
  expect(await screen.findByText(/Email của bạn chưa được xác minh/)).toBeTruthy();

  window.dispatchEvent(new StorageEvent("storage", { key: "stockpulse_email_verified_at", newValue: String(Date.now()) }));
  await waitFor(() => expect(screen.queryByText(/Email của bạn chưa được xác minh/)).toBeNull());
  expect(m.getCurrentUser).toHaveBeenCalledTimes(2);
});
it("does not redirect to /login on public /reset-password when expired token fails refresh", async () => {
  window.history.pushState(null, "", "/reset-password");
  localStorage.setItem("stockpulse_access_token", "expired-token");
  m.getCurrentUser.mockRejectedValueOnce(new Error("API error (401): Token has expired"));
  m.refresh.mockRejectedValueOnce(new Error("Refresh expired"));

  render(<AuthProvider><Consumer /></AuthProvider>);
  await waitFor(() => expect(m.refresh).toHaveBeenCalledTimes(1));
  await waitFor(() => expect(localStorage.getItem("stockpulse_access_token")).toBeNull());
  expect(m.router.push).not.toHaveBeenCalled();

  window.history.pushState(null, "", "/");
});
