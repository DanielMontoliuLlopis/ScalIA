import { useEffect } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { useAuthStore } from "./store/authStore";
import { Layout } from "./components/ui/Layout";
import { NewCampaign } from "./pages/NewCampaign";
import { PlanWorkspace } from "./pages/PlanWorkspace";
import { Dashboard } from "./pages/Dashboard";
import { Home } from "./pages/Home";
import { Login } from "./pages/Login";
import { Register } from "./pages/Register";
import { Settings } from "./pages/Settings";
import { Campaigns } from "./pages/Campaigns";
import { ResearchLibrary } from "./pages/ResearchLibrary";
import { ClientAccounts } from "./pages/ClientAccounts";
import { LandingPage, LandingThanks } from "./pages/LandingPage";
import { MetaCallback } from "./pages/MetaCallback";
import { Onboarding } from "./pages/Onboarding";
import { BillingSuccess } from "./pages/BillingSuccess";
import { Admin } from "./pages/Admin";
import { CloserLogin } from "./pages/CloserLogin";
import { CloserDashboard } from "./pages/CloserDashboard";
import { useCloserAuthStore } from "./store/closerAuthStore";

const ACTIVE_STATUSES = new Set(["trialing", "active", "past_due"]);

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { token } = useAuthStore();
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function RequireAdmin({ children }: { children: React.ReactNode }) {
  const { token, user } = useAuthStore();
  if (!token) return <Navigate to="/login" replace />;
  if (!user) return null;
  if (!user.is_superadmin) return <Navigate to="/" replace />;
  return <>{children}</>;
}

function RequireCloser({ children }: { children: React.ReactNode }) {
  const { token } = useCloserAuthStore();
  if (!token) return <Navigate to="/closer/login" replace />;
  return <>{children}</>;
}

function RequireSubscription({ children }: { children: React.ReactNode }) {
  const { token, user } = useAuthStore();
  if (!token) return <Navigate to="/login" replace />;
  if (!user) return null;
  if (!ACTIVE_STATUSES.has(user.subscription_status ?? "")) {
    return <Navigate to="/onboarding/plan" replace />;
  }
  return <>{children}</>;
}

export default function App() {
  const { token, fetchMe } = useAuthStore();

  useEffect(() => {
    if (token) fetchMe();
  }, [token]);

  // Captura el código de referido del closer (link /?ref=CODE) y lo persiste
  // hasta el registro.
  useEffect(() => {
    const ref = new URLSearchParams(window.location.search).get("ref");
    if (ref) localStorage.setItem("ref_code", ref);
  }, []);

  return (
    <BrowserRouter>
      <Routes>
        {/* Landing pública en raíz */}
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        {/* Onboarding y billing (autenticado pero sin suscripción) */}
        <Route
          path="/onboarding/plan"
          element={
            <RequireAuth>
              <Onboarding />
            </RequireAuth>
          }
        />
        <Route
          path="/billing/success"
          element={
            <RequireAuth>
              <BillingSuccess />
            </RequireAuth>
          }
        />
        {/* Rutas públicas de landing de campañas — sin auth */}
        <Route path="/meta/callback" element={<MetaCallback />} />
        <Route path="/landing/:id" element={<LandingPage />} />
        <Route path="/landing/:id/thanks" element={<LandingThanks />} />
        {/* App protegida (requiere suscripción activa) */}
        <Route
          element={
            <RequireSubscription>
              <Layout />
            </RequireSubscription>
          }
        >
          <Route path="/campaigns/new" element={<NewCampaign />} />
          <Route path="/plan/:planId" element={<PlanWorkspace />} />
          <Route path="/research" element={<ResearchLibrary />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/campaigns" element={<Campaigns />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/clients" element={<ClientAccounts />} />
        </Route>
        {/* Panel de administración de plataforma — solo superadmins */}
        <Route
          path="/admin"
          element={
            <RequireAdmin>
              <Admin />
            </RequireAdmin>
          }
        />
        {/* Portal del closer — sesión independiente */}
        <Route path="/closer/login" element={<CloserLogin />} />
        <Route
          path="/closer"
          element={
            <RequireCloser>
              <CloserDashboard />
            </RequireCloser>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
