"use client";

import { useEffect, useState } from "react";

import { PageHeader } from "@/components/layout/page-header";
import {
  EmptyState,
  ErrorState,
  LoadingState,
} from "@/components/layout/states";
import { Badge } from "@/components/ui/badge";
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
import type { Course, Exam } from "@/lib/types";
import { daysUntil, formatDateTime } from "@/lib/utils";

export default function ExamsPage() {
  const [exams, setExams] = useState<Exam[] | null>(null);
  const [courses, setCourses] = useState<Course[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.myExams(), api.myCourses()])
      .then(([myExams, myCourses]) => {
        setExams(myExams);
        setCourses(myCourses);
      })
      .catch((caught: unknown) =>
        setError(
          caught instanceof Error
            ? caught.message
            : "Provimet nuk u ngarkuan.",
        ),
      );
  }, []);

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!exams) {
    return <LoadingState />;
  }

  const courseById = new Map(
    courses.map((course) => [course.id, course]),
  );

  const upcoming = exams
    .filter((exam) => daysUntil(exam.exam_date) >= 0)
    .sort((a, b) => a.exam_date.localeCompare(b.exam_date));

  const past = exams
    .filter((exam) => daysUntil(exam.exam_date) < 0)
    .sort((a, b) => b.exam_date.localeCompare(a.exam_date));

  function renderTable(rows: Exam[], withCountdown: boolean) {
    return (
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Lënda</TableHead>
            <TableHead>Lloji</TableHead>
            <TableHead>Data</TableHead>
            <TableHead>Salla</TableHead>
            {withCountdown ? <TableHead>Mbetur</TableHead> : null}
          </TableRow>
        </TableHeader>

        <TableBody>
          {rows.map((exam) => {
            const course = courseById.get(exam.course_id);
            const remaining = daysUntil(exam.exam_date);

            return (
              <TableRow key={exam.id}>
                <TableCell>
                  <p className="font-medium">
                    {course?.name ?? "Lëndë"}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {course?.code ?? ""}
                  </p>
                </TableCell>

                <TableCell>
                  <Badge variant="outline">{exam.exam_type}</Badge>
                </TableCell>

                <TableCell className="tabular-nums">
                  {formatDateTime(exam.exam_date)}
                </TableCell>

                <TableCell>{exam.room ?? "—"}</TableCell>

                {withCountdown ? (
                  <TableCell>
                    <Badge
                      variant={remaining <= 7 ? "warning" : "secondary"}
                    >
                      {remaining === 0
                        ? "Sot"
                        : `${remaining} ditë`}
                    </Badge>
                  </TableCell>
                ) : null}
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Provimet"
        description={`${upcoming.length} të ardhshme · ${past.length} të kaluara`}
      />

      {exams.length === 0 ? (
        <EmptyState
          title="Nuk ka provime të regjistruara"
          description="Provimet shfaqen sapo fakulteti të publikojë afatet."
        />
      ) : (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Provimet e ardhshme</CardTitle>
            </CardHeader>

            <CardContent className="px-0">
              {upcoming.length === 0 ? (
                <p className="px-6 py-4 text-sm text-muted-foreground">
                  Nuk ke provime të planifikuara.
                </p>
              ) : (
                renderTable(upcoming, true)
              )}
            </CardContent>
          </Card>

          {past.length > 0 ? (
            <Card>
              <CardHeader>
                <CardTitle>Provimet e kaluara</CardTitle>
              </CardHeader>

              <CardContent className="px-0">
                {renderTable(past, false)}
              </CardContent>
            </Card>
          ) : null}
        </>
      )}
    </div>
  );
}
