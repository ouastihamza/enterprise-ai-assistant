import type { Metadata } from "next";

import { AuthProvider } from "../context/auth-context";

import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "ATLAS",
    template: "%s · ATLAS",
  },
  description:
    "Enterprise customer intelligence and grounded AI assistant.",
};

interface RootLayoutProps {
  children: React.ReactNode;
}

export default function RootLayout({
  children,
}: RootLayoutProps) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
