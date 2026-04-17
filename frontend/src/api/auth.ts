import { api } from "./client";

export type User = {
  id: number;
  club_id: number;
  email: string;
  role: "coach" | string;
  email_verified: boolean;
};

type AuthSuccess = { access_token: string; token_type: string; user: User };

export async function login(email: string, password: string) {
  const res = await api.post<AuthSuccess>("/auth/login", { email, password });
  return res.data;
}

export async function me() {
  const res = await api.get<User>("/auth/me");
  return res.data;
}

export async function register(club_name: string, email: string, password: string) {
  const res = await api.post<{ ok: boolean; message: string }>("/auth/register", {
    club_name,
    email,
    password,
  });
  return res.data;
}

export async function verifyEmail(token: string) {
  const res = await api.get<{ ok: boolean; message: string }>("/auth/verify-email", {
    params: { token },
  });
  return res.data;
}

