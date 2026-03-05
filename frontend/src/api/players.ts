import { api } from "./client";

export type Player = {
  id: number;
  first_name: string;
  last_name: string;
  jersey_number: number;
  position?: string | null;
};

export type ImportPlayersResult = {
  ok: boolean;
  created: number;
  updated: number;
  errors: Array<{ line: number; error: string; row: Record<string, unknown> }>;
};

export async function listPlayers() {
  const res = await api.get<Player[]>("/players");
  return res.data;
}

export async function createPlayer(payload: {
  first_name: string;
  last_name: string;
  jersey_number: number;
  position?: string;
}) {
  const res = await api.post<Player>("/players", payload);
  return res.data;
}

export async function deletePlayer(playerId: number) {
  const res = await api.delete(`/players/${playerId}`);
  return res.data;
}

export async function importPlayersCsv(file: File) {
  const form = new FormData();
  form.append("file", file);
  const res = await api.post("/players/import", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data as ImportPlayersResult;
}

export async function exportPlayersCsv() {
  const res = await api.get("/export/players.csv", { responseType: "blob" });
  return res.data as Blob;
}