import React from "react";
import EmailVerificationBanner from "@/components/auth/EmailVerificationBanner";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <><EmailVerificationBanner />{children}</>;
}
