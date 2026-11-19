// @vitest-environment jsdom
import React from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import AccountActionForm from "./AccountActionForm";
import EmailVerificationBanner from "./EmailVerificationBanner";
import RegisterPage from "@/app/(auth)/register/page";
import { AccountApiError } from "@/lib/api";
const m = vi.hoisted(() => ({ reset: vi.fn(), verify: vi.fn(), forgot: vi.fn(), resend: vi.fn(), register: vi.fn(), refresh: vi.fn(), push: vi.fn(), user: { email_verified_at: null } as { email_verified_at: string | null } }));
vi.mock("@/lib/api", async original => ({ ...await original<typeof import("@/lib/api")>(), requestPasswordReset: m.forgot, resetAccountPassword: m.reset, verifyAccountEmail: m.verify, resendVerification: m.resend }));
vi.mock("@/context/AuthContext", () => ({ useAuth: () => ({ refreshUser: m.refresh, user: m.user, register: m.register }), removeTokenCookie: vi.fn() }));
vi.mock("next/navigation", () => ({ useRouter: () => ({ push: m.push }) }));
afterEach(cleanup);
beforeEach(() => { vi.clearAllMocks(); window.history.replaceState(null, "", "/"); m.user = { email_verified_at: null }; });
it("does not verify on GET, removes fragment, survives Strict Mode and verifies on confirmation", async () => {
  window.history.replaceState(null, "", "/verify-email#token=test-token");
  m.verify.mockResolvedValue({ message: "Email đã được xác minh." });
  render(<React.StrictMode><AccountActionForm mode="verify" /></React.StrictMode>);
  expect(window.location.hash).toBe(""); expect(m.verify).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Xác minh email" }));
  await waitFor(() => expect(m.verify).toHaveBeenCalledWith("test-token"));
  expect(await screen.findByRole("status")).toBeTruthy(); expect(m.refresh).toHaveBeenCalled();
});
it("shows recovery action when token is missing", () => {
  render(<AccountActionForm mode="reset" />);
  expect(screen.getByRole("link", { name: "Yêu cầu đặt lại mật khẩu" }).getAttribute("href")).toBe("/forgot-password");
  expect(screen.queryByRole("button", { name: "Lưu mật khẩu mới" })).toBeNull();
});
it("associates mismatch error with field and supports password visibility", () => {
  window.history.replaceState(null, "", "/reset-password#token=test-token"); render(<AccountActionForm mode="reset" />);
  fireEvent.change(screen.getByLabelText("Mật khẩu mới (8–1024 ký tự)"), { target: { value: "password-one" } });
  fireEvent.change(screen.getByLabelText("Xác nhận mật khẩu"), { target: { value: "password-two" } });
  fireEvent.click(screen.getByRole("button", { name: "Lưu mật khẩu mới" }));
  expect(screen.getByLabelText("Xác nhận mật khẩu").getAttribute("aria-describedby")).toBe("confirm-error"); expect(m.reset).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Hiện mật khẩu" }));
  expect(screen.getByLabelText("Xác nhận mật khẩu").getAttribute("type")).toBe("text");
});
it("handles expired reset link", async () => {
  window.history.replaceState(null, "", "/reset-password#token=expired");
  m.reset.mockRejectedValue(new AccountApiError("INVALID_OR_EXPIRED_TOKEN", "Liên kết đã hết hạn.")); render(<AccountActionForm mode="reset" />);
  for (const label of ["Mật khẩu mới (8–1024 ký tự)", "Xác nhận mật khẩu"]) fireEvent.change(screen.getByLabelText(label), { target: { value: "new-password" } });
  fireEvent.click(screen.getByRole("button", { name: "Lưu mật khẩu mới" }));
  expect(await screen.findByRole("link", { name: "Yêu cầu đặt lại mật khẩu" })).toBeTruthy(); expect(m.reset).toHaveBeenCalledWith("expired", "new-password");
});
it("normalizes recovery email and prevents immediate resubmission", async () => {
  m.forgot.mockResolvedValue({ message: "Nếu email phù hợp, bạn sẽ nhận được hướng dẫn." }); render(<AccountActionForm mode="forgot" />);
  fireEvent.change(screen.getByLabelText("Địa chỉ email"), { target: { value: "USER@example.com" } });
  fireEvent.click(screen.getByRole("button", { name: "Gửi liên kết đặt lại" }));
  expect((await screen.findByRole("button", { name: /Thử lại sau/ }) as HTMLButtonElement).disabled).toBe(true); expect(m.forgot).toHaveBeenCalledWith("user@example.com");
});
it("resends with cooldown and hides verified banner", async () => {
  m.resend.mockResolvedValue({ message: "Đã tiếp nhận yêu cầu." }); const view = render(<EmailVerificationBanner />);
  fireEvent.click(screen.getByRole("button", { name: "Gửi lại thư xác minh" })); expect(await screen.findByRole("button", { name: /Gửi lại sau/ })).toBeTruthy();
  m.user = { email_verified_at: "2026-11-19T00:00:00Z" }; view.rerender(<EmailVerificationBanner />); expect(screen.queryByRole("complementary")).toBeNull();
});
it("reports account created separately from automatic login failure", async () => {
  m.register.mockResolvedValue({ status: "created" }); render(<RegisterPage />);
  fireEvent.change(screen.getByLabelText(/Địa chỉ Email/), { target: { value: "user@example.com" } });
  fireEvent.change(screen.getByLabelText(/^Mật khẩu \(/), { target: { value: "password-one" } });
  fireEvent.change(screen.getByLabelText(/Xác nhận mật khẩu/), { target: { value: "password-one" } });
  fireEvent.click(screen.getByRole("button", { name: "Hoàn tất đăng ký" }));
  expect(await screen.findByText("Tài khoản đã được tạo. Vui lòng đăng nhập để tiếp tục.")).toBeTruthy();
  expect(screen.getByRole("link", { name: "Đăng nhập" }).getAttribute("href")).toBe("/login?email=user%40example.com"); expect(m.push).not.toHaveBeenCalled();
});
