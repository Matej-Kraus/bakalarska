import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import { listSeasons } from "@/api/seasons";
import { teamStatsSeason } from "@/api/reports";
import { seasonLeaderboards, playerPerformance } from "@/api/analytics";
import { listPlayers } from "@/api/players";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

function ymd(d: string) {
  return d.length >= 10 ? d.slice(0, 10) : d;
}

export default function AnalyticsPage() {
  const seasonsQuery = useQuery({
    queryKey: ["seasons"],
    queryFn: listSeasons,
    refetchOnWindowFocus: false,
  });

  const playersQuery = useQuery({
    queryKey: ["players"],
    queryFn: listPlayers,
    refetchOnWindowFocus: false,
  });

  const [seasonId, setSeasonId] = useState<number>(1);
  const [playerId, setPlayerId] = useState<number>(1);

  useEffect(() => {
    if (seasonsQuery.data && seasonsQuery.data.length > 0) {
      setSeasonId(seasonsQuery.data[0].id);
    }
  }, [seasonsQuery.data]);

  useEffect(() => {
    if (playersQuery.data && playersQuery.data.length > 0) {
      setPlayerId(playersQuery.data[0].id);
    }
  }, [playersQuery.data]);

  const teamStatsQuery = useQuery({
    queryKey: ["team-stats", seasonId],
    queryFn: () => teamStatsSeason(seasonId),
    enabled: Number.isFinite(seasonId) && seasonId > 0,
    refetchOnWindowFocus: false,
  });

  const leaderboardQuery = useQuery({
    queryKey: ["leaderboards", seasonId],
    queryFn: () => seasonLeaderboards(seasonId),
    enabled: Number.isFinite(seasonId) && seasonId > 0,
    refetchOnWindowFocus: false,
  });

  const perfQuery = useQuery({
    queryKey: ["player-performance", playerId, seasonId],
    queryFn: () => playerPerformance(playerId, seasonId),
    enabled: Number.isFinite(playerId) && playerId > 0 && Number.isFinite(seasonId) && seasonId > 0,
    refetchOnWindowFocus: false,
  });

  const perfChartData = useMemo(() => {
    const rows = perfQuery.data ?? [];
    return rows.map((r) => ({
      date: ymd(r.match_date),
      goals: r.stats.goals,
      assists: r.stats.assists,
      passes: r.stats.passes,
      rating: r.rating ?? null,
    }));
  }, [perfQuery.data]);

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-xl font-semibold">Analytika</div>
          <div className="text-sm text-muted-foreground">
            Souhrny sezóny + vývoj výkonu hráče v čase.
          </div>
        </div>
      </div>

      <Card className="rounded-2xl">
        <CardHeader>
          <CardTitle>Nastavení</CardTitle>
        </CardHeader>
        <CardContent className="p-4 grid gap-3 md:grid-cols-2">
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Sezóna</div>
            {seasonsQuery.isLoading ? (
              <div className="text-sm text-muted-foreground">Načítám…</div>
            ) : (
              <select
                className="w-full rounded-xl border bg-background px-3 py-2 text-sm"
                value={seasonId}
                onChange={(e) => setSeasonId(Number(e.target.value))}
              >
                {(seasonsQuery.data ?? []).map((s) => (
                  <option key={s.id} value={s.id}>
                    #{s.id} {s.name}
                  </option>
                ))}
              </select>
            )}
          </div>

          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Hráč</div>
            {playersQuery.isLoading ? (
              <div className="text-sm text-muted-foreground">Načítám…</div>
            ) : (
              <select
                className="w-full rounded-xl border bg-background px-3 py-2 text-sm"
                value={playerId}
                onChange={(e) => setPlayerId(Number(e.target.value))}
              >
                {(playersQuery.data ?? []).map((p) => (
                  <option key={p.id} value={p.id}>
                    #{p.jersey_number} {p.first_name} {p.last_name} (id {p.id})
                  </option>
                ))}
              </select>
            )}
          </div>
        </CardContent>
      </Card>

      <Card className="rounded-2xl">
        <CardHeader>
          <CardTitle>Týmové statistiky (sezóna)</CardTitle>
        </CardHeader>
        <CardContent className="p-4">
          {teamStatsQuery.isLoading ? (
            <div className="text-sm text-muted-foreground">Načítám…</div>
          ) : teamStatsQuery.data ? (
            <div className="grid gap-2 md:grid-cols-4 text-sm">
              <div className="rounded-xl border p-3">
                <div className="text-xs text-muted-foreground">Zápasy</div>
                <div className="text-lg font-semibold">{teamStatsQuery.data.games}</div>
              </div>
              <div className="rounded-xl border p-3">
                <div className="text-xs text-muted-foreground">Góly</div>
                <div className="text-lg font-semibold">{teamStatsQuery.data.goals}</div>
              </div>
              <div className="rounded-xl border p-3">
                <div className="text-xs text-muted-foreground">Asistence</div>
                <div className="text-lg font-semibold">{teamStatsQuery.data.assists}</div>
              </div>
              <div className="rounded-xl border p-3">
                <div className="text-xs text-muted-foreground">Přihrávky</div>
                <div className="text-lg font-semibold">{teamStatsQuery.data.passes}</div>
              </div>
            </div>
          ) : (
            <div className="text-sm text-muted-foreground">Bez dat.</div>
          )}
        </CardContent>
      </Card>

      <Card className="rounded-2xl">
        <CardHeader>
          <CardTitle>Leaderboard (sezóna)</CardTitle>
        </CardHeader>
        <CardContent className="p-4 space-y-2">
          {leaderboardQuery.isLoading ? (
            <div className="text-sm text-muted-foreground">Načítám…</div>
          ) : (leaderboardQuery.data ?? []).length === 0 ? (
            <div className="text-sm text-muted-foreground">Bez dat.</div>
          ) : (
            <div className="space-y-2">
              {(leaderboardQuery.data ?? []).slice(0, 12).map((r) => (
                <div
                  key={r.player_id}
                  className="flex items-center justify-between gap-3 rounded-xl border p-3"
                >
                  <div className="min-w-0">
                    <div className="truncate font-medium">
                      #{r.jersey_number} {r.first_name} {r.last_name}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Zápasy: {r.games} • Góly: {r.goals} • Asistence: {r.assists} • Přihrávky:{" "}
                      {r.passes} • Avg rating:{" "}
                      {r.avg_rating == null ? "—" : r.avg_rating.toFixed(2)}
                    </div>
                  </div>
                  <div className="text-sm font-semibold">
                    {r.goals}G / {r.assists}A
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="rounded-2xl">
        <CardHeader>
          <CardTitle>Výkon hráče v čase</CardTitle>
        </CardHeader>
        <CardContent className="p-4 space-y-3">
          {perfQuery.isLoading ? (
            <div className="text-sm text-muted-foreground">Načítám…</div>
          ) : perfChartData.length === 0 ? (
            <div className="text-sm text-muted-foreground">Bez dat.</div>
          ) : (
            <>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={perfChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="goals" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="assists" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="passes" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={perfChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis domain={[0, 10]} />
                    <Tooltip />
                    <Line type="monotone" dataKey="rating" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </>
          )}
          <div className="text-xs text-muted-foreground">
            Pozn.: rating je dostupný až po vyplnění „Hodnocení hráčů“ u zápasu.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

