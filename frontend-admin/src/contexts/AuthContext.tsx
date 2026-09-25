import { createContext, useContext, useState, useEffect, ReactNode, useRef, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { User, AuthContextType, MANAGER_ROLES } from '@/types';
import api from '@/api/client';
import { adminIdentityKey } from '@/lib/adminQueryScope';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// eslint-disable-next-line react-refresh/only-export-components -- hook lives with its provider by design
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

// Data pages can also be rendered without the auth shell in isolated tests.
export const useAuthUser = () => useContext(AuthContext)?.user ?? null;

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const queryClient = useQueryClient();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const identityRef = useRef<string | null>(null);
  const checkSequence = useRef(0);

  const applyUser = useCallback((nextUser: User | null) => {
    const nextIdentity = nextUser ? adminIdentityKey(nextUser) : null;
    if (identityRef.current !== null && identityRef.current !== nextIdentity) {
      queryClient.clear();
    }
    identityRef.current = nextIdentity;
    setUser(nextUser);
  }, [queryClient]);

  useEffect(() => {
    const checkAuth = async () => {
      const sequence = ++checkSequence.current;
      const token = readSharedToken() || localStorage.getItem('adminToken');
      if (token) {
        try {
          const response = await api.get('/v1/accounts/me/');
          if (sequence !== checkSequence.current) return;
          if (MANAGER_ROLES.includes(response.data.role)) {
            applyUser(response.data);
          } else if (response.data.role === 'student') {
            queryClient.clear();
            identityRef.current = null;
            window.location.replace('/');
            return;
          } else {
            queryClient.clear();
            identityRef.current = null;
            setUser(null);
            localStorage.removeItem('adminToken');
          }
        } catch {
          if (sequence !== checkSequence.current) return;
          queryClient.clear();
          identityRef.current = null;
          setUser(null);
          localStorage.removeItem('adminToken');
        }
      } else {
        queryClient.clear();
        identityRef.current = null;
        setUser(null);
      }
      if (sequence !== checkSequence.current) return;
      setLoading(false);
    };

    const refreshOnStorageChange = (event: StorageEvent) => {
      if (event.key === 'auth-storage' || event.key === 'adminToken' || event.key === null) {
        queryClient.clear();
        setLoading(true);
        void checkAuth();
      }
    };
    const clearInvalidSession = () => {
      queryClient.clear();
      identityRef.current = null;
      setUser(null);
      setLoading(false);
    };
    window.addEventListener('storage', refreshOnStorageChange);
    window.addEventListener('unipath-auth-invalidated', clearInvalidSession);
    void checkAuth();
    return () => {
      checkSequence.current += 1;
      window.removeEventListener('storage', refreshOnStorageChange);
      window.removeEventListener('unipath-auth-invalidated', clearInvalidSession);
    };
  }, [applyUser, queryClient]);

  const login = async (email: string, password: string) => {
    const response = await api.post('/v1/accounts/login/', { email, password });
    const { access: token, user: userData } = response.data;

    if (!MANAGER_ROLES.includes(userData.role) && userData.role !== 'student') {
      throw new Error('Для этого аккаунта нет интерфейса входа.');
    }

    persistSession(token, userData);
    if (MANAGER_ROLES.includes(userData.role)) {
      applyUser(userData);
    } else {
      queryClient.clear();
      identityRef.current = null;
      setUser(null);
    }
    return userData as User;
  };

  const linkMaxProfile = async (initData: string) => {
    const signedInUser = readSharedUser();
    if (!signedInUser) throw new Error('Войдите в аккаунт перед привязкой MAX.');

    const response = await api.post('/max/launch/', { initData });
    const linkedUser = response.data.user as User;
    if (
      linkedUser.id !== signedInUser.id ||
      (!MANAGER_ROLES.includes(linkedUser.role) && linkedUser.role !== 'student')
    ) {
      throw new Error('MAX вернул другую учётную запись. Привязка отменена.');
    }

    const token = response.data.tokens?.access;
    if (token) persistSession(token, linkedUser);
    if (MANAGER_ROLES.includes(linkedUser.role)) {
      applyUser(linkedUser);
    } else {
      queryClient.clear();
      identityRef.current = null;
      setUser(null);
    }
    return linkedUser;
  };

  const logout = () => {
    sessionStorage.setItem('max-launch-suppressed', 'true');
    sessionStorage.removeItem('max-launch-pending');
    queryClient.clear();
    identityRef.current = null;
    localStorage.removeItem('adminToken');
    localStorage.removeItem('auth-storage');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, linkMaxProfile, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

function persistSession(token: string, user: User) {
  localStorage.setItem('adminToken', token);
  localStorage.setItem('auth-storage', JSON.stringify({
    state: { token, user },
    version: 0,
  }));
}

function readSharedToken() {
  try {
    return JSON.parse(localStorage.getItem('auth-storage') || '{}')?.state?.token || null;
  } catch {
    return null;
  }
}

function readSharedUser(): User | null {
  try {
    return JSON.parse(localStorage.getItem('auth-storage') || '{}')?.state?.user || null;
  } catch {
    return null;
  }
}
