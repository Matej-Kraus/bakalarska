import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

import type { EventType } from "@/api/matches";
import type { RosterWithStatsRow } from "@/api/types";

import { playerName } from "@/features/live-match/utils";

const EVENT_SHORT: Record<EventType, string> = {
  goal: "G",
  assist: "A",
  shot_on_goal: "SOG",
  shot_off_goal: "SOFF",
  pass: "P",
  won_ball: "WB",
  lost_ball: "LB",
  won_duel: "WD",
  lost_duel: "LD",
  foul: "F",
  yellow_card: "YC",
  red_card: "RC",
  error: "E",
  penalty: "PEN",
};

type Props = {
  roster: RosterWithStatsRow[];
  isCoach: boolean;
  isLoading: boolean;
  onDelta: (playerId: number, eventType: EventType, delta: 1 | -1) => Promise<void>;
  /** When false, event buttons are disabled (e.g. player not on field) */
  canRecordForPlayer?: (row: RosterWithStatsRow) => boolean;
};

const ALL_EVENT_TYPES: EventType[] = [
  "goal",
  "assist",
  "shot_on_goal",
  "shot_off_goal",
  "pass",
  "won_ball",
  "lost_ball",
  "won_duel",
  "lost_duel",
  "foul",
  "yellow_card",
  "red_card",
  "error",
  "penalty",
];

function statValueForEvent(row: RosterWithStatsRow, event: EventType): number | null {
  const s = row.stats;
  if (event === "goal") return s.goals;
  if (event === "assist") return s.assists;
  if (event === "error") return s.errors;
  if (event === "won_ball") return s.won_balls;
  if (event === "lost_ball") return s.lost_balls;
  if (event === "foul") return s.fouls;
  if (event === "pass") return s.passes;
  if (event === "won_duel") return s.won_duels;
  if (event === "lost_duel") return s.lost_duels;
  if (event === "shot_on_goal") return s.shots_on_goal;
  if (event === "shot_off_goal") return s.shots_off_goal;
  if (event === "yellow_card") return s.yellow_cards;
  if (event === "red_card") return s.red_cards;
  if (event === "penalty") return s.penalties;
  return null;
}

export function RosterEventsCard({
  roster,
  isCoach,
  isLoading,
  onDelta,
  canRecordForPlayer,
}: Props) {
  const canRecordFor = canRecordForPlayer ?? (() => true);

  return (
    <Card className="w-full rounded-2xl">
      <CardHeader>
        <CardTitle>Hráči a události</CardTitle>
      </CardHeader>
      <CardContent className="w-full p-4">
        {isLoading ? (
          <div className="text-sm text-muted-foreground">Načítám sestavu…</div>
        ) : roster.length === 0 ? (
          <div className="text-sm text-muted-foreground">
            Sestava pro zápas je prázdná. Nastav ji v „Sestava“ u zápasu.
          </div>
        ) : (
          <div className="w-full space-y-3">
            {roster.map((p) => {
              const canRecordThis = isCoach && canRecordFor(p);
              return (
                <div
                  key={p.player_id}
                  className="flex w-full items-center gap-4 rounded-xl border bg-card px-4 py-3"
                >
                  <div className="shrink-0 w-32 min-w-[8rem]">
                    <span className="text-sm font-medium truncate block">
                      #{p.jersey_number_match} {playerName(p)}
                    </span>
                    <span
                      className={
                        p.on_field === true
                          ? "text-xs font-medium text-green-700 dark:text-green-400"
                          : "text-xs text-muted-foreground"
                      }
                    >
                      {p.on_field === true
                        ? "Na hřišti"
                        : p.role === "starter"
                          ? "Vystřídán"
                          : "Na lavičce"}
                    </span>
                  </div>
                  <div className="flex flex-1 flex-wrap items-center gap-2 min-w-0">
                    {ALL_EVENT_TYPES.map((event) => {
                      const value = statValueForEvent(p, event);
                      return (
                        <div
                          key={event}
                          className="flex items-center gap-1 rounded-lg border border-border bg-background px-2 py-1.5 text-sm shrink-0"
                          title={event}
                        >
                          <Button
                            type="button"
                            size="icon"
                            variant="ghost"
                            className="h-8 w-8 min-h-8 min-w-8 shrink-0 touch-manipulation"
                            disabled={!canRecordThis || isLoading}
                            onClick={() => onDelta(p.player_id, event, 1)}
                          >
                            +
                          </Button>
                          <span className="w-6 text-center tabular-nums font-medium text-sm">
                            {value ?? 0}
                          </span>
                          <span className="w-7 shrink-0 text-muted-foreground text-xs font-medium">
                            {EVENT_SHORT[event]}
                          </span>
                          <Button
                            type="button"
                            size="icon"
                            variant="ghost"
                            className="h-8 w-8 min-h-8 min-w-8 shrink-0 touch-manipulation"
                            disabled={!canRecordThis || isLoading || (value ?? 0) <= 0}
                            onClick={() => onDelta(p.player_id, event, -1)}
                          >
                            −
                          </Button>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

