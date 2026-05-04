import type { ReactNode } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import PlayersPage from "./pages/PlayersPage";
import MatchesPage from "./pages/MatchesPage";
import LineupPage from "./pages/LineupPage";
import LiveMatchPage from "./pages/LiveMatchPage";
import MatchEvaluationPage from "./pages/MatchEvaluationPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import ClubSettingsPage from "./pages/ClubSettingsPage";
import LoginPage from "./pages/LoginPage";
import { useAuth } from "./auth/AuthContext";

function RequireAuth({ children }: { children: ReactNode }) {
  const auth = useAuth();
  if (auth.loading) {
    return <div className="p-6 text-sm text-muted-foreground">Načítám…</div>;
  }
  if (!auth.token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route
        element={
          <RequireAuth>
            <AppLayout />
          </RequireAuth>
        }
      >
        <Route path="/players" element={<PlayersPage />} />
        <Route path="/matches" element={<MatchesPage />} />
        <Route path="/matches/:matchId/lineup" element={<LineupPage />} />
        <Route path="/matches/:matchId/live" element={<LiveMatchPage />} />
        <Route path="/matches/:matchId/evaluation" element={<MatchEvaluationPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/club" element={<ClubSettingsPage />} />

        <Route path="*" element={<Navigate to="/players" replace />} />
      </Route>
    </Routes>
  );
}