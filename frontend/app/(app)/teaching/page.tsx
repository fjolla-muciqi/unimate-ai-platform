"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  BookOpen,
  CalendarClock,
  FileText,
  Users,
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { api } from "@/lib/api";
import type { ProfessorCourse, ProfessorDashboard } from "@/lib/types";
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
  icon: typeof Users;
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

export default function TeachingPage() {
  const [data, setData] = useState<ProfessorDashboard | null>(null);
  const [courses, setCourses] = useState<ProfessorCourse[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.professorDashboard(), api.professorCourses()])
      .then(([dashboard, taught]) => {
        setData(dashboard);
        setCourses(taught);
      })
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

  return (
    <div className="space-y-6">
      <PageHeader
        title={data.full_name}
        description={[
          data.faculty_name,
          data.office ? `Zyra ${data.office}` : null,
          data.consultation_hours,
        ]
          .filter(Boolean)
          .join(" · ")}
      >
        <Button asChild variant="outline">
          <Link href="/teaching/students">
            <Users className="size-4" />
            Studentët e mi
          </Link>
        </Button>
      </PageHeader>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Lëndë që ligjëroj"
          value={data.courses_taught}
          icon={BookOpen}
        />
        <StatCard
          label="Studentë gjithsej"
          value={data.total_students}
          hint="Të regjistruar aktivisht"
          icon={Users}
        />
        <StatCard
          label="Provime të ardhshme"
          value={data.upcoming_exams.length}
          hint={
            data.upcoming_exams[0]
              ? `Më i afërti pas ${data.upcoming_exams[0].days_until} ditësh`
              : "Asnjë i planifikuar"
          }
          icon={CalendarClock}
        />
        <StatCard
          label="Dokumentet e mia"
          value={data.my_documents}
          hint="Të ngarkuara nga unë"
          icon={FileText}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>
              Ligjëratat e sotme ·{" "}
              {DAY_LABELS[data.today] ?? data.today}
            </CardTitle>
            <CardDescription>
              Vetëm lëndët që ligjëroj vetë.
            </CardDescription>
          </CardHeader>

          <CardContent>
            {data.today_schedule.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">
                Sot nuk keni ligjërata të planifikuara.
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
            <CardTitle>Provimet e ardhshme</CardTitle>
            <CardDescription>
              Me numrin e kandidatëve për secilën lëndë.
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
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Lëndët që ligjëroj</CardTitle>
        </CardHeader>

        <CardContent className="px-0">
          {courses.length === 0 ? (
            <p className="px-6 py-6 text-center text-sm text-muted-foreground">
              Nuk ju është caktuar asnjë lëndë.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Lënda</TableHead>
                  <TableHead>Semestri</TableHead>
                  <TableHead>ECTS</TableHead>
                  <TableHead>Studentë</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>

              <TableBody>
                {courses.map((course) => (
                  <TableRow key={course.id}>
                    <TableCell>
                      <p className="font-medium">{course.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {course.code}
                      </p>
                    </TableCell>

                    <TableCell className="tabular-nums">
                      {course.semester}
                    </TableCell>

                    <TableCell className="tabular-nums">
                      {course.ects}
                    </TableCell>

                    <TableCell className="tabular-nums">
                      {course.enrolled_students}
                    </TableCell>

                    <TableCell>
                      <div className="flex justify-end">
                        <Button asChild variant="ghost" size="sm">
                          <Link
                            href={`/teaching/students?course=${course.code}`}
                          >
                            Shiko studentët
                          </Link>
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
