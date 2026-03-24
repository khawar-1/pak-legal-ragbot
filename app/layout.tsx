import "./globals.css";
import { Inter } from "next/font/google";
import { AppRouterCacheProvider } from "@mui/material-nextjs/v13-appRouter";
import ThemeProvider from "./components/ThemeProvider";

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
  title: "Legal Case Assistant",
  description: "AI-powered Pakistan legal case assistant with RAG technology",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AppRouterCacheProvider>
          <ThemeProvider>
            {children}
          </ThemeProvider>
        </AppRouterCacheProvider>
      </body>
    </html>
  );
}
