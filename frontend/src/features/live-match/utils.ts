import type { RosterWithStatsRow } from "@/api/types";

export function formatTime(sec: number) {
  const s = Math.max(0, Math.floor(sec));
  const mm = String(Math.floor(s / 60)).padStart(2, "0");
  const ss = String(s % 60).padStart(2, "0");
  return `${mm}:${ss}`;
}

export function playerName(p: { first_name: string; last_name: string } | RosterWithStatsRow) {
  return `${p.first_name} ${p.last_name}`;
}

