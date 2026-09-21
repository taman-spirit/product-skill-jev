import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Providers } from '@/components/layout/Providers'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: {
    default: 'AISilicons — AI Co-pilot for Product Managers',
    template: '%s | AISilicons',
  },
  description:
    'Score features with RICE, write PRDs, manage Epics, detect conflicts, track stakeholders. Plain language. Files you own.',
  keywords: ['product management', 'PRD', 'AI', 'RICE scoring', 'product requirements'],
  authors: [{ name: 'AISilicons' }],
  icons: {
    icon: '/logo.png',
    apple: '/logo.png',
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://aisilicons.com',
    siteName: 'AISilicons',
    title: 'AISilicons — AI Co-pilot for Product Managers',
    description: 'Score features with RICE, write PRDs, manage Epics. Plain language. Files you own.',
    images: [{ url: '/logo.png', width: 512, height: 512, alt: 'AISilicons' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'AISilicons',
    description: 'AI Co-pilot for Product Managers',
    images: ['/logo.png'],
  },
  robots: { index: true, follow: true },
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000'),
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
