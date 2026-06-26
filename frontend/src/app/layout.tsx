import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NOVO Control Center",
  description: "Owner-controlled Personal AI Operating System",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
