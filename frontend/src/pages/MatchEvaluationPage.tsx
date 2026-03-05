import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/auth/AuthContext";
import { useLiveMatchData, getErrorMessage } from "@/features/live-match/useLiveMatchData";
import type { PlayerStats } from "@/api/types";
import type { RatingRow } from "@/api/ratings";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

function clamp(v: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, v));
}

function computeAutoRating(stats: PlayerStats): number {
  const positive =
    stats.goals * 5 +
    stats.assists * 3 +
    stats.shots_on_goal * 1.5 +
    stats.shots_off_goal * 0.5 +
    stats.passes * 0.05 +
    stats.won_duels * 0.7 +
    stats.won_balls * 0.5 +
    stats.penalties * 2;

  const negative =
    stats.errors * 2 +
    stats.lost_balls * 0.5 +
    stats.lost_duels * 0.7 +
    stats.fouls * 0.5 +
    stats.yellow_cards * 1.5 +
    stats.red_cards * 4;

  const score = positive - negative;

  // Map raw score into 1–10 range (soft caps).
  const rawMin = -5;
  const rawMax = 15;
  const norm = (score - rawMin) / (rawMax - rawMin);
  const scaled = 1 + 9 * clamp(norm, 0, 1);
  return Math.round(scaled * 10) / 10; // one decimal
}

type RatingsDraft = Record<number, { rating: string; note: string }>;

type TimelineBucket = {
  bucketIndex: number;
  startMinute: number;
  endMinute: number;
  minute: number;
  label: string;
  total: number;
  passes: number;
  shots: number;
  duels: number;
  fouls: number;
  goals: number;
  yellowCards: number;
  redCards: number;
};

