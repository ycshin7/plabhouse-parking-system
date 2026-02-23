import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
    title: "🅿️ 플랩하우스 주차 시스템",
    description: "플랩하우스 크루를 위한 주차 배정 시스템",
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="ko">
            <body className="min-h-screen bg-slate-100">
                {children}
            </body>
        </html>
    );
}
