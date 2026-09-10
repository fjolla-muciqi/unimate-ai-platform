"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";

import { api, clearToken, getToken, setToken } from "@/lib/api";
import type { User } from "@/lib/types";

interface AuthState {
  user: User | null;

  /** True derisa tokeni i ruajtur verifikohet me backend-in. */
  loading: boolean;

  login: (email: string, password: string) => Promise<User>;
  logout: () => void;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

/** Ku shkon secili rol pas kyçjes. */
export function homeFor(user: User): string {
  if (user.role === "ADMIN") {
    return "/admin";
  }

  if (user.role === "PROFESSOR") {
    return "/teaching";
  }

  return "/dashboard";
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();

  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    if (!getToken()) {
      setUser(null);
      setLoading(false);

      return;
    }

    try {
      setUser(await api.me());
    } catch {
      // Tokeni i pavlefshëm ose i skaduar: fillojmë nga e para.
      clearToken();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const login = useCallback(
    async (email: string, password: string) => {
      const token = await api.login(email, password);

      setToken(token);

      const profile = await api.me();

      setUser(profile);

      return profile;
    },
    [],
  );

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
    router.replace("/login");
  }, [router]);

  const value = useMemo(
    () => ({ user, loading, login, logout, refresh }),
    [user, loading, login, logout, refresh],
  );

  return (
    <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth duhet përdorur brenda AuthProvider.");
  }

  return context;
}
