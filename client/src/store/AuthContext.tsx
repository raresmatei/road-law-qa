import React, {
  createContext,
  useEffect,
  useState,
  useCallback,
} from 'react';
import type { ReactNode } from 'react';
import { loginService } from '../services/authService';
import type { LoginPayload, LoginResponse } from '../services/authService';

interface User {
  username: string;
}

interface AuthContextType {
  user: User | null;
  isAdmin: boolean;
  login: (credentials: LoginPayload) => Promise<boolean>;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextType>({
  user: null,
  isAdmin: false,
  login: async () => false,
  logout: () => {},
});

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);

  // Restore from localStorage on mount
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const storedUsername = localStorage.getItem('user_username');
    const storedIsAdmin = localStorage.getItem('is_admin');
    if (token && storedUsername) {
      setUser({ username: storedUsername });
      setIsAdmin(storedIsAdmin === 'true');
    }
  }, []);

  const login = useCallback(
    async ({ username, password }: LoginPayload) => {
      const data: LoginResponse = await loginService({ username, password });
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('user_username', username);
      localStorage.setItem('is_admin', data.is_admin.toString());
      setUser({ username });
      setIsAdmin(data.is_admin);
      return data.is_admin;
    },
    []
  );

  const logout = useCallback(() => {
    setUser(null);
    setIsAdmin(false);
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_username');
    localStorage.removeItem('is_admin');
  }, []);

  return (
    <AuthContext.Provider value={{ user, isAdmin, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
