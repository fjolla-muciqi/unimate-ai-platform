"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Loader2, Plus, Trash2, X } from "lucide-react";

import { PageHeader } from "@/components/layout/page-header";
import { ErrorState, LoadingState } from "@/components/layout/states";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { admin, api } from "@/lib/api";
import type { AdminStudentDetail, Course, CourseGroup } from "@/lib/types";

// Radix Select nuk pranon "" si vlerë.
const NO_GROUP = "__none";
const AUTO = "__auto";

function errorMessage(caught: unknown, fallback: string): string {
  return caught instanceof Error ? caught.message : fallback;
}

export default function StudentDetailPage() {
  const params = useParams<{ id: string }>();
  const userId = Number(params.id);

  const [student, setStudent] = useState<AdminStudentDetail | null>(null);
  const [courses, setCourses] = useState<Course[]>([]);
  const [groups, setGroups] = useState<CourseGroup[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState<number | "add" | null>(null);
  const [confirmId, setConfirmId] = useState<number | null>(null);

  const [newCourse, setNewCourse] = useState("");
  const [newGroup, setNewGroup] = useState(AUTO);

  const refresh = useCallback(async () => {
    try {
      const [detail, allGroups] = await Promise.all([
        admin.student(userId),
        admin.courseGroups.list(),
      ]);

      setStudent(detail);
      setGroups(allGroups);
    } catch (caught) {
      setError(errorMessage(caught, "Studenti nuk u ngarkua."));
    }
  }, [userId]);

  useEffect(() => {
    void refresh();

    api
      .courses()
      .then(setCourses)
      .catch(() => setCourses([]));
  }, [refresh]);

  const groupsOf = useCallback(
    (courseId: number) => groups.filter((group) => group.course_id === courseId),
    [groups],
  );

  // Lëndët e programit të studentit ku ende nuk është i regjistruar.
  const available = useMemo(() => {
    if (!student) {
      return [];
    }

    const enrolled = new Set(student.courses.map((course) => course.course_id));

    return courses
      .filter(
        (course) =>
          course.program_id === student.program_id && !enrolled.has(course.id),
      )
      .sort((a, b) => a.semester - b.semester || a.code.localeCompare(b.code));
  }, [courses, student]);

  async function run(
    key: number | "add",
    action: () => Promise<unknown>,
    success: string,
  ): Promise<boolean> {
    setBusy(key);
    setError(null);
    setNotice(null);

    try {
      await action();
      setNotice(success);
      await refresh();

      return true;
    } catch (caught) {
      setError(errorMessage(caught, "Veprimi dështoi."));

      return false;
    } finally {
      setBusy(null);
    }
  }

  function addCourse() {
    if (!student?.student_profile_id || !newCourse) {
      return;
    }

    const profileId = student.student_profile_id;

    void run(
      "add",
      () =>
        admin.enroll({
          student_profile_id: profileId,
          course_id: Number(newCourse),
          group_id: newGroup === AUTO ? null : Number(newGroup),
        }),
      "Lënda u shtua.",
    ).then((ok) => {
      if (ok) {
        setNewCourse("");
        setNewGroup(AUTO);
      }
    });
  }

  if (!student) {
    return error ? <ErrorState message={error} /> : <LoadingState />;
  }

  const activeCourses = student.courses.filter((course) => course.status === "ACTIVE");
  const totalEcts = activeCourses.reduce((sum, course) => sum + course.ects, 0);
  const earnedEcts = student.courses
    .filter((course) => course.status === "COMPLETED")
    .reduce((sum, course) => sum + course.ects, 0);

  return (
    <div className="space-y-6">
      <Button asChild variant="ghost" className="-ml-3">
        <Link href="/admin/students">
          <ArrowLeft className="size-4" />
          Të gjithë studentët
        </Link>
      </Button>

      <PageHeader title={student.full_name} description={student.email}>
        {student.is_active ? (
          <Badge variant="success">Aktiv</Badge>
        ) : (
          <Badge variant="outline">Joaktiv</Badge>
        )}
      </PageHeader>

      {error ? <ErrorState message={error} /> : null}

      {notice ? (
        <Alert variant="success">
          <AlertDescription>{notice}</AlertDescription>
        </Alert>
      ) : null}

      {student.student_profile_id === null ? (
        <Alert>
          <AlertDescription>
            Ky student ende nuk e ka plotësuar profilin akademik. Pas
            kyçjes së parë i kërkohet programi, viti dhe semestri; lëndët
            mund t&apos;i shtohen pas kësaj.
          </AlertDescription>
        </Alert>
      ) : (
        <>
          <Card>
            <CardContent className="grid gap-4 p-6 sm:grid-cols-5">
              {[
                ["Numri i studentit", student.student_number],
                ["Programi", student.program_name],
                ["Viti i studimit / Semestri", `${student.study_year} / ${student.semester}`],
                ["Lëndë aktive", `${student.course_count} (${totalEcts} ECTS)`],
                ["ECTS të fituara", String(earnedEcts)],
              ].map(([label, value]) => (
                <div key={label}>
                  <p className="text-sm text-muted-foreground">{label}</p>
                  <p className="font-medium">{value ?? "—"}</p>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Lëndët dhe grupet</CardTitle>
              <CardDescription>
                Grupi përcakton profesorin dhe ushtrimet e studentit te
                lëndët që jepen nga disa profesorë.
              </CardDescription>
            </CardHeader>

            <CardContent className="overflow-x-auto px-0">
              {student.courses.length === 0 ? (
                <p className="px-6 pb-4 text-sm text-muted-foreground">
                  Nuk është i regjistruar në asnjë lëndë.
                </p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Sem.</TableHead>
                      <TableHead>Lënda</TableHead>
                      <TableHead>Periudha</TableHead>
                      <TableHead>ECTS</TableHead>
                      <TableHead>Grupi</TableHead>
                      <TableHead>Profesori</TableHead>
                      <TableHead />
                    </TableRow>
                  </TableHeader>

                  <TableBody>
                    {student.courses.map((course) => {
                      const options = groupsOf(course.course_id);

                      return (
                        <TableRow key={course.enrollment_id}>
                          <TableCell className="tabular-nums">
                            {course.semester}
                          </TableCell>
                          <TableCell>
                            <span className="font-medium">{course.code}</span>{" "}
                            {course.name}
                          </TableCell>
                          <TableCell className="text-xs">
                            {course.period_label ?? "—"}
                            {course.status === "COMPLETED" ? (
                              <Badge variant="success" className="ml-2">
                                E përfunduar
                              </Badge>
                            ) : null}
                          </TableCell>
                          <TableCell className="tabular-nums">{course.ects}</TableCell>

                          <TableCell>
                            {options.length === 0 ? (
                              <span className="text-muted-foreground">Pa grupe</span>
                            ) : (
                              <Select
                                value={
                                  course.group_id === null
                                    ? NO_GROUP
                                    : String(course.group_id)
                                }
                                onValueChange={(value) =>
                                  void run(
                                    course.enrollment_id,
                                    () =>
                                      admin.changeGroup(
                                        course.enrollment_id,
                                        value === NO_GROUP ? null : Number(value),
                                      ),
                                    `Grupi te ${course.code} u ndryshua.`,
                                  )
                                }
                                disabled={busy === course.enrollment_id}
                              >
                                <SelectTrigger className="h-8 w-56 text-xs">
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value={NO_GROUP}>Pa grup</SelectItem>
                                  {options.map((group) => (
                                    <SelectItem key={group.id} value={String(group.id)}>
                                      {group.name}
                                      {group.professor_name
                                        ? ` — ${group.professor_name}`
                                        : ""}
                                    </SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                            )}
                          </TableCell>

                          <TableCell>{course.teacher_name ?? "—"}</TableCell>

                          <TableCell>
                            <div className="flex justify-end gap-1">
                              {confirmId === course.enrollment_id ? (
                                <>
                                  <Button
                                    variant="destructive"
                                    size="sm"
                                    disabled={busy === course.enrollment_id}
                                    onClick={() =>
                                      void run(
                                        course.enrollment_id,
                                        () => admin.unenroll(course.enrollment_id),
                                        `${course.code} u hoq.`,
                                      ).then((ok) => ok && setConfirmId(null))
                                    }
                                  >
                                    Hiq lëndën
                                  </Button>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="size-8"
                                    onClick={() => setConfirmId(null)}
                                    aria-label="Anulo"
                                  >
                                    <X className="size-3.5" />
                                  </Button>
                                </>
                              ) : (
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="size-8 text-destructive"
                                  onClick={() => setConfirmId(course.enrollment_id)}
                                  aria-label={`Hiq ${course.code}`}
                                  title="Hiq lëndën"
                                >
                                  <Trash2 className="size-3.5" />
                                </Button>
                              )}
                            </div>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Shto lëndë</CardTitle>
              <CardDescription>
                Lëndët e programit “{student.program_name}” ku studenti ende
                nuk është i regjistruar.
              </CardDescription>
            </CardHeader>

            <CardContent className="flex flex-wrap items-end gap-3">
              <div className="w-full space-y-1 sm:w-96">
                <Label htmlFor="new-course">Lënda</Label>
                <Select
                  value={newCourse}
                  onValueChange={(value) => {
                    setNewCourse(value);
                    setNewGroup(AUTO);
                  }}
                >
                  <SelectTrigger id="new-course">
                    <SelectValue placeholder="Zgjidh lëndën" />
                  </SelectTrigger>
                  <SelectContent>
                    {available.map((course) => (
                      <SelectItem key={course.id} value={String(course.id)}>
                        Sem {course.semester} · {course.code} — {course.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="w-full space-y-1 sm:w-72">
                <Label htmlFor="new-group">Grupi</Label>
                <Select
                  value={newGroup}
                  onValueChange={setNewGroup}
                  disabled={!newCourse}
                >
                  <SelectTrigger id="new-group">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={AUTO}>
                      Automatik (grupi me më pak studentë)
                    </SelectItem>
                    {newCourse
                      ? groupsOf(Number(newCourse)).map((group) => (
                          <SelectItem key={group.id} value={String(group.id)}>
                            {group.name}
                            {group.professor_name ? ` — ${group.professor_name}` : ""}
                            {` (${group.student_count})`}
                          </SelectItem>
                        ))
                      : null}
                  </SelectContent>
                </Select>
              </div>

              <Button onClick={addCourse} disabled={!newCourse || busy === "add"}>
                {busy === "add" ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <Plus className="size-4" />
                )}
                Shto
              </Button>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
