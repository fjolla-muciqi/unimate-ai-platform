"use client";

import { useEffect, useState } from "react";

import { PageHeader } from "@/components/layout/page-header";
import {
  EmptyState,
  ErrorState,
  LoadingState,
} from "@/components/layout/states";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { api } from "@/lib/api";
import type { Professor, Schedule, StudentCourse } from "@/lib/types";
import { DAY_LABELS, DAY_ORDER, formatTime } from "@/lib/utils";

export default function CoursesPage() {
  const [courses, setCourses] = useState<StudentCourse[] | null>(null);
  const [schedule, setSchedule] = useState<Schedule[]>([]);
  const [professors, setProfessors] = useState<Professor[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api.myCourses(),
      api.mySchedule(),
      api.professors(),
    ])
      .then(([myCourses, mySchedule, allProfessors]) => {
        setCourses(myCourses);
        setSchedule(mySchedule);
        setProfessors(allProfessors);
      })
      .catch((caught: unknown) =>
        setError(
          caught instanceof Error
            ? caught.message
            : "Lëndët nuk u ngarkuan.",
        ),
      );
  }, []);

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!courses) {
    return <LoadingState />;
  }

  const professorById = new Map(
    professors.map((professor) => [professor.id, professor]),
  );

  const totalEcts = courses.reduce(
    (sum, course) => sum + course.ects,
    0,
  );

  return (
    <div>
      <PageHeader
        title="Lëndët e mia"
        description={`${courses.length} lëndë aktive · ${totalEcts} ECTS gjithsej`}
      />

      {courses.length === 0 ? (
        <EmptyState
          title="Nuk je i regjistruar në asnjë lëndë"
          description="Kontakto zyrën e studentëve për regjistrimin e semestrit."
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {courses.map((course) => {
            const professor = course.professor_id
              ? professorById.get(course.professor_id)
              : undefined;

            const slots = schedule
              .filter((slot) => slot.course_id === course.id)
              .sort(
                (a, b) =>
                  DAY_ORDER.indexOf(a.day_of_week) -
                    DAY_ORDER.indexOf(b.day_of_week) ||
                  a.start_time.localeCompare(b.start_time),
              );

            return (
              <Card key={course.id} className="flex flex-col">
                <CardHeader>
                  <div className="flex items-start justify-between gap-2">
                    <Badge variant="secondary">{course.code}</Badge>
                    <Badge variant="outline">{course.ects} ECTS</Badge>
                  </div>

                  <CardTitle className="pt-2">{course.name}</CardTitle>

                  {course.description ? (
                    <CardDescription className="line-clamp-3">
                      {course.description}
                    </CardDescription>
                  ) : null}
                </CardHeader>

                <CardContent className="mt-auto space-y-3 text-sm">
                  <div>
                    <p className="text-xs text-muted-foreground">
                      Ligjërues{course.group_name ? ` · ${course.group_name}` : ""}
                    </p>
                    <p className="font-medium">
                      {/* Profesori i grupit të studentit; pa grup, koordinatori. */}
                      {course.teacher_name ??
                        (professor
                          ? `${professor.title ?? ""} ${professor.full_name}`.trim()
                          : "I pacaktuar")}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs text-muted-foreground">
                      Orari
                    </p>

                    {slots.length === 0 ? (
                      <p className="text-muted-foreground">
                        I papublikuar
                      </p>
                    ) : (
                      <ul className="space-y-0.5">
                        {slots.map((slot) => (
                          <li key={slot.id} className="tabular-nums">
                            {DAY_LABELS[slot.day_of_week] ??
                              slot.day_of_week}{" "}
                            {formatTime(slot.start_time)}–
                            {formatTime(slot.end_time)}
                            {slot.room ? ` · ${slot.room}` : ""}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
