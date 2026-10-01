"use client";

import { useEffect, useState, type FormEvent } from "react";
import { Loader2 } from "lucide-react";

import { PageHeader } from "@/components/layout/page-header";
import { ErrorState, LoadingState } from "@/components/layout/states";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { MyProfile } from "@/lib/types";

const LANGUAGES: { value: MyProfile["preferred_language"]; label: string }[] =
  [
    { value: "sq", label: "Shqip" },
    { value: "en", label: "English" },
  ];

// I njëjti minimum si te backend-i (`PasswordChange`).
const MIN_PASSWORD_LENGTH = 8;

function errorMessage(caught: unknown, fallback: string): string {
  return caught instanceof Error ? caught.message : fallback;
}

function AcademicProfileCard() {
  const [profile, setProfile] = useState<MyProfile | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api
      .myProfile()
      .then(setProfile)
      .catch((caught) =>
        setError(errorMessage(caught, "Profili nuk u ngarkua.")),
      );
  }, []);

  async function changeLanguage(value: string) {
    setSaving(true);
    setError(null);
    setNotice(null);

    try {
      setProfile(
        await api.updateMyProfile(value as MyProfile["preferred_language"]),
      );
      setNotice("Gjuha e preferuar u ruajt.");
    } catch (caught) {
      setError(errorMessage(caught, "Ruajtja dështoi."));
    } finally {
      setSaving(false);
    }
  }

  if (!profile) {
    return error ? <ErrorState message={error} /> : <LoadingState />;
  }

  const rows: [string, string | number][] = [
    ["Numri i studentit", profile.student_number],
    ["Fakulteti", profile.faculty_name ?? "—"],
    ["Programi", profile.program_name ?? "—"],
    ["Viti i studimit", profile.study_year],
    ["Semestri i kurrikulës", profile.semester],
    ["Viti akademik", profile.academic_year ?? "—"],
    ["Periudha", profile.period_label?.split(", ")[1] ?? "—"],
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Profili akademik</CardTitle>
        <CardDescription>
          Programin, vitin dhe semestrin i ndryshon administrata. Asistenti
          i përdor këto të dhëna për t&apos;i personalizuar përgjigjet.
          {profile.ects_is_official
            ? null
            : " ECTS-të e lëndëve janë demonstrative, jo zyrtare."}
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-6">
        <dl className="grid gap-4 sm:grid-cols-2">
          {rows.map(([label, value]) => (
            <div key={label}>
              <dt className="text-sm text-muted-foreground">{label}</dt>
              <dd className="font-medium">{value}</dd>
            </div>
          ))}
        </dl>

        <div className="max-w-xs space-y-2">
          <Label htmlFor="language">Gjuha e preferuar</Label>
          <Select
            value={profile.preferred_language}
            onValueChange={(value) => void changeLanguage(value)}
            disabled={saving}
          >
            <SelectTrigger id="language">
              <SelectValue />
            </SelectTrigger>

            <SelectContent>
              {LANGUAGES.map((language) => (
                <SelectItem key={language.value} value={language.value}>
                  {language.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {error ? <ErrorState message={error} /> : null}

        {notice ? (
          <Alert variant="success">
            <AlertDescription>{notice}</AlertDescription>
          </Alert>
        ) : null}
      </CardContent>
    </Card>
  );
}

function PasswordCard() {
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();

    setError(null);
    setNotice(null);

    if (next !== confirm) {
      setError("Fjalëkalimi i ri dhe konfirmimi nuk përputhen.");

      return;
    }

    setSaving(true);

    try {
      await api.changePassword(current, next);

      setCurrent("");
      setNext("");
      setConfirm("");
      setNotice("Fjalëkalimi u ndryshua.");
    } catch (caught) {
      setError(errorMessage(caught, "Ndryshimi dështoi."));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Ndrysho fjalëkalimin</CardTitle>
        <CardDescription>
          Të paktën {MIN_PASSWORD_LENGTH} karaktere. Kërkohet edhe
          fjalëkalimi aktual.
        </CardDescription>
      </CardHeader>

      <CardContent>
        <form onSubmit={handleSubmit} className="max-w-sm space-y-4">
          <div className="space-y-2">
            <Label htmlFor="current-password">Fjalëkalimi aktual</Label>
            <Input
              id="current-password"
              type="password"
              autoComplete="current-password"
              required
              value={current}
              onChange={(event) => setCurrent(event.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="new-password">Fjalëkalimi i ri</Label>
            <Input
              id="new-password"
              type="password"
              autoComplete="new-password"
              required
              minLength={MIN_PASSWORD_LENGTH}
              value={next}
              onChange={(event) => setNext(event.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirm-password">Përsërit fjalëkalimin e ri</Label>
            <Input
              id="confirm-password"
              type="password"
              autoComplete="new-password"
              required
              minLength={MIN_PASSWORD_LENGTH}
              value={confirm}
              onChange={(event) => setConfirm(event.target.value)}
            />
          </div>

          {error ? <ErrorState message={error} /> : null}

          {notice ? (
            <Alert variant="success">
              <AlertDescription>{notice}</AlertDescription>
            </Alert>
          ) : null}

          <Button type="submit" disabled={saving}>
            {saving ? <Loader2 className="size-4 animate-spin" /> : null}
            Ruaj fjalëkalimin
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

export default function ProfilePage() {
  const { user } = useAuth();

  if (!user) {
    return <LoadingState />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Profili im"
        description={`${user.first_name} ${user.last_name} · ${user.email}`}
      />

      {user.role === "STUDENT" ? <AcademicProfileCard /> : null}

      <PasswordCard />
    </div>
  );
}
