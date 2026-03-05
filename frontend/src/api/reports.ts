import { api } from "./client";
import type { PlayerStats } from "./types";

export type TeamStats = { games: number } & PlayerStats;

export async function teamStatsSeason(seasonId: number) {
  const res = await api.get<TeamStats>(`/seasons/${seasonId}/team-stats`);
  return res.data;
}

