import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Ergonomia - IRL Chatbot",
  description: "Chatbot für das Immersive Reality Lab",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="de">
      <body>{children}</body>
    </html>
  );
}
