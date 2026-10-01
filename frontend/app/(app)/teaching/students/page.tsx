"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

import { PageHeader } from "@/components/layout/page-header";
import {
  EmptyState,
  ErrorState,
  LoadingState,
} from "@/components/layout/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { api } from "@/lib/api";
import type { ProfessorCourse, ProfessorStudent } from "@/lib/types";

function StudentsView() {
  const params = useSearchParams();

  const [students, setStudents] = useState<ProfessorStudent[] | null>(
    null,
  );
  const [courses, setCourses] = useState<ProfessorCourse[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Filtri vjen nga URL-ja, që lidhja nga faqja e ligjëratave ta
  // hapë menjëherë lëndën e duhur.
  const selected = params.get("course");

  useEffect(() => {
    Promise.all([
      api.professorStudents(selected ?? undefined),
      api.professorCourses(),
    ])
      .then(([rows, taught]) => {
        setStudents(rows);
        setCourses(taught);
      })
      .catch((caught: unknown) =>
        setError(
          caught instanceof Error
            ? caught.message
            : "Studentët nuk u ngarkuan.",
        ),
      );
  }, [selected]);

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!students) {
    return <LoadingState />;
  }

  const byCourse = new Map<string, ProfessorStudent[]>();

  for (const student of students) {
    const key = `${student.course_name} (${student.course_code})`;

    byCourse.set(key, [...(byCourse.get(key) ?? []), student]);
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Studentët e mi"
        description={`${students.length} regjistrime aktive në lëndët që ligjëroj`}
      />

      <div className="flex flex-wrap gap-2">
        <Button
          asChild
          variant={selected ? "outline" : "default"}
          size="sm"
        >
          <a href="/teaching/students">Të gjitha lëndët</a>
        </Button>

        {courses.map((course) => (
          <Button
            key={course.id}
            asChild
            variant={selected === course.code ? "default" : "outline"}
            size="sm"
          >
            <a href={`/teaching/students?course=${course.code}`}>
              {course.code}
            </a>
          </Button>
        ))}
      </div>

      {students.length === 0 ? (
        <EmptyState
          title="Asnjë student i regjistruar"
          description={
            selected
              ? `Lënda ${selected} nuk ka regjistrime aktive, ose nuk ju takon juve.`
              : "Sapo të regjistrohen studentë, do të shfaqen këtu."
          }
        />
      ) : (
        Array.from(byCourse.entries()).map(([label, rows]) => (
          <Card key={label}>
            <CardHeader>
              <div className="flex items-center justify-between gap-2">
                <CardTitle>{label}</CardTitle>
                <Badge variant="secondary">
                  {rows.length} studentë
                </Badge>
              </div>
            </CardHeader>

            <CardContent className="px-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Studenti</TableHead>
                    <TableHead>Grupi</TableHead>
                    <TableHead>Numri</TableHead>
                    <TableHead>Viti</TableHead>
                    <TableHead>Email</TableHead>
                  </TableRow>
                </TableHeader>

                <TableBody>
                  {rows.map((student) => (
                    <TableRow key={student.student_profile_id}>
                      <TableCell className="font-medium">
                        {student.full_name}
                      </TableCell>

                      <TableCell>{student.group_name ?? "—"}</TableCell>
                      <TableCell className="tabular-nums">
                        {student.student_number}
                      </TableCell>

                      <TableCell className="tabular-nums">
                        {student.study_year}
                      </TableCell>

                      <TableCell className="text-muted-foreground">
                        {student.email}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        ))
      )}
    </div>
  );
}

export default function StudentsPage() {
  // `useSearchParams` kërkon një kufi Suspense në App Router.
  return (
    <Suspense fallback={<LoadingState />}>
      <StudentsView />
    </Suspense>
  );
}
