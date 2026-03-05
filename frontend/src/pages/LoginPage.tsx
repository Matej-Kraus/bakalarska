import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/auth/AuthContext";

export default function LoginPage() {
  const navigate = useNavigate();
  const auth = useAuth();

  const [email, setEmail] = useState("coach@demo.local");
  const [password, setPassword] = useState("coach");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function submit() {
    try {
      setError(null);
      setSubmitting(true);
      await auth.login(email.trim(), password);
      navigate("/players", { replace: true });
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Login failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-background text-foreground p-6 flex items-center justify-center">
      <Card className="rounded-2xl w-full max-w-md">
        <CardHeader>
          <CardTitle>Přihlášení</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {error && (
            <div className="rounded-xl border border-destructive p-3 text-sm text-destructive">
              {error}
            </div>
          )}

          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Email</div>
            <Input value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>

          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Heslo</div>
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") submit();
              }}
            />
          </div>

          <Button className="w-full" disabled={submitting} onClick={submit}>
            Přihlásit
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

