'use client';
import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { api, TOKEN_KEY } from './api';

export interface AuthUser {
  id: string;
  username: string;
  display_name?: string | null;
  is_admin?: boolean;
}

interface TokenResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

interface AuthCtx {
  user: AuthUser | null;
  ready: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthCtx>({
  user: null,
  ready: false,
  login: async () => {},
  logout: () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [ready, setReady] = useState(false);

  // Restore session: if a token exists, validate it against /auth/me.
  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      setReady(true);
      return;
    }
    api
      .get<AuthUser>('/auth/me')
      .then((u) => setUser(u))
      .catch(() => localStorage.removeItem(TOKEN_KEY))
      .finally(() => setReady(true));
  }, []);

  // Other tabs / expired-token events clear the session.
  useEffect(() => {
    const onExpired = () => setUser(null);
    window.addEventListener('hh-auth-expired', onExpired);
    return () => window.removeEventListener('hh-auth-expired', onExpired);
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const res = await api.post<TokenResponse>('/auth/login', { username, password });
    localStorage.setItem(TOKEN_KEY, res.access_token);
    setUser(res.user);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, ready, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
