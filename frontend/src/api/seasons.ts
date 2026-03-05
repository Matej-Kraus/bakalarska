import { api } from "./client";

export type Season = { id: number; name: string };

export async function listSeasons() {
  const res = await api.get<Season[]>("/seasons");
  return res.data;
}