export default function MatchEvaluationPage() {
  const navigate = useNavigate();
  const auth = useAuth();
  const isCoach = auth.user?.role === "coach";

  const { matchId: matchIdParam } = useParams();
  const matchId = Number(matchIdParam);
  const isValidMatchId = Number.isFinite(matchId) && matchId > 0;

  const [error, setError] = useState<string | null>(null);
  const [ratingsDraft, setRatingsDraft] = useState<RatingsDraft>({});

  const {
    match,
    roster,
    ratings,
    substitutions,
    ratingsQuery,
    saveRatingsMutation,
    eventsQuery,
  } = useLiveMatchData(matchId, isValidMatchId);

  // Determine which players actually played: starters + any player who ever came in as a substitute.
  const { playedRoster, autoRatings, playedIds } = useMemo(() => {
    const starters = roster.filter((r) => r.role === "starter");
    const played = new Set<number>(starters.map((r) => r.player_id));
    substitutions.forEach((s) => {
      played.add(s.player_in_id);
    });

    const pr = roster.filter((r) => played.has(r.player_id));
    const auto: Record<number, number> = {};
    pr.forEach((p) => {
      auto[p.player_id] = computeAutoRating(p.stats);
    });
    return { playedRoster: pr, autoRatings: auto, playedIds: played };
  }, [roster, substitutions]);

  const teamTotals = useMemo(() => {
    const base = {
      goals: 0,
      assists: 0,
      errors: 0,
      won_balls: 0,
      lost_balls: 0,
      fouls: 0,
      passes: 0,
      won_duels: 0,
      lost_duels: 0,
      shots_on_goal: 0,
      shots_off_goal: 0,
      yellow_cards: 0,
      red_cards: 0,
      penalties: 0,
    };

    roster.forEach((r) => {
      const s = r.stats;
      base.goals += s.goals;
      base.assists += s.assists;
      base.errors += s.errors;
      base.won_balls += s.won_balls;
      base.lost_balls += s.lost_balls;
      base.fouls += s.fouls;
      base.passes += s.passes;
      base.won_duels += s.won_duels;
      base.lost_duels += s.lost_duels;
      base.shots_on_goal += s.shots_on_goal;
      base.shots_off_goal += s.shots_off_goal;
      base.yellow_cards += s.yellow_cards;
      base.red_cards += s.red_cards;
      base.penalties += s.penalties;
    });

    const shotsTotal = base.shots_on_goal + base.shots_off_goal;
    const duelsTotal = base.won_duels + base.lost_duels;
    const shotAccuracy = shotsTotal > 0 ? base.shots_on_goal / shotsTotal : null;
    const duelSuccess = duelsTotal > 0 ? base.won_duels / duelsTotal : null;
    const teamActionsForShare =
      base.passes +
      shotsTotal +
      duelsTotal +
      base.won_balls +
      base.lost_balls +
      base.fouls;

    return {
      ...base,
      shotsTotal,
      duelsTotal,
      shotAccuracy,
      duelSuccess,
      teamActionsForShare,
    };
  }, [roster]);

  const events = eventsQuery.data ?? [];

  const timeline = useMemo(() => {
    const BUCKET_SECONDS = 5 * 60;

    if (!events || events.length === 0) {
      return [] as TimelineBucket[];
    }

    let maxBucketIndex = -1;
    events.forEach((ev) => {
      // Only count +1 events; -1 is typically undo in UI
      if (ev.delta <= 0) return;
      const idx = Math.floor(ev.second_in_match / BUCKET_SECONDS);
      if (idx > maxBucketIndex) maxBucketIndex = idx;
    });

    if (maxBucketIndex < 0) {
      return [] as TimelineBucket[];
    }

    const buckets: TimelineBucket[] = [];
    for (let i = 0; i <= maxBucketIndex; i += 1) {
      const startMinute = (i * BUCKET_SECONDS) / 60;
      const endMinute = ((i + 1) * BUCKET_SECONDS) / 60;
      buckets.push({
        bucketIndex: i,
        startMinute,
        endMinute,
        minute: startMinute,
        label: `${startMinute}-${endMinute}'`,
        total: 0,
        passes: 0,
        shots: 0,
        duels: 0,
        fouls: 0,
        goals: 0,
        yellowCards: 0,
        redCards: 0,
      });
    }

    events.forEach((ev) => {
      if (ev.delta <= 0) return;
      const idx = Math.floor(ev.second_in_match / BUCKET_SECONDS);
      const bucket = buckets[idx];
      if (!bucket) return;

      bucket.total += 1;
      switch (ev.event_type) {
        case "pass":
          bucket.passes += 1;
          break;
        case "shot_on_goal":
        case "shot_off_goal":
          bucket.shots += 1;
          break;
        case "won_duel":
        case "lost_duel":
          bucket.duels += 1;
          break;
        case "foul":
          bucket.fouls += 1;
          break;
        case "goal":
          bucket.goals += 1;
          break;
        case "yellow_card":
          bucket.yellowCards += 1;
          break;
        case "red_card":
          bucket.redCards += 1;
          break;
        default:
          break;
      }
    });

    return buckets;
  }, [events]);

  const topPerformers = useMemo(() => {
    if (roster.length === 0) {
      return {
        mostPasses: null as (typeof roster)[number] | null,
        mostDuelsWon: null as (typeof roster)[number] | null,
        mostShots: null as (typeof roster)[number] | null,
      };
    }

    const mostPasses = [...roster].sort(
      (a, b) => b.stats.passes - a.stats.passes,
    )[0];

    const mostDuelsWon = [...roster].sort(
      (a, b) => b.stats.won_duels - a.stats.won_duels,
    )[0];

    const mostShots = [...roster].sort(
      (a, b) =>
        b.stats.shots_on_goal +
        b.stats.shots_off_goal -
        (a.stats.shots_on_goal + a.stats.shots_off_goal),
    )[0];

    return { mostPasses, mostDuelsWon, mostShots };
  }, [roster]);

  // Initialize manual ratings draft from existing ratings (only for players who actually played).
  useEffect(() => {
    if (!isValidMatchId) return;
    if (playedRoster.length === 0) return;
    if (Object.keys(ratingsDraft).length > 0) return;

    const existing = new Map<number, { rating: number; note?: string | null }>();
    (ratings as RatingRow[] | undefined)?.forEach((r) =>
      existing.set(r.player_id, { rating: r.rating, note: r.note ?? null }),
    );

    const init: RatingsDraft = {};
    playedRoster.forEach((p) => {
      const found = existing.get(p.player_id);
      init[p.player_id] = {
        rating: found ? String(found.rating) : "",
        note: found?.note ?? "",
      };
    });
    setRatingsDraft(init);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isValidMatchId, playedRoster, ratings]);

  if (!isValidMatchId) {
    return (
      <div className="p-6 space-y-3">
        <div className="text-lg font-semibold">Hodnocení zápasu</div>
        <div className="text-sm text-muted-foreground">
          Chybí nebo je špatný parametr <code>match_id</code> v URL.
        </div>
        <Button variant="secondary" onClick={() => navigate("/matches")}>
          Zpět na zápasy
        </Button>
      </div>
    );
  }

  if (match && match.status !== "finished") {
    return (
      <div className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-lg font-semibold">Hodnocení zápasu</div>
            <div className="text-sm text-muted-foreground">
              Zápas ID: {match.id} ještě není ukončen. Nejprve ukonči zápas na obrazovce Live.
            </div>
          </div>
          <Button onClick={() => navigate(`/matches/${match.id}/live`)}>Přejít na Live</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full min-h-screen px-4 py-4 space-y-6 md:px-6 md:py-6">
      <div className="flex items-center justify-between gap-3">
        <div className="flex flex-col">
          <div className="text-lg font-semibold">Hodnocení zápasu</div>
          <div className="text-xs text-muted-foreground">
            Zápas ID: {matchId} • Stav: {match?.status ?? "Načítám…"}
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => navigate("/matches")}>
            Zpět na zápasy
          </Button>
        </div>
      </div>

      {error && (
        <Card className="w-full rounded-2xl border-destructive">
          <CardContent className="p-4 text-sm text-destructive">{error}</CardContent>
        </Card>
      )}

      <Card className="w-full rounded-2xl">
        <CardHeader>
          <CardTitle>Průběh zápasu v čase</CardTitle>
        </CardHeader>
        <CardContent className="p-4 space-y-3">
          {eventsQuery.isLoading ? (
            <div className="text-sm text-muted-foreground">Načítám časovou osu…</div>
          ) : timeline.length === 0 ? (
            <div className="text-sm text-muted-foreground">
              Pro tento zápas zatím nejsou žádné zaznamenané události.
            </div>
          ) : (
            <div className="space-y-6">
              <div className="space-y-2">
                <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Celková intenzita (všechny akce)
                </div>
                <div className="h-56">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={timeline}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis
                        dataKey="minute"
                        tickFormatter={(v) => `${v}'`}
                        allowDecimals={false}
                      />
                      <YAxis allowDecimals={false} />
                      <Tooltip
                        labelFormatter={(v) => `${v}.–${v + 5}. minuta`}
                      />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="total"
                        name="Akce celkem"
                        stroke="#0f766e"
                        strokeWidth={2}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="grid gap-6 lg:grid-cols-2">
                <div className="space-y-2">
                  <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Přihrávky a souboje
                  </div>
                  <div className="h-56">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={timeline}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                          dataKey="minute"
                          tickFormatter={(v) => `${v}'`}
                          allowDecimals={false}
                        />
                        <YAxis allowDecimals={false} />
                        <Tooltip labelFormatter={(v) => `${v}.–${v + 5}. minuta`} />
                        <Legend />
                        <Line
                          type="monotone"
                          dataKey="passes"
                          name="Přihrávky"
                          stroke="#2563eb"
                          strokeWidth={2}
                          dot={false}
                        />
                        <Line
                          type="monotone"
                          dataKey="duels"
                          name="Souboje"
                          stroke="#f97316"
                          strokeWidth={2}
                          dot={false}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Střely a góly
                  </div>
                  <div className="h-56">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={timeline}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                          dataKey="minute"
                          tickFormatter={(v) => `${v}'`}
                          allowDecimals={false}
                        />
                        <YAxis allowDecimals={false} />
                        <Tooltip labelFormatter={(v) => `${v}.–${v + 5}. minuta`} />
                        <Legend />
                        <Line
                          type="monotone"
                          dataKey="shots"
                          name="Střely"
                          stroke="#7c3aed"
                          strokeWidth={2}
                          dot={false}
                        />
                        <Line
                          type="monotone"
                          dataKey="goals"
                          name="Góly"
                          stroke="#22c55e"
                          strokeWidth={2}
                          dot={false}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Fauly a karty
                </div>
                <div className="h-56">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={timeline}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis
                        dataKey="minute"
                        tickFormatter={(v) => `${v}'`}
                        allowDecimals={false}
                      />
                      <YAxis allowDecimals={false} />
                      <Tooltip labelFormatter={(v) => `${v}.–${v + 5}. minuta`} />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="fouls"
                        name="Fauly"
                        stroke="#64748b"
                        strokeWidth={2}
                        dot={false}
                      />
                      <Line
                        type="monotone"
                        dataKey="yellowCards"
                        name="Žluté karty"
                        stroke="#facc15"
                        strokeWidth={2}
                        dot={false}
                      />
                      <Line
                        type="monotone"
                        dataKey="redCards"
                        name="Červené karty"
                        stroke="#ef4444"
                        strokeWidth={2}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          )}
          <div className="text-xs text-muted-foreground">
            Intervaly po 5 minutách, počítají se pouze přidání událostí (+1), ne rušení.
          </div>
        </CardContent>
      </Card>

      <Card className="w-full rounded-2xl">
        <CardHeader>
          <CardTitle>Týmové statistiky v zápase</CardTitle>
        </CardHeader>
        <CardContent className="p-4 space-y-3">
          {roster.length === 0 ? (
            <div className="text-sm text-muted-foreground">
              Zatím nejsou k dispozici žádné statistiky. Ujisti se, že byla nastavena sestava a
              zaznamenány události.
            </div>
          ) : (
            <>
              <div className="rounded-xl border">
                <div className="border-b px-4 py-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Přehled týmu
                </div>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Statistika</TableHead>
                        <TableHead className="text-right">Hodnota</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      <TableRow>
                        <TableCell>Góly</TableCell>
                        <TableCell className="text-right">{teamTotals.goals}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Asistence</TableCell>
                        <TableCell className="text-right">{teamTotals.assists}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Střely (na / mimo)</TableCell>
                        <TableCell className="text-right">
                          {teamTotals.shots_on_goal} / {teamTotals.shots_off_goal}
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Přesnost střel</TableCell>
                        <TableCell className="text-right">
                          {teamTotals.shotAccuracy == null
                            ? "—"
                            : `${Math.round(teamTotals.shotAccuracy * 100)} %`}
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Přihrávky</TableCell>
                        <TableCell className="text-right">{teamTotals.passes}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Souboje (vyhrané / prohrané)</TableCell>
                        <TableCell className="text-right">
                          {teamTotals.won_duels} / {teamTotals.lost_duels}
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Úspěšnost v soubojích</TableCell>
                        <TableCell className="text-right">
                          {teamTotals.duelSuccess == null
                            ? "—"
                            : `${Math.round(teamTotals.duelSuccess * 100)} %`}
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Zisky / ztráty míče</TableCell>
                        <TableCell className="text-right">
                          {teamTotals.won_balls} / {teamTotals.lost_balls}
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Fauly</TableCell>
                        <TableCell className="text-right">{teamTotals.fouls}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Žluté karty</TableCell>
                        <TableCell className="text-right">{teamTotals.yellow_cards}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Červené karty</TableCell>
                        <TableCell className="text-right">{teamTotals.red_cards}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Penalty</TableCell>
                        <TableCell className="text-right">{teamTotals.penalties}</TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </div>
              </div>

              <div className="grid gap-4 text-sm lg:grid-cols-2">
                <div className="space-y-2">
                  <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Útok
                  </div>
                  <div className="grid gap-2 sm:grid-cols-2">
                    <div className="rounded-xl border p-3">
                      <div className="text-xs text-muted-foreground">Góly / asistence</div>
                      <div className="text-lg font-semibold">
                        {teamTotals.goals} G / {teamTotals.assists} A
                      </div>
                    </div>
                    <div className="rounded-xl border p-3">
                      <div className="text-xs text-muted-foreground">Střely (na / mimo)</div>
                      <div className="text-lg font-semibold">
                        {teamTotals.shots_on_goal} / {teamTotals.shots_off_goal}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Přesnost{" "}
                        {teamTotals.shotAccuracy == null
                          ? "—"
                          : `${Math.round(teamTotals.shotAccuracy * 100)} %`}
                      </div>
                    </div>
                    <div className="rounded-xl border p-3 sm:col-span-2">
                      <div className="text-xs text-muted-foreground">Přihrávky</div>
                      <div className="text-lg font-semibold">{teamTotals.passes}</div>
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Souboje a práce s míčem
                  </div>
                  <div className="grid gap-2 sm:grid-cols-2">
                    <div className="rounded-xl border p-3">
                      <div className="text-xs text-muted-foreground">Souboje (+ / −)</div>
                      <div className="text-lg font-semibold">
                        {teamTotals.won_duels} / {teamTotals.lost_duels}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Úspěšnost{" "}
                        {teamTotals.duelSuccess == null
                          ? "—"
                          : `${Math.round(teamTotals.duelSuccess * 100)} %`}
                      </div>
                    </div>
                    <div className="rounded-xl border p-3">
                      <div className="text-xs text-muted-foreground">Zisky / ztráty míče</div>
                      <div className="text-lg font-semibold">
                        {teamTotals.won_balls} / {teamTotals.lost_balls}
                      </div>
                    </div>
                    <div className="rounded-xl border p-3 sm:col-span-2">
                      <div className="text-xs text-muted-foreground">Penalty</div>
                      <div className="text-lg font-semibold">{teamTotals.penalties}</div>
                    </div>
                  </div>
                </div>

                <div className="space-y-2 lg:col-span-2">
                  <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Disciplína
                  </div>
                  <div className="grid gap-2 sm:grid-cols-3">
                    <div className="rounded-xl border p-3">
                      <div className="text-xs text-muted-foreground">Fauly</div>
                      <div className="text-lg font-semibold">{teamTotals.fouls}</div>
                    </div>
                    <div className="rounded-xl border p-3">
                      <div className="text-xs text-muted-foreground">Žluté karty</div>
                      <div className="text-lg font-semibold">{teamTotals.yellow_cards}</div>
                    </div>
                    <div className="rounded-xl border p-3">
                      <div className="text-xs text-muted-foreground">Červené karty</div>
                      <div className="text-lg font-semibold">{teamTotals.red_cards}</div>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <Card className="w-full rounded-2xl">
        <CardHeader>
          <CardTitle>Souhrn výkonu hráčů</CardTitle>
        </CardHeader>
        <CardContent className="p-4 space-y-3">
          {playedRoster.length === 0 ? (
            <div className="text-sm text-muted-foreground">
              Zatím nejsou k dispozici žádné statistiky. Ujisti se, že byla nastavena sestava a
              zaznamenány události.
            </div>
          ) : (
            <>
              <div className="rounded-xl border">
                <div className="border-b px-4 py-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Statistiky hráčů
                </div>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Hráč</TableHead>
                        <TableHead className="text-right">G</TableHead>
                        <TableHead className="text-right">A</TableHead>
                        <TableHead className="text-right">Střely</TableHead>
                        <TableHead className="text-right">Přihrávky</TableHead>
                        <TableHead className="text-right">Souboje (+/−)</TableHead>
                        <TableHead className="text-right">Zisky/Ztráty</TableHead>
                        <TableHead className="text-right">Fauly</TableHead>
                        <TableHead className="text-right">Karty (ŽK/ČK)</TableHead>
                        <TableHead className="text-right">Podíl na akcích</TableHead>
                        <TableHead className="text-right">Auto rating</TableHead>
                        <TableHead className="text-right">Kombinované</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {playedRoster.map((p) => {
                        const auto = autoRatings[p.player_id] ?? 0;
                        const v = ratingsDraft[p.player_id] ?? { rating: "", note: "" };
                        const manualNum = Number(v.rating);
                        const hasManual =
                          Number.isFinite(manualNum) && manualNum >= 1 && manualNum <= 10;
                        const combined = hasManual
                          ? Math.round(((auto * 0.6 + manualNum * 0.4) + Number.EPSILON) * 10) /
                            10
                          : auto;

                        const shots = p.stats.shots_on_goal + p.stats.shots_off_goal;
                        const teamShare =
                          teamTotals.teamActionsForShare > 0
                            ? ((p.stats.passes +
                                p.stats.shots_on_goal +
                                p.stats.shots_off_goal +
                                p.stats.won_duels +
                                p.stats.lost_duels +
                                p.stats.won_balls +
                                p.stats.lost_balls +
                                p.stats.fouls) /
                                teamTotals.teamActionsForShare) *
                              100
                            : null;

                        return (
                          <TableRow key={p.player_id}>
                            <TableCell>
                              <div className="flex flex-col">
                                <span className="font-medium">
                                  #{p.jersey_number_match} {p.first_name} {p.last_name}
                                </span>
                                <span className="text-xs text-muted-foreground">
                                  {p.role === "starter" ? "Základní sestava" : "Střídající"}
                                </span>
                              </div>
                            </TableCell>
                            <TableCell className="text-right">{p.stats.goals}</TableCell>
                            <TableCell className="text-right">{p.stats.assists}</TableCell>
                            <TableCell className="text-right">{shots}</TableCell>
                            <TableCell className="text-right">{p.stats.passes}</TableCell>
                            <TableCell className="text-right">
                              {p.stats.won_duels} / {p.stats.lost_duels}
                            </TableCell>
                            <TableCell className="text-right">
                              {p.stats.won_balls} / {p.stats.lost_balls}
                            </TableCell>
                            <TableCell className="text-right">{p.stats.fouls}</TableCell>
                            <TableCell className="text-right">
                              {p.stats.yellow_cards} / {p.stats.red_cards}
                            </TableCell>
                            <TableCell className="text-right">
                              {teamShare == null ? "—" : `${teamShare.toFixed(1)} %`}
                            </TableCell>
                            <TableCell className="text-right">{auto.toFixed(1)}</TableCell>
                            <TableCell className="text-right">{combined.toFixed(1)}</TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </div>
              </div>

              <div className="grid gap-3 md:grid-cols-3">
                {topPerformers.mostPasses && (
                  <div className="rounded-xl border p-3 text-sm">
                    <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      Nejvíce přihrávek
                    </div>
                    <div className="mt-1 font-medium">
                      #{topPerformers.mostPasses.jersey_number_match}{" "}
                      {topPerformers.mostPasses.first_name}{" "}
                      {topPerformers.mostPasses.last_name}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {topPerformers.mostPasses.stats.passes} přihrávek
                    </div>
                  </div>
                )}
                {topPerformers.mostDuelsWon && (
                  <div className="rounded-xl border p-3 text-sm">
                    <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      Nejvíce vyhraných soubojů
                    </div>
                    <div className="mt-1 font-medium">
                      #{topPerformers.mostDuelsWon.jersey_number_match}{" "}
                      {topPerformers.mostDuelsWon.first_name}{" "}
                      {topPerformers.mostDuelsWon.last_name}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {topPerformers.mostDuelsWon.stats.won_duels} vyhraných soubojů
                    </div>
                  </div>
                )}
                {topPerformers.mostShots && (
                  <div className="rounded-xl border p-3 text-sm">
                    <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      Nejvíce střel
                    </div>
                    <div className="mt-1 font-medium">
                      #{topPerformers.mostShots.jersey_number_match}{" "}
                      {topPerformers.mostShots.first_name}{" "}
                      {topPerformers.mostShots.last_name}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {topPerformers.mostShots.stats.shots_on_goal +
                        topPerformers.mostShots.stats.shots_off_goal}{" "}
                      střel
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </CardContent>
      </Card>
      {isCoach && playedRoster.length > 0 && (
        <Card className="w-full rounded-2xl">
          <CardHeader>
            <CardTitle>Hodnocení trenéra (po zápase)</CardTitle>
          </CardHeader>
          <CardContent className="p-4 space-y-4">
            <div className="text-xs text-muted-foreground">
              Zadej hodnocení trenéra pro každého hráče (1–10). Kombinované hodnocení vychází z
              automatického modelu a ručního ratingu.
            </div>
            <div className="rounded-xl border">
              <div className="border-b px-4 py-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Hodnocení hráčů
              </div>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Hráč</TableHead>
                      <TableHead className="text-right">Auto rating</TableHead>
                      <TableHead className="text-right">Hodnocení trenéra</TableHead>
                      <TableHead className="text-right">Kombinované</TableHead>
                      <TableHead>Poznámka trenéra</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {playedRoster.map((p) => {
                      const auto = autoRatings[p.player_id] ?? 0;
                      const v = ratingsDraft[p.player_id] ?? { rating: "", note: "" };
                      const manualNum = Number(v.rating);
                      const hasManual =
                        Number.isFinite(manualNum) && manualNum >= 1 && manualNum <= 10;
                      const combined = hasManual
                        ? Math.round(((auto * 0.6 + manualNum * 0.4) + Number.EPSILON) * 10) / 10
                        : auto;

                      return (
                        <TableRow key={p.player_id}>
                          <TableCell>
                            <div className="flex flex-col">
                              <span className="font-medium">
                                #{p.jersey_number_match} {p.first_name} {p.last_name}
                              </span>
                              <span className="text-xs text-muted-foreground">
                                {p.role === "starter" ? "Základní sestava" : "Střídající"}
                              </span>
                            </div>
                          </TableCell>
                          <TableCell className="text-right">{auto.toFixed(1)}</TableCell>
                          <TableCell className="text-right">
                            <Input
                              className="w-20 text-right"
                              inputMode="numeric"
                              placeholder="1–10"
                              value={v.rating}
                              onChange={(e) =>
                                setRatingsDraft((prev) => ({
                                  ...prev,
                                  [p.player_id]: { ...v, rating: e.target.value },
                                }))
                              }
                            />
                          </TableCell>
                          <TableCell className="text-right">{combined.toFixed(1)}</TableCell>
                          <TableCell>
                            <Input
                              className="w-40 md:w-64"
                              placeholder="Krátká poznámka"
                              value={v.note}
                              onChange={(e) =>
                                setRatingsDraft((prev) => ({
                                  ...prev,
                                  [p.player_id]: { ...v, note: e.target.value },
                                }))
                              }
                            />
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
            </div>
            <div className="flex justify-end">
              <Button
                onClick={async () => {
                  setError(null);
                  try {
                    const items = Object.entries(ratingsDraft)
                      .filter(([playerId]) => playedIds.has(Number(playerId)))
                      .map(([playerId, v]) => ({
                        player_id: Number(playerId),
                        rating: Number(v.rating),
                        note: v.note.trim() || null,
                      }))
                      .filter(
                        (x) =>
                          Number.isFinite(x.rating) &&
                          x.rating >= 1 &&
                          x.rating <= 10,
                      );
                    await saveRatingsMutation.mutateAsync(items);
                  } catch (e: unknown) {
                    setError(getErrorMessage(e));
                  }
                }}
                disabled={ratingsQuery.isLoading || saveRatingsMutation.isPending}
              >
                Uložit hodnocení trenéra
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

