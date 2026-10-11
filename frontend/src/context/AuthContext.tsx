import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiFetch } from '../api/client';

export interface User {
  id: string;
  email: string;
  full_name: string;
  name?: string;
  ratings_count: number;
  is_cold_start: boolean;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  signIn: (email: string, password: string) => Promise<User>;
  signUp: (email: string, password: string, fullName: string) => Promise<User>;
  signOut: () => void;
  refreshUser: () => Promise<void>;
  setUser: React.Dispatch<React.SetStateAction<User | null>>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('cinematch_token'));
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = async () => {
    const savedToken = localStorage.getItem('cinematch_token');
    if (!savedToken) {
      setUser(null);
      setIsLoading(false);
      return;
    }

    try {
      const data = await apiFetch<any>('/auth/me');
      const currentUser: User = {
        id: data.id || data.user_id || '',
        email: data.email || '',
        full_name: data.full_name || data.name || (data.email ? data.email.split('@')[0] : 'User'),
        name: data.name || data.full_name || '',
        ratings_count: data.ratings_count ?? 0,
        is_cold_start: data.is_cold_start ?? true,
      };
      setUser(currentUser);
    } catch {
      localStorage.removeItem('cinematch_token');
      setToken(null);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshUser();
  }, []);

  const signIn = async (email: string, password: string): Promise<User> => {
    const res = await apiFetch<any>('/auth/signin', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });

    const authToken = res.access_token || res.token;
    localStorage.setItem('cinematch_token', authToken);
    setToken(authToken);

    const userObj = res.user || res;
    const currentUser: User = {
      id: userObj.id || res.user_id || '',
      email: userObj.email || res.email || email,
      full_name: userObj.full_name || userObj.name || res.full_name || (email ? email.split('@')[0] : 'User'),
      name: userObj.name || userObj.full_name || '',
      ratings_count: userObj.ratings_count ?? res.ratings_count ?? 0,
      is_cold_start: userObj.is_cold_start ?? res.is_cold_start ?? true,
    };
    setUser(currentUser);
    return currentUser;
  };

  const signUp = async (email: string, password: string, fullName: string): Promise<User> => {
    const res = await apiFetch<any>('/auth/signup', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name: fullName }),
    });

    const authToken = res.access_token || res.token;
    localStorage.setItem('cinematch_token', authToken);
    setToken(authToken);

    const userObj = res.user || res;
    const currentUser: User = {
      id: userObj.id || res.user_id || '',
      email: userObj.email || res.email || email,
      full_name: userObj.full_name || userObj.name || fullName || (email ? email.split('@')[0] : 'User'),
      name: userObj.name || userObj.full_name || fullName,
      ratings_count: userObj.ratings_count ?? res.ratings_count ?? 0,
      is_cold_start: userObj.is_cold_start ?? res.is_cold_start ?? true,
    };
    setUser(currentUser);
    return currentUser;
  };

  const signOut = () => {
    localStorage.removeItem('cinematch_token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        signIn,
        signUp,
        signOut,
        refreshUser,
        setUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
