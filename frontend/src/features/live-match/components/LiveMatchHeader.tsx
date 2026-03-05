import { Button } from "@/components/ui/button";

import { useAuth } from "@/auth/AuthContext";
import type { MatchStatus } from "@/api/matches";

type Props = {
  matchId: number;
  status: MatchStatus | null;
  half: 1 | 2;
  clockSeconds: number;
  onBack: () => void;
  onRefresh: () => void;
  onStart: () => void | Promise<unknown>;
  onHalfTime: () => void | Promise<unknown>;
  onStartSecondHalf: () => void | Promise<unknown>;
  onFinish: () => void | Promise<unknown>;
  starting: boolean;
  halfTiming: boolean;
  startingSecond: boolean;
  finishing: boolean;
  setError: (msg: string | null) => void;
  getErrorMessage: (err: unknown) => string;
};

function formatClock(sec: number) {
  const s = Math.max(0, Math.floor(sec));
  const mm = String(Math.floor(s / 60)).padStart(2, "0");
  const ss = String(s % 60).padStart(2, "0");
  return `${mm}:${ss}`;
}

function statusLabel(status: MatchStatus | null) {
  if (!status) return "Načítám…";
  if (status === "planned") return "Plánováno";
  if (status === "live_half_1") return "1. poločas";
  if (status === "half_time") return "Poločas";
  if (status === "live_half_2") return "2. poločas";
  if (status === "finished") return "Ukončeno";
  return status;
}

export function LiveMatchHeader({
  matchId,
  status,
  half,
  clockSeconds,
  onBack,
  onRefresh,
  onStart,
  onHalfTime,
  onStartSecondHalf,
  onFinish,
  starting,
  halfTiming,
  startingSecond,
  finishing,
  setError,
  getErrorMessage,
}: Props) {
  const auth = useAuth();
  const isCoach = auth.user?.role === "coach";

  const canStart = status === "planned";
  const canHalfTime = status === "live_half_1";
  const canStartSecond = status === "half_time";
  const canFinish = status === "live_half_1" || status === "live_half_2";

  return (
    <div className="flex w-full items-center justify-between gap-3 flex-wrap">
      <div className="flex flex-col">
        <div className="text-lg font-semibold">Live zápas</div>
        <div className="text-xs text-muted-foreground">
          Zápas ID: {matchId} • Stav: {statusLabel(status)} • Poločas:{" "}
          {status === "planned" ? "—" : half} • Čas: {formatClock(clockSeconds)}
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Button variant="secondary" className="h-10 px-3" onClick={onBack}>
          Zpět
        </Button>
        <Button variant="outline" className="h-10 px-3 text-xs" onClick={onRefresh}>
          Obnovit data
        </Button>
        {isCoach && (
          <>
            <Button
              className="h-10 px-3 text-xs"
              onClick={async () => {
                setError(null);
                try {
                  await onStart();
                } catch (e: unknown) {
                  setError(getErrorMessage(e));
                }
              }}
              disabled={!canStart || starting}
            >
              Start 1. poločas
            </Button>
            <Button
              className="h-10 px-3 text-xs"
              variant="outline"
              onClick={async () => {
                setError(null);
                try {
                  await onHalfTime();
                } catch (e: unknown) {
                  setError(getErrorMessage(e));
                }
              }}
              disabled={!canHalfTime || halfTiming}
            >
              Poločas
            </Button>
            <Button
              className="h-10 px-3 text-xs"
              variant="outline"
              onClick={async () => {
                setError(null);
                try {
                  await onStartSecondHalf();
                } catch (e: unknown) {
                  setError(getErrorMessage(e));
                }
              }}
              disabled={!canStartSecond || startingSecond}
            >
              Start 2. poločas
            </Button>
            <Button
              className="h-10 px-3 text-xs"
              variant="outline"
              onClick={async () => {
                setError(null);
                try {
                  await onFinish();
                } catch (e: unknown) {
                  setError(getErrorMessage(e));
                }
              }}
              disabled={!canFinish || finishing}
            >
              Ukončit
            </Button>
          </>
        )}
      </div>
    </div>
  );
}

