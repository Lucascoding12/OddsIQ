import type { Metadata } from "next"
import { DM_Sans, IBM_Plex_Mono } from "next/font/google"
import "./globals.css"
import { Navbar } from "@/components/nav/Navbar"
import { BetsProvider } from "@/context/BetsContext"
import { AuthProvider } from "@/context/AuthContext"

const dmSans = DM_Sans({ subsets: ["latin"], variable: "--font-dm-sans" })
const ibmPlexMono = IBM_Plex_Mono({ subsets: ["latin"], weight: ["400", "500", "600"], variable: "--font-plex-mono" })

export const metadata: Metadata = {
  title: { default: "OddsIQ — Sharp Betting Tools", template: "%s · OddsIQ" },
  description:
    "Line shopping, EV and arbitrage calculators, CLV tracking, and live odds across 80+ sportsbooks — free.",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${dmSans.variable} ${ibmPlexMono.variable} font-sans`}>
        <AuthProvider>
          <BetsProvider>
            <Navbar />
            <main className="max-w-7xl mx-auto px-4 py-6">{children}</main>
          </BetsProvider>
        </AuthProvider>
      </body>
    </html>
  )
}
