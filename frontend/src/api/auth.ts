import { api } from "./client";

export type User = {
  id: number;
  club_id: number;
  email: string;
  role: "coach" | "assistant" | string;
};

export async function login(email: string, password: string) {
  const res = await api.post<{ access_token: string; token_type: string; user: User }>(
    "/auth/login",
    { email, password }
  );
  return res.data;
}

export async function me() {
  const res = await api.get<User>("/auth/me");
  return res.data;
}

