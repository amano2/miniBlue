import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuthStore } from './lib/store';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';

// Pages
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { ChatPage } from './pages/ChatPage';
import { RequestsPage } from './pages/RequestsPage';
import { ReviewsPage } from './pages/ReviewsPage';
import { SimulatorPage } from './pages/SimulatorPage';
import { AuditPage } from './pages/AuditPage';
import { PoliciesPage } from './pages/PoliciesPage';
import { EvaluationPage } from './pages/EvaluationPage';
import { UsersPage } from './pages/UsersPage';
import { UserRole } from './types';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,
      retry: 1,
    },
  },
});

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: UserRole[];
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, allowedRoles }) => {
  const { isAuthenticated, user } = useAuthStore();

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    // If unauthorized, redirect to employee home (/chat) or dashboard
    return <Navigate to={user.role === 'employee' ? '/chat' : '/dashboard'} replace />;
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-obsidian-950 font-sans text-slate-100">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto p-6 relative">
          {children}
        </main>
      </div>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          {/* Chat Route (All Roles) */}
          <Route
            path="/chat"
            element={
              <ProtectedRoute allowedRoles={['employee', 'manager', 'admin', 'auditor']}>
                <ChatPage />
              </ProtectedRoute>
            }
          />

          {/* My Requests / Action Ledger (All Roles) */}
          <Route
            path="/requests"
            element={
              <ProtectedRoute allowedRoles={['employee', 'manager', 'admin', 'auditor']}>
                <RequestsPage />
              </ProtectedRoute>
            }
          />

          {/* Observability Dashboard (Manager, Admin, Auditor) */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute allowedRoles={['manager', 'admin', 'auditor']}>
                <DashboardPage />
              </ProtectedRoute>
            }
          />

          {/* HITL Review Inbox (Manager, Admin) */}
          <Route
            path="/reviews"
            element={
              <ProtectedRoute allowedRoles={['manager', 'admin']}>
                <ReviewsPage />
              </ProtectedRoute>
            }
          />

          {/* Policy Counterfactual Simulator (Admin) */}
          <Route
            path="/simulator"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <SimulatorPage />
              </ProtectedRoute>
            }
          />

          {/* Cryptographic Audit Ledger (Admin, Auditor) */}
          <Route
            path="/audit"
            element={
              <ProtectedRoute allowedRoles={['admin', 'auditor']}>
                <AuditPage />
              </ProtectedRoute>
            }
          />

          {/* Policy Knowledge Base (All Roles) */}
          <Route
            path="/policies"
            element={
              <ProtectedRoute allowedRoles={['employee', 'manager', 'admin', 'auditor']}>
                <PoliciesPage />
              </ProtectedRoute>
            }
          />

          {/* Automated Evaluation Harness (Admin, Auditor) */}
          <Route
            path="/evaluation"
            element={
              <ProtectedRoute allowedRoles={['admin', 'auditor']}>
                <EvaluationPage />
              </ProtectedRoute>
            }
          />

          {/* User Management (Admin) */}
          <Route
            path="/users"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <UsersPage />
              </ProtectedRoute>
            }
          />

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
