import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "StockPulse VN — Hệ thống Dự báo Xu hướng & Đánh giá Chiến lược Đầu tư",
  description:
    "Hệ thống Dự báo Xu hướng Thị trường Chứng khoán & Đánh giá Chiến lược Đầu tư dựa trên Học máy và Phân tích Định lượng (ĐATN Tin học Kinh tế - HUMG)",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="vi" className="dark" suppressHydrationWarning>
      <body
        className="min-h-screen bg-slate-950 text-slate-100 antialiased selection:bg-emerald-500 selection:text-slate-950"
        suppressHydrationWarning
      >
        {children}
      </body>
    </html>
  );
}
