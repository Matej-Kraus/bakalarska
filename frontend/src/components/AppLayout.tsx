import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/auth/AuthContext";


const navLinkBase =
  "flex-1 flex items-center justify-center text-xs font-medium uppercase tracking-wide";

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  `${navLinkBase} ${isActive ? "text-primary" : "text-muted-foreground"}`;

export default function AppLayout() {
  const auth = useAuth();
  const navigate = useNavigate();

  return (
    <div className="flex min-h-screen w-screen flex-col bg-background text-foreground">
      {/* Top app bar */}
      <header className="flex items-center justify-between border-b px-4 py-3">
        <div className="flex flex-col">
          <span className="text-base font-semibold">Coach App</span>
          {auth.user && (
            <span className="text-xs text-muted-foreground">
              {auth.user.email} • {auth.user.role}
            </span>
          )}
        </div>

        <Button
          variant="outline"
          className="h-10 px-4 text-xs font-medium"
          onClick={() => {
            auth.logout();
            navigate("/login", { replace: true });
          }}
        >
          Odhlásit
        </Button>
      </header>

      {/* Main content - full width; live match page uses its own full-width layout */}
      <main className="flex-1 overflow-y-auto overflow-x-hidden w-full min-w-0">
        <Outlet />
      </main>

      {/* Bottom navigation for touch devices */}
      <nav className="flex border-t bg-card">
        <NavLink to="/players" className={navLinkClass}>
          Hráči
        </NavLink>
        <NavLink to="/matches" className={navLinkClass}>
          Zápasy
        </NavLink>
        <NavLink to="/analytics" className={navLinkClass}>
          Analytika
        </NavLink>
      </nav>
    </div>
  );
}