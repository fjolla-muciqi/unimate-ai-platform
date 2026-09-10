import type { Metadata } from "next";

import { AuthProvider } from "@/lib/auth-context";

import "./globals.css";

export const metadata: Metadata = {
  title: "UniMate AI",
  description:
    "Platforma universitare me asistent AI multi-agent dhe RAG.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="sq">
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
