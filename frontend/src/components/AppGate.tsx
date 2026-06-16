'use client';
import React from 'react';
import { Loader2 } from 'lucide-react';
import { useAuth } from '@/lib/auth';
import Sidebar from '@/components/Sidebar';
import LoginScreen from '@/components/LoginScreen';

export default function AppGate({ children }: { children: React.ReactNode }) {
  const { user, ready } = useAuth();

  if (!ready) {
    return (
      <div className="flex min-h-screen w-full items-center justify-center bg-slate-50">
        <Loader2 size={28} className="animate-spin text-blue-500" />
      </div>
    );
  }

  if (!user) {
    return <LoginScreen />;
  }

  return (
    <div className="flex min-h-screen w-full">
      <Sidebar />
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
