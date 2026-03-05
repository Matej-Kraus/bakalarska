import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import { useNavigate } from "react-router-dom";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/api/client";
import { useAuth } from "@/auth/AuthContext";
import { exportMatchEventsCsv } from "@/api/matches";
import { downloadBlob } from "@/utils/download";

type Match = {
  id: number;
  opponent: string;
  competition: string;
  match_date: string;
  status: string;
  season_id: number;
};

function getErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const data = err.response?.data;
    if (typeof data === "object" && data !== null && "detail" in data) {
      const detail = (data as { detail?: unknown }).detail;
      if (typeof detail === "string") return detail;
      if (detail != null) return JSON.stringify(detail);
    }
    return err.message;
  }
  if (err instanceof Error) return err.message;
  return "Unknown error";
}

export default function MatchesPage() {
  const navigate = useNavigate();
  const auth = useAuth();
  const isCoach = auth.user?.role === "coach";


  const [opponent, setOpponent] = useState("Sparta");
  const [competition, setCompetition] = useState("Liga");
  const [matchDate, setMatchDate] = useState("2026-02-23T18:00:00");
  const [seasonId, setSeasonId] = useState<number>(1);
  const [err, setErr] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  const { data: matches, isLoading } = useQuery({
    queryKey: ["matches"],
    queryFn: async () => {
      const res = await api.get("/matches");
      return res.data as Match[];
    },
  });

  const sorted = useMemo(() => {
    return [...(matches ?? [])].sort((a, b) => b.id - a.id);
  }, [matches]);

  async function createMatch() {
    try {
      setErr(null);
      setCreating(true);

      // Backend musí mít POST /matches (ty už ho zjevně máš podle Swaggeru).
      const res = await api.post("/matches", {
        season_id: seasonId,
        opponent,
        competition,
        match_date: matchDate,
      });

      const newId = Number((res.data as { id?: unknown }).id);

      if (!Number.isFinite(newId)) {
        setErr(`Backend nevrátil id. Odpověď: ${JSON.stringify(res.data)}`);
        return;
      }

      navigate(`/matches/${newId}/lineup`);
    } catch (e: unknown) {
      setErr(getErrorMessage(e));
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="p-6 space-y-4">
      <Card className="rounded-2xl">
        <CardHeader>
          <CardTitle>Zápasy</CardTitle>
        </CardHeader>

        <CardContent className="space-y-3">
          {err && (
            <div className="rounded-xl border border-destructive p-3 text-sm text-destructive">
              {err}
            </div>
          )}

          <div className="grid gap-3 md:grid-cols-4">
            <div className="space-y-1">
              <div className="text-xs text-muted-foreground">Soupeř</div>
              <Input value={opponent} onChange={(e) => setOpponent(e.target.value)} />
            </div>

            <div className="space-y-1">
              <div className="text-xs text-muted-foreground">Soutěž</div>
              <Input value={competition} onChange={(e) => setCompetition(e.target.value)} />
            </div>

            <div className="space-y-1">
              <div className="text-xs text-muted-foreground">Datum/čas (ISO)</div>
              <Input value={matchDate} onChange={(e) => setMatchDate(e.target.value)} />
            </div>

            <div className="space-y-1">
              <div className="text-xs text-muted-foreground">Sezóna ID</div>
              <Input
                value={String(seasonId)}
                inputMode="numeric"
                onChange={(e) => setSeasonId(Number(e.target.value || 1))}
              />
            </div>
          </div>

          <div className="flex gap-2">
            <Button onClick={createMatch} disabled={!isCoach || creating}>
              Vytvořit zápas → Sestava
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card className="rounded-2xl">
        <CardHeader>
          <CardTitle>Seznam zápasů</CardTitle>
        </CardHeader>

        <CardContent className="space-y-2">
          {isLoading ? (
            <div className="text-sm text-muted-foreground">Načítám…</div>
          ) : sorted.length === 0 ? (
            <div className="text-sm text-muted-foreground">Zatím žádné zápasy.</div>
          ) : (
            sorted.map((m) => (
              <div
                key={m.id}
                className="flex items-center justify-between gap-3 rounded-xl border p-3"
              >
                <div className="min-w-0">
                  <div className="truncate font-medium">
                    #{m.id} vs {m.opponent}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {m.competition} • {m.match_date} • {m.status}
                  </div>
                </div>

                <div className="flex gap-2">
                  <Button variant="outline" onClick={() => navigate(`/matches/${m.id}/lineup`)}>
                    Sestava
                  </Button>
                  <Button
                    onClick={() =>
                      navigate(
                        m.status === "finished"
                          ? `/matches/${m.id}/evaluation`
                          : `/matches/${m.id}/live`,
                      )
                    }
                  >
                    {m.status === "finished" ? "Report" : "Live"}
                  </Button>
                  {isCoach && (
                    <Button
                      variant="outline"
                      onClick={async () => {
                        const blob = await exportMatchEventsCsv(m.id);
                        downloadBlob(blob, `match_${m.id}_events.csv`);
                      }}
                    >
                      Export events
                    </Button>
                  )}
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}