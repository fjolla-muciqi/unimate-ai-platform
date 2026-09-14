"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  BellRing,
  BookOpen,
  CalendarClock,
  FileText,
  GraduationCap,
  MessageSquare,
} from "lucide-react";

import { PageHeader } from "@/components/layout/page-header";
import { ErrorState, LoadingState } from "@/components/layout/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { api } from "@/lib/api";
import type { Dashboard } from "@/lib/types";
import { DAY_LABELS, formatDateTime, formatTime } from "@/lib/utils";

function StatCard({
  label,
  value,
  hint,
  icon: Icon,
}: {
  label: string;
  value: string | number;
  hint?: string;
  icon: typeof BookOpen;
}) {
  return (
    <Card>
      <CardContent className="flex items-start justify-between gap-4 p-5">
        <div className="space-y-1">
          <p className="text-sm text-muted-foreground">{label}</p>
          <p className="text-3xl font-semibold tabular-nums">{value}</p>

          {hint ? (
            <p className="text-xs text-muted-foreground">{hint}</p>
          ) : null}
        </div>

        <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
          <Icon className="size-5" />
        </div>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .dashboard()
      .then(setData)
      .catch((caught: unknown) =>
        setError(
          caught instanceof Error
            ? caught.message
            : "Paneli nuk u ngarkua.",
        ),
      );
  }, []);

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!data) {
    return <LoadingState />;
  }

  const firstName = data.full_name.split(" ")[0];

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Mirë se erdhe, ${firstName}`}
        description={`${data.program_name} · Viti ${data.academic_year}, semestri ${data.semester} · Nr. ${data.student_number}`}
      >
        <Button asChild>
          <Link href="/chat">
            <MessageSquare className="size-4" />
            Pyet asistentin
          </Link>
        </Button>
      </PageHeader>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Lëndë aktive"
          value={data.active_courses}
          hint={`${data.progress.in_progress_ects} ECTS këtë semestër`}
          icon={BookOpen}
        />
        <StatCard
          label="Provime të ardhshme"
          value={data.upcoming_exams.length}
          hint={
            data.upcoming_exams[0]
              ? `Më i afërti pas ${data.upcoming_exams[0].days_until} ditësh`
              : "Asnjë provim i planifikuar"
          }
          icon={GraduationCap}
        />
        <StatCard
          label="Afate & njoftime"
          value={data.upcoming_deadlines + data.active_notifications}
          hint={`${data.upcoming_deadlines} afate, ${data.active_notifications} njoftime`}
          icon={BellRing}
        />
        <StatCard
          label="Dokumente të indeksuara"
          value={data.available_documents}
          hint="Gati për pyetje te asistenti"
          icon={FileText}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>
              Orari i sotëm ·{" "}
              {DAY_LABELS[data.today] ?? data.today}
            </CardTitle>
            <CardDescription>
              Vetëm lëndët ku je i regjistruar aktivisht.
            </CardDescription>
          </CardHeader>

          <CardContent>
            {data.today_schedule.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">
                Sot nuk ke ligjërata të planifikuara.
              </p>
            ) : (
              <ul className="divide-y">
                {data.today_schedule.map((slot, index) => (
                  <li
                    key={`${slot.course_code}-${index}`}
                    className="flex items-center gap-4 py-3"
                  >
                    <div className="w-24 shrink-0 text-sm font-medium tabular-nums">
                      {formatTime(slot.start_time)}–
                      {formatTime(slot.end_time)}
                    </div>

                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">
                        {slot.course_name}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {slot.course_code}
                        {slot.room ? ` · ${slot.room}` : ""}
                      </p>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Progresi i studimeve</CardTitle>
            <CardDescription>
              Kredite të fituara nga lëndët e përfunduara.
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            <div>
              <div className="mb-2 flex items-baseline justify-between">
                <span className="text-2xl font-semibold tabular-nums">
                  {data.progress.percent}%
                </span>
                <span className="text-sm text-muted-foreground tabular-nums">
                  {data.progress.earned_ects} /{" "}
                  {data.progress.required_ects} ECTS
                </span>
              </div>

              <Progress value={data.progress.percent} />
            </div>

            <div className="rounded-lg bg-muted/50 p-3 text-sm">
              <p className="text-muted-foreground">
                Në proces këtë semestër
              </p>
              <p className="font-medium tabular-nums">
                {data.progress.in_progress_ects} ECTS
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Provimet e ardhshme</CardTitle>
          <CardDescription>
            Tri provimet më të afërta nga lëndët e tua aktive.
          </CardDescription>
        </CardHeader>

        <CardContent>
          {data.upcoming_exams.length === 0 ? (
            <p className="py-6 text-center text-sm text-muted-foreground">
              Nuk ka provime të planifikuara.
            </p>
          ) : (
            <ul className="divide-y">
              {data.upcoming_exams.map((exam, index) => (
                <li
                  key={`${exam.course_code}-${index}`}
                  className="flex flex-wrap items-center gap-3 py-3"
                >
                  <CalendarClock className="size-4 shrink-0 text-muted-foreground" />

                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">
                      {exam.course_name}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {exam.course_code} ·{" "}
                      {formatDateTime(exam.exam_date)}
                      {exam.room ? ` · ${exam.room}` : ""}
                    </p>
                  </div>

                  <Badge
                    variant={
                      exam.days_until <= 7 ? "warning" : "secondary"
                    }
                  >
                    {exam.days_until === 0
                      ? "Sot"
                      : `Pas ${exam.days_until} ditësh`}
                  </Badge>

                  <Badge variant="outline">{exam.exam_type}</Badge>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
