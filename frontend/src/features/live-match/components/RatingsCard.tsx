import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import type { RosterWithStatsRow } from "@/api/types";

import { playerName } from "@/features/live-match/utils";

type RatingsDraft = Record<number, { rating: string; note: string }>;

type Props = {
  roster: RosterWithStatsRow[];
  ratingsDraft: RatingsDraft;
  onDraftChange: (playerId: number, value: { rating: string; note: string }) => void;
  isCoach: boolean;
  isLoading: boolean;
  onSave: () => Promise<void>;
  saving: boolean;
};

export function RatingsCard({
  roster,
  ratingsDraft,
  onDraftChange,
  isCoach,
  isLoading,
  onSave,
  saving,
}: Props) {
  return (
    <Card className="w-full rounded-2xl">
      <CardHeader>
        <CardTitle>Hodnocení hráčů (1–10)</CardTitle>
      </CardHeader>
      <CardContent className="p-4 space-y-3">
        {isLoading ? (
          <div className="text-sm text-muted-foreground">Načítám…</div>
        ) : roster.length === 0 ? (
          <div className="text-sm text-muted-foreground">Nejdřív nastav sestavu.</div>
        ) : (
          <div className="space-y-2">
            {roster.map((p) => {
              const v = ratingsDraft[p.player_id] ?? { rating: "", note: "" };
              return (
                <div
                  key={p.player_id}
                  className="flex flex-col gap-2 rounded-xl border p-3 md:flex-row md:items-center md:justify-between"
                >
                  <div className="min-w-0">
                    <div className="truncate font-medium">
                      #{p.jersey_number_match} {playerName(p)}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {p.role === "starter" ? "Hraje" : "Střídá"}
                    </div>
                  </div>

                  <div className="flex flex-1 flex-col gap-2 md:flex-row md:items-center md:justify-end">
                    <div className="w-28">
                      <Input
                        inputMode="numeric"
                        placeholder="1-10"
                        disabled={!isCoach}
                        value={v.rating}
                        onChange={(e) =>
                          onDraftChange(p.player_id, { ...v, rating: e.target.value })
                        }
                      />
                    </div>
                    <div className="md:w-[360px]">
                      <Input
                        placeholder="Poznámka (volitelně)"
                        disabled={!isCoach}
                        value={v.note}
                        onChange={(e) =>
                          onDraftChange(p.player_id, { ...v, note: e.target.value })
                        }
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {isCoach && (
          <div className="flex gap-2">
            <Button
              onClick={() => onSave()}
              disabled={saving || !roster.length || isLoading}
            >
              Uložit hodnocení
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

