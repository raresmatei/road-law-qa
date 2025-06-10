// src/store/AuthContext.tsx
import React, {
  createContext,
  useEffect,
  useState,
  useCallback,
} from 'react';
import type { ReactNode } from 'react';
import { loginService } from '../services/authService';
import type {LoginPayload} from '../services/authService';

interface User {
  username: string;
}

interface AuthContextType {
  user: User | null;
  login: (credentials: LoginPayload) => Promise<void>;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextType>({
  user: null,
  login: async () => {},
  logout: () => {},
});

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);

  // On mount, restore from localStorage
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const storedUsername = localStorage.getItem('user_username');
    if (token && storedUsername) {
      setUser({ username: storedUsername });
    }
  }, []);

  // login() now calls the real /login endpoint with { username, password }
  const login = useCallback(
    async ({ username, password }: LoginPayload) => {
      const data = await loginService({ username, password });
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('user_username', username);
      setUser({ username });
    },
    []
  );

  const logout = useCallback(() => {
    setUser(null);
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_username');
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
