import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Pulse-0G",
  description:
    "Autoevaluación de salud en misión, con cada afirmación atada a su fuente.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
