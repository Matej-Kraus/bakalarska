import { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/auth/AuthContext";
import * as clubApi from "@/api/club";
import { createSeason, listSeasons } from "@/api/seasons";
import { getActiveSeasonId, onActiveSeasonChange, setActiveSeasonId } from "@/state/season";


const navLinkBase =
  "flex-1 rounded-xl px-2 py-2.5 text-sm font-semibold tracking-wide transition-colors";

function navLinkClass(
  palette: string,
  paletteActive: string,
) {
  return ({ isActive }: { isActive: boolean }) =>
    isActive
      ? `${navLinkBase} ${paletteActive}`
      : `${navLinkBase} ${palette} hover:bg-muted/60`;
}

export default function AppLayout() {
  const auth = useAuth();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [clubName, setClubName] = useState<string | null>(null);
  const [activeSeasonId, setActiveSeasonIdState] = useState<number | null>(() =>
    getActiveSeasonId(),
  );
  const [newSeasonName, setNewSeasonName] = useState("");

  const seasonsQuery = useQuery({
    queryKey: ["seasons"],
    queryFn: listSeasons,
    enabled: !!auth.token,
    refetchOnWindowFocus: false,
  });

  const createSeasonMutation = useMutation({
    mutationFn: createSeason,
    onSuccess: async (s) => {
      await qc.invalidateQueries({ queryKey: ["seasons"] });
      setActiveSeasonId(s.id);
      setNewSeasonName("");
    },
  });

  useEffect(() => {
    if (!auth.token) {
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const c = await clubApi.getClub();
        if (!cancelled) setClubName(c.name);
      } catch {
        if (!cancelled) setClubName(null);
      }
    })();
    const onUpdate = () => {
      clubApi.getClub().then((c) => setClubName(c.name)).catch(() => {});
    };
    window.addEventListener("club-updated", onUpdate);
    return () => {
      cancelled = true;
      window.removeEventListener("club-updated", onUpdate);
    };
  }, [auth.token]);

  useEffect(() => {
    if (!auth.token) return;
    const unsub = onActiveSeasonChange((sid) => setActiveSeasonIdState(sid));
    return unsub;
  }, [auth.token]);

  useEffect(() => {
    if (!seasonsQuery.data || seasonsQuery.data.length === 0) {
      return;
    }
    const existing = getActiveSeasonId();
    if (
      existing &&
      seasonsQuery.data.some((s) => s.id === existing)
    ) {
      return;
    }
    setActiveSeasonId(seasonsQuery.data[0].id);
  }, [seasonsQuery.data]);

  return (
    <div className="flex min-h-screen w-screen flex-col bg-background text-foreground">
      {/* Top app bar */}
      <header className="flex items-center justify-between border-b px-4 py-3">
        <div className="flex flex-col min-w-0">
          <span className="text-base font-semibold truncate">
            {auth.token ? clubName ?? "Coach App" : "Coach App"}
          </span>
          {auth.user && (
            <span className="text-xs text-muted-foreground">
              {auth.user.email} • {auth.user.role}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <select
            className="h-10 rounded-lg border bg-background px-2 text-xs"
            value={activeSeasonId ?? ""}
            onChange={(e) => {
              const sid = Number(e.target.value);
              if (Number.isFinite(sid) && sid > 0) {
                setActiveSeasonId(sid);
              }
            }}
          >
            {(seasonsQuery.data ?? []).map((s) => (
              <option key={s.id} value={s.id}>
                Sezóna: {s.name}
              </option>
            ))}
          </select>
          {auth.user?.role === "coach" && (
            <>
              <Input
                className="h-10 w-36 text-xs"
                placeholder="Nová sezóna"
                value={newSeasonName}
                onChange={(e) => setNewSeasonName(e.target.value)}
              />
              <Button
                variant="outline"
                className="h-10 px-3 text-xs font-medium"
                disabled={!newSeasonName.trim() || createSeasonMutation.isPending}
                onClick={() =>
                  createSeasonMutation.mutate({ name: newSeasonName.trim() })
                }
              >
                Přidat sezónu
              </Button>
            </>
          )}
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
        </div>
      </header>

      {/* Main content - full width; live match page uses its own full-width layout */}
      <main className="flex-1 overflow-y-auto overflow-x-hidden w-full min-w-0">
        <Outlet />
      </main>

      {/* Bottom navigation for touch devices */}
      <nav className="grid grid-cols-4 gap-2 border-t bg-card px-3 py-2">
        <NavLink
          to="/players"
          className={navLinkClass(
            "text-emerald-700 dark:text-emerald-300",
            "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-200",
          )}
        >
          Hráči
        </NavLink>
        <NavLink
          to="/matches"
          className={navLinkClass(
            "text-blue-700 dark:text-blue-300",
            "bg-blue-100 text-blue-800 dark:bg-blue-950/40 dark:text-blue-200",
          )}
        >
          Zápasy
        </NavLink>
        <NavLink
          to="/analytics"
          className={navLinkClass(
            "text-violet-700 dark:text-violet-300",
            "bg-violet-100 text-violet-800 dark:bg-violet-950/40 dark:text-violet-200",
          )}
        >
          Analytika
        </NavLink>
        <NavLink
          to="/club"
          className={navLinkClass(
            "text-amber-700 dark:text-amber-300",
            "bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-200",
          )}
        >
          Klub
        </NavLink>
      </nav>
    </div>
  );
}