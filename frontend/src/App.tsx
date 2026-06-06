import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import { AuthProvider } from './lib/AuthContext'
import { ProtectedRoute } from './lib/ProtectedRoute'
import { AppShell } from './components/layout/AppShell'
import { HomePage } from './pages/HomePage'
import { ReportsPage } from './pages/ReportsPage'
import { NewsPage } from './pages/NewsPage'
import { PriceTrendPage } from './pages/PriceTrendPage'
import { WorkflowPage } from './pages/WorkflowPage'
import { KeywordTrackingPage } from './pages/KeywordTrackingPage'
import { AccountPage } from './pages/AccountPage'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 1 },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route element={<ProtectedRoute />}>
              <Route element={<AppShell />}>
                <Route path="/" element={<HomePage />} />
                <Route path="/reports" element={<ReportsPage />} />
                <Route path="/topic-analysis" element={<Navigate to="/reports" replace />} />
                <Route path="/news" element={<NewsPage />} />
                <Route path="/price-trend" element={<PriceTrendPage />} />
                <Route path="/workflow" element={<WorkflowPage />} />
                <Route path="/keyword-tracking" element={<KeywordTrackingPage />} />
                <Route path="/account" element={<AccountPage />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Route>
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
      <Toaster position="top-right" richColors closeButton />
    </QueryClientProvider>
  )
}
