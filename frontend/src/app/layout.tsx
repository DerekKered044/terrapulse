import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TerraPulse — Earth System Trend Detective",
  description:
    "Find trends in NASA MERRA-2 Earth-system data and test whether they are statistically significant and robust to the dates chosen.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full">{children}</body>
    </html>
  );
}
