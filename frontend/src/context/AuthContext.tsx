import { createContext, useContext, useState } from "react";
import type { ReactNode } from "react";
import { tokens } from "../services/tokens";

interface AuthContextType {
  token: string | null;
  login: (access: string, refresh: string) => void;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(tokens.getAccess());

  function login(access: string, refresh: string) {
    tokens.set(access, refresh);
    setToken(access);
  }

  function logout() {
    tokens.clear();
    setToken(null);
  }

  return (
    <AuthContext.Provider value={{ token, login, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
