import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { Navbar } from "@/components/nav/Navbar"
import { BetsProvider } from "@/context/BetsContext"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "OddsIQ",
  description: "Sports odds aggregation and sharp analytics",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <BetsProvider>
          <Navbar />
          <main className="max-w-7xl mx-auto px-4 py-6">{children}</main>
        </BetsProvider>
      </body>
    </html>
  )
}
