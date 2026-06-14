import { BrowserRouter, Navigate, Route, Routes, useParams } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import { AuthProvider } from './lib/AuthContext'
import { ProtectedRoute } from './lib/ProtectedRoute'
import { AppShell } from './components/layout/AppShell'
import { ChatProvider } from './features/chat/ChatProvider'
import { HomePage } from './pages/HomePage'
import { ReportsPage } from './pages/ReportsPage'
import { NewsPage } from './pages/NewsPage'
import { PriceTrendPage } from './pages/PriceTrendPage'
import { WorkflowPage } from './pages/WorkflowPage'
import { KeywordTrackingPage } from './pages/KeywordTrackingPage'
import { AccountPage } from './pages/AccountPage'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { LandingOrRedirect } from './pages/LandingOrRedirect'
import { OnboardingProvider } from './features/onboarding/OnboardingProvider'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 1 },
  },
})

const legacyRedirects = [
  '/reports',
  '/news',
  '/price-trend',
  '/workflow',
  '/keyword-tracking',
  '/account',
  '/topic-analysis',
] as const

function LegacyReportDetailRedirect() {
  const { id } = useParams<{ id: string }>()
  return <Navigate to={`/app/reports?open=${encodeURIComponent(id!)}`} replace />
}

function LegacyNewsDetailRedirect() {
  const { id } = useParams<{ id: string }>()
  return <Navigate to={`/app/news?open=${encodeURIComponent(id!)}`} replace />
}

function ReportDetailOpenRedirect() {
  const { id } = useParams<{ id: string }>()
  return <Navigate to={`/app/reports?open=${encodeURIComponent(id!)}`} replace />
}

function NewsDetailOpenRedirect() {
  const { id } = useParams<{ id: string }>()
  return <Navigate to={`/app/news?open=${encodeURIComponent(id!)}`} replace />
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<LandingOrRedirect />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            {legacyRedirects.map((from) => (
              <Route
                key={from}
                path={from}
                element={<Navigate to={`/app${from === '/topic-analysis' ? '/reports' : from}`} replace />}
              />
            ))}
            <Route path="/reports/:id" element={<LegacyReportDetailRedirect />} />
            <Route path="/news/:id" element={<LegacyNewsDetailRedirect />} />
            <Route element={<ProtectedRoute />}>
              <Route element={<OnboardingProvider><ChatProvider><AppShell /></ChatProvider></OnboardingProvider>}>
                <Route path="/app" element={<HomePage />} />
                <Route path="/app/reports" element={<ReportsPage />} />
                <Route path="/app/reports/:id" element={<ReportDetailOpenRedirect />} />
                <Route path="/app/topic-analysis" element={<Navigate to="/app/reports" replace />} />
                <Route path="/app/news" element={<NewsPage />} />
                <Route path="/app/news/:id" element={<NewsDetailOpenRedirect />} />
                <Route path="/app/price-trend" element={<PriceTrendPage />} />
                <Route path="/app/workflow" element={<WorkflowPage />} />
                <Route path="/app/keyword-tracking" element={<KeywordTrackingPage />} />
                <Route path="/app/account" element={<AccountPage />} />
                <Route path="*" element={<Navigate to="/app" replace />} />
              </Route>
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
      <Toaster position="top-right" richColors closeButton />
    </QueryClientProvider>
  )
}
