import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, AuthContextType, MANAGER_ROLES } from '@/types';
import api from '@/api/client';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// eslint-disable-next-line react-refresh/only-export-components -- hook lives with its provider by design
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('adminToken');
      if (token) {
        try {
          const response = await api.get('/v1/accounts/me/');
          if (MANAGER_ROLES.includes(response.data.role)) {
            setUser(response.data);
          } else {
            localStorage.removeItem('adminToken');
          }
        } catch (error) {
          localStorage.removeItem('adminToken');
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    const response = await api.post('/v1/accounts/login/', { email, password });
    const { access: token, user: userData } = response.data;

    if (!MANAGER_ROLES.includes(userData.role)) {
      throw new Error('Доступ запрещен. Нужны права администратора или редактора.');
    }

    localStorage.setItem('adminToken', token);
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem('adminToken');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
