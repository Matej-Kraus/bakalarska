import React, { createContext, useContext, useEffect, useMemo, useState } from "react";

import { clearAccessToken, getAccessToken, setAccessToken } from "./token";
import * as authApi from "@/api/auth";

type AuthState = {
  token: string | null;
  user: authApi.User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (clubName: string, email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() => getAccessToken());
  const [user, setUser] = useState<authApi.User | null>(null);
  const [loading, setLoading] = useState<boolean>(Boolean(token));

  useEffect(() => {
    let cancelled = false;
    async function loadMe() {
      if (!token) return;
      try {
        setLoading(true);
        const u = await authApi.me();
        if (!cancelled) setUser(u);
      } catch {
        clearAccessToken();
        if (!cancelled) {
          setToken(null);
          setUser(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    loadMe();
    return () => {
      cancelled = true;
    };
  }, [token]);

  const value = useMemo<AuthState>(
    () => ({
      token,
      user,
      loading,
      login: async (email: string, password: string) => {
        const res = await authApi.login(email, password);
        setAccessToken(res.access_token);
        setToken(res.access_token);
        setUser(res.user);
      },
      register: async (clubName: string, email: string, password: string) => {
        await authApi.register(clubName, email, password);
      },
      logout: () => {
        clearAccessToken();
        setToken(null);
        setUser(null);
      },
    }),
    [token, user, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

