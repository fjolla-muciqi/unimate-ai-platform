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
import { api } from "@/lib/api";
import type { Course, Schedule } from "@/lib/types";
import { DAY_LABELS, DAY_ORDER, cn, formatTime } from "@/lib/utils";

export default function SchedulePage() {
  const [schedule, setSchedule] = useState<Schedule[] | null>(null);
  const [courses, setCourses] = useState<Course[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.mySchedule(), api.myCourses()])
      .then(([mySchedule, myCourses]) => {
        setSchedule(mySchedule);
        setCourses(myCourses);
      })
      .catch((caught: unknown) =>
        setError(
          caught instanceof Error
            ? caught.message
            : "Orari nuk u ngarkua.",
        ),
      );
  }, []);

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!schedule) {
    return <LoadingState />;
  }

  const courseById = new Map(
    courses.map((course) => [course.id, course]),
  );

  const today = new Date().toLocaleDateString("en-US", {
    weekday: "long",
  });

  // Vetëm ditët e punës kanë ligjërata; e shtuna shfaqet nëse ka.
  const days = DAY_ORDER.filter(
    (day) =>
      day !== "Sunday" &&
      (day !== "Saturday" ||
        schedule.some((slot) => slot.day_of_week === "Saturday")),
  );

  return (
    <div>
      <PageHeader
        title="Orari javor"
        description={`${schedule.length} terma nga ${courses.length} lëndë aktive`}
      />

      {schedule.length === 0 ? (
        <EmptyState
          title="Orari nuk është publikuar ende"
          description="Sapo fakulteti ta publikojë, do të shfaqet këtu."
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {days.map((day) => {
            const slots = schedule
              .filter((slot) => slot.day_of_week === day)
              .sort((a, b) =>
                a.start_time.localeCompare(b.start_time),
              );

            const isToday = day === today;

            return (
              <Card
                key={day}
                className={cn(isToday && "border-primary/40 shadow-md")}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle>{DAY_LABELS[day]}</CardTitle>

                    {isToday ? <Badge>Sot</Badge> : null}
                  </div>
                </CardHeader>

                <CardContent>
                  {slots.length === 0 ? (
                    <p className="py-4 text-sm text-muted-foreground">
                      Ditë e lirë.
                    </p>
                  ) : (
                    <ul className="space-y-3">
                      {slots.map((slot) => {
                        const course = courseById.get(slot.course_id);

                        return (
                          <li
                            key={slot.id}
                            className="rounded-lg border-l-2 border-primary bg-muted/40 p-3"
                          >
                            <p className="text-sm font-medium">
                              {course?.name ?? "Lëndë"}
                            </p>
                            <p className="mt-0.5 text-xs tabular-nums text-muted-foreground">
                              {formatTime(slot.start_time)}–
                              {formatTime(slot.end_time)}
                              {course ? ` · ${course.code}` : ""}
                              {slot.room ? ` · ${slot.room}` : ""}
                            </p>
                          </li>
                        );
                      })}
                    </ul>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
