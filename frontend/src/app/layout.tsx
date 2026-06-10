import type { Metadata } from 'next';
import './globals.css';
import Sidebar from '@/components/Sidebar';
import { LangProvider } from '@/lib/i18n';

export const metadata: Metadata = {
  title: 'HH Research – AI Intelligence Knowledge Base',
  description: 'AI signal collection and knowledge management system',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh">
      <body className="flex min-h-screen">
        <LangProvider>
          <Sidebar />
          <main className="flex-1 overflow-auto">
            {children}
          </main>
        </LangProvider>
      </body>
    </html>
  );
}
