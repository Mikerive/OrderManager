import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { ThemeProvider, createTheme } from '@mui/material';
import { Layout } from './components/Layout/Layout';
import { AuthProvider, useAuth } from './features/user_management/context/AuthContext';
import { AuthPage } from './features/user_management/pages/AuthPage';
import { OrderManagementPage } from './features/order_management/pages/OrderManagementPage';
import { DiscordIntegrationPage } from './features/discord_integration/pages/DiscordIntegrationPage';

const queryClient = new QueryClient();

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  
  if (!user) {
    return <Navigate to="/auth" replace />;
  }

  return <>{children}</>;
};

const AppRoutes: React.FC = () => {
  return (
    <Routes>
      <Route path="/auth" element={<AuthPage />} />
      <Route
        path="/orders"
        element={
          <ProtectedRoute>
            <OrderManagementPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/discord"
        element={
          <ProtectedRoute>
            <DiscordIntegrationPage />
          </ProtectedRoute>
        }
      />
      <Route path="/" element={<Navigate to="/orders" replace />} />
    </Routes>
  );
};

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <AuthProvider>
          <Router>
            <Layout>
              <AppRoutes />
            </Layout>
          </Router>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

export default App;
