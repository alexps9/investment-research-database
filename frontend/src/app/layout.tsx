import type { Metadata } from 'next';
import './globals.css';
import { LangProvider } from '@/lib/i18n';
import { AuthProvider } from '@/lib/auth';
import AppGate from '@/components/AppGate';

export const metadata: Metadata = {
  title: 'HH Research – AI Intelligence Knowledge Base',
  description: 'AI signal collection and knowledge management system',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh">
      <body className="min-h-screen">
        <LangProvider>
          <AuthProvider>
            <AppGate>{children}</AppGate>
          </AuthProvider>
        </LangProvider>
      </body>
    </html>
  );
}
