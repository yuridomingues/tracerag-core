import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TraceRAG",
  description: "Black-box regression testing for RAG APIs.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
