import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from '@/contexts/AuthContext';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { Layout } from '@/components/Layout';
import { ToastProvider } from '@/ui';
import { Login } from '@/pages/Login';
import { Dashboard } from '@/pages/Dashboard';
import { KnowledgeBase } from '@/pages/KnowledgeBase';
import { Opportunities } from '@/pages/Opportunities';
import { CareerRoles } from '@/pages/CareerRoles';
import { Analytics } from '@/pages/Analytics';
import { Users } from '@/pages/Users';

function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              path="/*"
              element={
                <ProtectedRoute>
                  <Layout>
                    <Routes>
                      <Route path="/" element={<Dashboard />} />
                      <Route path="/knowledge" element={<KnowledgeBase />} />
                      <Route path="/opportunities" element={<Opportunities />} />
                      <Route path="/career-roles" element={<CareerRoles />} />
                      <Route path="/analytics" element={<Analytics />} />
                      <Route path="/users" element={<Users />} />
                      <Route path="*" element={<Navigate to="/" replace />} />
                    </Routes>
                  </Layout>
                </ProtectedRoute>
              }
            />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ToastProvider>
  );
}

export default App;
