import { useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";

import {
  addEvent,
  createSubstitution,
  finishMatch,
  getMatch,
  getRosterWithStats,
  listEvents,
  listSubstitutions,
  setHalfTime,
  startMatch,
  startSecondHalf,
  type EventType,
  type MatchDto,
  type SubstitutionDto,
} from "@/api/matches";
import type { MatchEvent, RosterWithStatsRow } from "@/api/types";
import { listRatings, saveRatings } from "@/api/ratings";

export function getErrorMessage(err: unknown): string {
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

export function useLiveMatchData(matchId: number, isValidMatchId: boolean) {
  const qc = useQueryClient();

  const matchQuery = useQuery({
    queryKey: ["match", matchId],
    queryFn: () => getMatch(matchId),
    enabled: isValidMatchId,
    refetchOnWindowFocus: false,
    refetchInterval: 10000,
  });

  const rosterQuery = useQuery({
    queryKey: ["roster-with-stats", matchId],
    queryFn: () => getRosterWithStats(matchId),
    enabled: isValidMatchId,
    refetchOnWindowFocus: false,
  });

  const eventsQuery = useQuery({
    queryKey: ["events", matchId],
    queryFn: () => listEvents(matchId),
    enabled: isValidMatchId,
    refetchOnWindowFocus: false,
  });

  const ratingsQuery = useQuery({
    queryKey: ["ratings", matchId],
    queryFn: () => listRatings(matchId),
    enabled: isValidMatchId,
    refetchOnWindowFocus: false,
  });

  const substitutionsQuery = useQuery({
    queryKey: ["substitutions", matchId],
    queryFn: () => listSubstitutions(matchId),
    enabled: isValidMatchId,
    refetchOnWindowFocus: false,
  });

  const invalidateLive = async () => {
    await qc.invalidateQueries({ queryKey: ["match", matchId] });
    await qc.invalidateQueries({ queryKey: ["roster-with-stats", matchId] });
    await qc.invalidateQueries({ queryKey: ["events", matchId] });
  };

  const startMutation = useMutation({
    mutationFn: () => startMatch(matchId),
    onSuccess: invalidateLive,
  });

  const halfTimeMutation = useMutation({
    mutationFn: () => setHalfTime(matchId),
    onSuccess: invalidateLive,
  });

  const startSecondHalfMutation = useMutation({
    mutationFn: () => startSecondHalf(matchId),
    onSuccess: invalidateLive,
  });

  const finishMutation = useMutation({
    mutationFn: () => finishMatch(matchId),
    onSuccess: invalidateLive,
  });

  const addEventMutation = useMutation({
    mutationFn: (p: {
      playerId: number;
      delta: 1 | -1;
      eventType: EventType;
      half: 1 | 2;
      secondInMatch: number;
    }) =>
      addEvent({
        matchId,
        playerId: p.playerId,
        eventType: p.eventType,
        delta: p.delta,
        half: p.half,
        secondInMatch: p.secondInMatch,
      }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["roster-with-stats", matchId] });
      await qc.invalidateQueries({ queryKey: ["events", matchId] });
    },
  });

  const saveRatingsMutation = useMutation({
    mutationFn: (items: Array<{ player_id: number; rating: number; note: string | null }>) =>
      saveRatings(matchId, items),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["ratings", matchId] });
    },
  });

  const roster: RosterWithStatsRow[] = rosterQuery.data ?? [];

  const lastEvents: MatchEvent[] = useMemo(() => {
    const events = eventsQuery.data ?? [];
    return [...events].slice(-30).reverse();
  }, [eventsQuery.data]);

  const match: MatchDto | null = matchQuery.data ?? null;
  const substitutions: SubstitutionDto[] = substitutionsQuery.data ?? [];

  const onFieldIds = new Set<number>(
    roster.filter((r) => r.role === "starter").map((r) => r.player_id),
  );
  substitutions.forEach((s) => {
    if (onFieldIds.has(s.player_out_id)) {
      onFieldIds.delete(s.player_out_id);
    }
    onFieldIds.add(s.player_in_id);
  });

  const rosterWithOnField: RosterWithStatsRow[] = roster.map((r) => ({
    ...r,
    on_field: onFieldIds.has(r.player_id),
  }));

  const createSubstitutionMutation = useMutation({
    mutationFn: (p: {
      playerOutId: number;
      playerInId: number;
      half: 1 | 2;
      secondInMatch: number;
    }) =>
      createSubstitution({
        matchId,
        playerOutId: p.playerOutId,
        playerInId: p.playerInId,
        half: p.half,
        secondInMatch: p.secondInMatch,
      }),
    onSuccess: async () => {
      await qc.refetchQueries({ queryKey: ["substitutions", matchId] });
      await qc.refetchQueries({ queryKey: ["roster-with-stats", matchId] });
      await qc.invalidateQueries({ queryKey: ["events", matchId] });
    },
  });

  return {
    match,
    roster: rosterWithOnField,
    lastEvents,
    ratings: ratingsQuery.data ?? [],
    matchQuery,
    rosterQuery,
    eventsQuery,
    ratingsQuery,
    startMutation,
    halfTimeMutation,
    startSecondHalfMutation,
    finishMutation,
    addEventMutation,
    saveRatingsMutation,
    substitutions,
    createSubstitutionMutation,
    substitutionsQuery,
  };
}

