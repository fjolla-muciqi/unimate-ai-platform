"use client";

import { useEffect, useMemo, useState, type FormEvent } from "react";
import { Loader2 } from "lucide-react";

import { ErrorState, LoadingState } from "@/components/layout/states";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { admin, api } from "@/lib/api";
import type { MyProfile, Program } from "@/lib/types";

export default function OnboardingPage() {
  const [programs, setPrograms] = useState<Program[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const [programId, setProgramId] = useState("");
  const [year, setYear] = useState("1");
  const [semester, setSemester] = useState("1");
  const [language, setLanguage] =
    useState<MyProfile["preferred_language"]>("sq");

  useEffect(() => {
    admin.programs
      .list()
      .then((loaded) => {
        setPrograms(loaded);
        setProgramId(loaded[0] ? String(loaded[0].id) : "");
      })
      .catch((caught) =>
        setError(
          caught instanceof Error
            ? caught.message
            : "Programet nuk u ngarkuan.",
        ),
      );
  }, []);

  const program = programs?.find((item) => String(item.id) === programId);

  const years = useMemo(
    () =>
      Array.from({ length: program?.duration_years ?? 3 }, (_, index) =>
        String(index + 1),
      ),
    [program],
  );

  // Viti N përmban semestrat 2N-1 dhe 2N, si te backend-i.
  const semesters = [String(2 * Number(year) - 1), String(2 * Number(year))];

  function changeYear(value: string) {
    setYear(value);
    setSemester(String(2 * Number(value) - 1));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();

    setSaving(true);
    setError(null);

    try {
      await api.createMyProfile({
        program_id: Number(programId),
        study_year: Number(year),
        semester: Number(semester),
        preferred_language: language,
      });

      // Rringarkim i plotë: shiriti anësor e rilexon profilin nga e para.
      window.location.assign("/dashboard");
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Ruajtja dështoi.",
      );
      setSaving(false);
    }
  }

  if (!programs) {
    return error ? <ErrorState message={error} /> : <LoadingState />;
  }

  return (
    <div className="mx-auto max-w-xl">
      <Card>
        <CardHeader>
          <CardTitle>Plotëso profilin akademik</CardTitle>
          <CardDescription>
            Një hap i vetëm para se të fillosh. Do të regjistrohesh
            automatikisht në lëndët e semestrit që zgjedh. Më vonë,
            programin dhe vitin i ndryshon administrata.
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="program">Programi i studimit</Label>
              <Select value={programId} onValueChange={setProgramId}>
                <SelectTrigger id="program">
                  <SelectValue placeholder="Zgjidh programin" />
                </SelectTrigger>

                <SelectContent>
                  {programs.map((item) => (
                    <SelectItem key={item.id} value={String(item.id)}>
                      {item.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="year">Viti i studimit</Label>
                <Select value={year} onValueChange={changeYear}>
                  <SelectTrigger id="year">
                    <SelectValue />
                  </SelectTrigger>

                  <SelectContent>
                    {years.map((value) => (
                      <SelectItem key={value} value={value}>
                        Viti {value}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="semester">Semestri</Label>
                <Select value={semester} onValueChange={setSemester}>
                  <SelectTrigger id="semester">
                    <SelectValue />
                  </SelectTrigger>

                  <SelectContent>
                    {semesters.map((value) => (
                      <SelectItem key={value} value={value}>
                        Semestri {value}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="language">Gjuha e preferuar</Label>
              <Select
                value={language}
                onValueChange={(value) =>
                  setLanguage(value as MyProfile["preferred_language"])
                }
              >
                <SelectTrigger id="language">
                  <SelectValue />
                </SelectTrigger>

                <SelectContent>
                  <SelectItem value="sq">Shqip</SelectItem>
                  <SelectItem value="en">English</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {error ? <ErrorState message={error} /> : null}

            <Button type="submit" disabled={saving || !programId}>
              {saving ? <Loader2 className="size-4 animate-spin" /> : null}
              Ruaj dhe vazhdo
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
