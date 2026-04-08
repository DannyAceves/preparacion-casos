import type { Metadata } from "next";
import { ReactNode } from "react";

import "@/app/globals.css";
import { appConfig } from "@/lib/config";

export const metadata: Metadata = {
  title: appConfig.appName,
  description: "Internal staff workspace for case preparation operations.",
};

interface RootLayoutProps {
  children: ReactNode;
}

export default function RootLayout({ children }: RootLayoutProps): JSX.Element {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
