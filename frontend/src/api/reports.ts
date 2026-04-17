import { api } from "./client";
import type { PlayerStats } from "./types";

export type TeamStats = {
  games: number;
  season_matches_total: number;
  passes_success: number;
  passes_unsuccess: number;
} & PlayerStats;

export async function teamStatsSeason(seasonId: number) {
  const res = await api.get<TeamStats>(`/seasons/${seasonId}/team-stats`);
  return res.data;
}

