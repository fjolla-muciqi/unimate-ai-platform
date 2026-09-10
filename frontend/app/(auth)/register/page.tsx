"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import { homeFor, useAuth } from "@/lib/auth-context";

export default function RegisterPage() {
  const router = useRouter();
  const { login } = useAuth();

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();

    setBusy(true);
    setError(null);

    try {
      await api.register({
        first_name: firstName,
        last_name: lastName,
        email,
        password,
      });

      // Regjistrimi krijon gjithmonë një student; roli nuk zgjidhet
      // nga formulari sepse backend-i nuk e pranon.
      const profile = await login(email, password);

      router.replace(homeFor(profile));
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Regjistrimi dështoi. Provo përsëri.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h2 className="text-2xl font-semibold tracking-tight">
          Krijo llogari studenti
        </h2>
        <p className="text-sm text-muted-foreground">
          Profili akademik lidhet nga administrata pas regjistrimit.
        </p>
      </div>

      {error ? (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="firstName">Emri</Label>
            <Input
              id="firstName"
              required
              minLength={2}
              value={firstName}
              onChange={(event) => setFirstName(event.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="lastName">Mbiemri</Label>
            <Input
              id="lastName"
              required
              minLength={2}
              value={lastName}
              onChange={(event) => setLastName(event.target.value)}
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            autoComplete="username"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="password">Fjalëkalimi</Label>
          <Input
            id="password"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
          <p className="text-xs text-muted-foreground">
            Të paktën 8 karaktere.
          </p>
        </div>

        <Button type="submit" className="w-full" disabled={busy}>
          {busy ? <Loader2 className="size-4 animate-spin" /> : null}
          Regjistrohu
        </Button>
      </form>

      <p className="text-center text-sm text-muted-foreground">
        Ke tashmë llogari?{" "}
        <Link
          href="/login"
          className="font-medium text-primary hover:underline"
        >
          Kyçu
        </Link>
      </p>
    </div>
  );
}
