"use client";

import { useEffect, useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { homeFor, useAuth } from "@/lib/auth-context";

/** Llogaritë që krijon `python -m scripts.seed`. */
const DEMO_ACCOUNTS = [
  {
    label: "Student",
    email: "student@unimate.edu",
    password: "Student123!",
  },
  {
    label: "Administrator",
    email: "admin@unimate.edu",
    password: "Admin123!",
  },
];

export default function LoginPage() {
  const router = useRouter();
  const { user, loading, login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // Kush është tashmë i kyçur nuk ka pse ta shohë këtë faqe.
  useEffect(() => {
    if (!loading && user) {
      router.replace(homeFor(user));
    }
  }, [loading, user, router]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();

    setBusy(true);
    setError(null);

    try {
      const profile = await login(email, password);

      router.replace(homeFor(profile));
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Kyçja dështoi. Provo përsëri.",
      );
    } finally {
      setBusy(false);
    }
  }

  function fill(account: (typeof DEMO_ACCOUNTS)[number]) {
    setEmail(account.email);
    setPassword(account.password);
    setError(null);
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h2 className="text-2xl font-semibold tracking-tight">
          Kyçu në llogarinë tënde
        </h2>
        <p className="text-sm text-muted-foreground">
          Përdor emailin universitar për të hyrë në platformë.
        </p>
      </div>

      {error ? (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            autoComplete="username"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="student@unimate.edu"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="password">Fjalëkalimi</Label>
          <Input
            id="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </div>

        <Button type="submit" className="w-full" disabled={busy}>
          {busy ? <Loader2 className="size-4 animate-spin" /> : null}
          Kyçu
        </Button>
      </form>

      <div className="rounded-lg border bg-muted/40 p-4">
        <p className="mb-3 text-xs font-medium text-muted-foreground">
          Llogaritë demo nga seed-i
        </p>

        <div className="flex flex-wrap gap-2">
          {DEMO_ACCOUNTS.map((account) => (
            <Button
              key={account.email}
              type="button"
              variant="outline"
              size="sm"
              onClick={() => fill(account)}
            >
              {account.label}
            </Button>
          ))}
        </div>
      </div>

      <p className="text-center text-sm text-muted-foreground">
        Nuk ke llogari?{" "}
        <Link
          href="/register"
          className="font-medium text-primary hover:underline"
        >
          Regjistrohu
        </Link>
      </p>
    </div>
  );
}
