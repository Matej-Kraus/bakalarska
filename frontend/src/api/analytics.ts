import { api } from "./client";
import type { PlayerStats } from "./types";

export type PlayerPerformanceRow = {
  match_id: number;
  match_date: string;
  opponent: string;
  competition?: string | null;
  status: string;
  stats: { match_id: number; player_id: number } & PlayerStats;
  rating?: number | null;
  note?: string | null;
};

export type LeaderboardRow = {
  player_id: number;
  first_name: string;
  last_name: string;
  jersey_number: number;
  games: number;
  goals: number;
  assists: number;
  passes: number;
  yellow_cards: number;
  red_cards: number;
  avg_rating?: number | null;
};

export async function playerPerformance(playerId: number, seasonId?: number) {
  const res = await api.get<PlayerPerformanceRow[]>(`/players/${playerId}/performance`, {
    params: seasonId ? { season_id: seasonId } : undefined,
  });
  return res.data;
}

export async function seasonLeaderboards(seasonId: number) {
  const res = await api.get<LeaderboardRow[]>(`/seasons/${seasonId}/leaderboards`);
  return res.data;
}

