import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/auth/AuthContext";
import { verifyEmail } from "@/api/auth";

function getErrorMessage(e: unknown): string {
  if (axios.isAxiosError(e)) {
    const detail = e.response?.data?.detail;
    if (typeof detail === "string" && detail.trim().length > 0) {
      return detail;
    }
    return e.message;
  }
  return e instanceof Error ? e.message : "Operace selhala";
}

export default function LoginPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const auth = useAuth();

  const [registerClubName, setRegisterClubName] = useState("");
  const [registerEmail, setRegisterEmail] = useState("");
  const [registerPassword, setRegisterPassword] = useState("");
  const [registerError, setRegisterError] = useState<string | null>(null);
  const [registerSuccess, setRegisterSuccess] = useState<string | null>(null);
  const [registerSubmitting, setRegisterSubmitting] = useState(false);

  const [loginEmail, setLoginEmail] = useState("coach@demo.local");
  const [loginPassword, setLoginPassword] = useState("coach");
  const [loginError, setLoginError] = useState<string | null>(null);
  const [loginSubmitting, setLoginSubmitting] = useState(false);

  useEffect(() => {
    const token = searchParams.get("verify_token");
    if (!token) return;
    let cancelled = false;
    (async () => {
      try {
        const res = await verifyEmail(token);
        if (cancelled) return;
        setRegisterSuccess(res.message);
        setRegisterError(null);
      } catch (e: unknown) {
        if (cancelled) return;
        setRegisterError(getErrorMessage(e));
      } finally {
        if (cancelled) return;
        const next = new URLSearchParams(searchParams);
        next.delete("verify_token");
        setSearchParams(next, { replace: true });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [searchParams, setSearchParams]);

  async function submitRegister() {
    try {
      setRegisterError(null);
      setRegisterSuccess(null);
      setRegisterSubmitting(true);
      await auth.register(registerClubName.trim(), registerEmail.trim(), registerPassword);
      setRegisterSuccess(
        "Registrace proběhla. Ověřovací e-mail byl odeslán. Po ověření se přihlas vpravo.",
      );
    } catch (e: unknown) {
      setRegisterError(getErrorMessage(e));
    } finally {
      setRegisterSubmitting(false);
    }
  }

  async function submitLogin() {
    try {
      setLoginError(null);
      setLoginSubmitting(true);
      await auth.login(loginEmail.trim(), loginPassword);
      navigate("/players", { replace: true });
    } catch (e: unknown) {
      setLoginError(getErrorMessage(e));
    } finally {
      setLoginSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-background text-foreground p-6 flex items-center justify-center">
      <div className="w-full max-w-5xl grid gap-4 md:grid-cols-2">
        <Card className="rounded-2xl">
          <CardHeader>
            <CardTitle>Registrace klubu</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {registerError && (
              <div className="rounded-xl border border-destructive p-3 text-sm text-destructive">
                {registerError}
              </div>
            )}
            {registerSuccess && (
              <div className="rounded-xl border border-emerald-500/60 bg-emerald-500/10 p-3 text-sm text-emerald-700 dark:text-emerald-300">
                {registerSuccess}
              </div>
            )}

            <div className="space-y-1">
              <div className="text-xs text-muted-foreground">Název klubu</div>
              <Input
                value={registerClubName}
                onChange={(e) => setRegisterClubName(e.target.value)}
                placeholder="Např. FK Příbram"
              />
            </div>

            <div className="space-y-1">
              <div className="text-xs text-muted-foreground">Email</div>
              <Input
                value={registerEmail}
                onChange={(e) => setRegisterEmail(e.target.value)}
                placeholder="trener@klub.cz"
              />
            </div>

            <div className="space-y-1">
              <div className="text-xs text-muted-foreground">Heslo</div>
              <Input
                type="password"
                value={registerPassword}
                onChange={(e) => setRegisterPassword(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") void submitRegister();
                }}
              />
            </div>

            <Button className="w-full" disabled={registerSubmitting} onClick={() => void submitRegister()}>
              Registrovat
            </Button>
          </CardContent>
        </Card>

        <Card className="rounded-2xl">
          <CardHeader>
            <CardTitle>Přihlášení</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {loginError && (
              <div className="rounded-xl border border-destructive p-3 text-sm text-destructive">
                {loginError}
              </div>
            )}

            <div className="space-y-1">
              <div className="text-xs text-muted-foreground">Email</div>
              <Input value={loginEmail} onChange={(e) => setLoginEmail(e.target.value)} />
            </div>

            <div className="space-y-1">
              <div className="text-xs text-muted-foreground">Heslo</div>
              <Input
                type="password"
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") void submitLogin();
                }}
              />
            </div>

            <Button className="w-full" disabled={loginSubmitting} onClick={() => void submitLogin()}>
              Přihlásit
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

