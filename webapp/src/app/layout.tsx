import type { Metadata } from 'next';
import './globals.css';
import { LangProvider } from '@/lib/i18n';

export const metadata: Metadata = {
  title: 'Research Studio',
  description: 'Deep research with trajectory, people, and industry views',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh">
      <body className="min-h-screen">
        <LangProvider>{children}</LangProvider>
      </body>
    </html>
  );
}
