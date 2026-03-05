import { api } from "./client";
import type { MatchEvent, RosterWithStatsRow } from "./types";

export type MatchStatus =
  | "planned"
  | "live_half_1"
  | "half_time"
  | "live_half_2"
  | "finished";

export type MatchDto = {
  id: number;
  season_id: number;
  opponent: string;
  competition?: string | null;
  match_date: string;
  status: MatchStatus;
  seconds_before_live: number;
  live_started_at: string | null;
};

export type SubstitutionDto = {
  id: number;
  match_id: number;
  player_out_id: number;
  player_out_name: string;
  player_in_id: number;
  player_in_name: string;
  half: number;
  second_in_match: number;
};

export async function getMatch(matchId: number) {
  const res = await api.get<MatchDto>(`/matches/${matchId}`);
  return res.data;
}

export async function startMatch(matchId: number) {
  const res = await api.post<MatchDto>(`/matches/${matchId}/start`);
  return res.data;
}

export async function setHalfTime(matchId: number) {
  const res = await api.post<MatchDto>(`/matches/${matchId}/half-time`);
  return res.data;
}

export async function startSecondHalf(matchId: number) {
  const res = await api.post<MatchDto>(`/matches/${matchId}/start-second-half`);
  return res.data;
}

export async function finishMatch(matchId: number) {
  const res = await api.post<MatchDto>(`/matches/${matchId}/finish`);
  return res.data;
}

export async function listSubstitutions(matchId: number) {
  const res = await api.get<SubstitutionDto[]>(`/matches/${matchId}/substitutions`);
  return res.data;
}

export async function createSubstitution(params: {
  matchId: number;
  playerOutId: number;
  playerInId: number;
  half: 1 | 2;
  secondInMatch: number;
}) {
  const res = await api.post<SubstitutionDto>(`/matches/${params.matchId}/substitutions`, {
    player_out_id: params.playerOutId,
    player_in_id: params.playerInId,
    half: params.half,
    second_in_match: params.secondInMatch,
  });
  return res.data;
}

export async function getRosterWithStats(matchId: number) {
  const res = await api.get<RosterWithStatsRow[]>(
    `/matches/${matchId}/roster-with-stats`
  );
  return res.data;
}

export async function listEvents(matchId: number) {
  const res = await api.get<MatchEvent[]>(`/matches/${matchId}/events`);
  return res.data;
}

export async function exportMatchEventsCsv(matchId: number) {
  const res = await api.get(`/export/matches/${matchId}/events.csv`, { responseType: "blob" });
  return res.data as Blob;
}

export type EventType =
  | "goal"
  | "assist"
  | "error"
  | "won_ball"
  | "lost_ball"
  | "foul"
  | "pass"
  | "won_duel"
  | "lost_duel"
  | "shot_on_goal"
  | "shot_off_goal"
  | "yellow_card"
  | "red_card"
  | "penalty";

export async function addEvent(params: {
  matchId: number;
  playerId: number;
  eventType: EventType;
  delta: 1 | -1;
  half: 1 | 2;
  secondInMatch: number;
}) {
  const res = await api.post(`/matches/${params.matchId}/events`, {
    player_id: params.playerId,
    event_type: params.eventType,
    delta: params.delta,
    half: params.half,
    second_in_match: params.secondInMatch,
  });
  return res.data;
}