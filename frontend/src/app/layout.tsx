import type { Metadata, Viewport } from "next";
import { Atkinson_Hyperlegible_Mono, Atkinson_Hyperlegible_Next, Fira_Code, Fira_Sans } from "next/font/google";
import { THEME_INIT_SCRIPT } from "@/hooks/useTheme";
import "./globals.css";

// Passenger side: Atkinson Hyperlegible, designed for low-vision readability. Codes (PNR, flight,
// airport) use its mono sibling so characters like 0/O and 1/I stay distinct.
const atkinson = Atkinson_Hyperlegible_Next({ variable: "--font-atkinson", subsets: ["latin"], adjustFontFallback: false });
const atkinsonMono = Atkinson_Hyperlegible_Mono({ variable: "--font-atkinson-mono", subsets: ["latin"], adjustFontFallback: false });

// Admin console: Fira Sans + Fira Code, tuned for dense tables and numbers.
const firaSans = Fira_Sans({ variable: "--font-fira-sans", subsets: ["latin"], weight: ["400", "500", "600", "700"] });
const firaCode = Fira_Code({ variable: "--font-fira-code", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Kenya Airways Assistant",
  description: "Passenger self-service and AI assistant (academic prototype).",
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#15181d" },
  ],
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    // suppressHydrationWarning: the inline script sets data-theme before React hydrates.
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
      </head>
      <body
        className={`${atkinson.variable} ${atkinsonMono.variable} ${firaSans.variable} ${firaCode.variable} font-sans antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
