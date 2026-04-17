import { api } from "./client";

export type ClubDto = {
  id: number;
  name: string;
  short_name: string | null;
  city: string | null;
  home_venue: string | null;
  founded_year: number | null;
};

export async function getClub() {
  const res = await api.get<ClubDto>("/club");
  return res.data;
}

export async function updateClub(payload: {
  name: string;
  short_name?: string | null;
  city?: string | null;
  home_venue?: string | null;
  founded_year?: number | null;
}) {
  const res = await api.put<ClubDto>("/club", payload);
  return res.data;
}
