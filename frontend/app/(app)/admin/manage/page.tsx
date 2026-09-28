"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import {
  NONE,
  ResourceManager,
  type FieldDef,
  type FormValues,
} from "@/components/admin/resource-manager";
import { UsersManager } from "@/components/admin/users-manager";
import { PageHeader } from "@/components/layout/page-header";
import { ErrorState, LoadingState } from "@/components/layout/states";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { admin, api } from "@/lib/api";
import type {
  Course,
  Deadline,
  Exam,
  Notification,
  Professor,
  Program,
  Schedule,
} from "@/lib/types";
import {
  DAY_LABELS,
  DAY_ORDER,
  formatDateTime,
  formatTime,
} from "@/lib/utils";

const EXAM_TYPES = [
  { value: "MIDTERM", label: "Provim i ndërmjetëm" },
  { value: "FINAL", label: "Provim final" },
  { value: "RETAKE", label: "Riprovim" },
];

const DEADLINE_TYPES = [
  { value: "REGISTRATION", label: "Regjistrim" },
  { value: "PAYMENT", label: "Pagesë" },
  { value: "GRADUATION", label: "Diplomim" },
  { value: "EVENT", label: "Event" },
  { value: "OTHER", label: "Tjetër" },
];

const SEVERITIES = [
  { value: "INFO", label: "Informacion" },
  { value: "WARNING", label: "Paralajmërim" },
  { value: "URGENT", label: "Urgjent" },
];

const ACTIVE_OPTIONS = [
  { value: "true", label: "Aktiv" },
  { value: "false", label: "Joaktiv" },
];

const DAY_OPTIONS = DAY_ORDER.map((day) => ({
  value: day,
  label: DAY_LABELS[day],
}));

function labelOf(options: { value: string; label: string }[], value: string) {
  return options.find((option) => option.value === value)?.label ?? value;
}

// --- Konvertimet mes formës (tekst) dhe API-t -----------------------

function optionalText(value: string): string | null {
  return value.trim() ? value.trim() : null;
}

function optionalId(value: string): number | null {
  return !value || value === NONE ? null : Number(value);
}

function idOrNone(value: number | null): string {
  return value === null ? NONE : String(value);
}

/** "09:00" nga input-i -> "09:00:00" për API-në. */
function toApiTime(value: string): string {
  return value.length === 5 ? `${value}:00` : value;
}

/** "2026-10-08T09:00:00" -> "2026-10-08T09:00" për datetime-local. */
function toInputDateTime(value: string): string {
  return value.slice(0, 16);
}

function toApiDateTime(value: string): string {
  return value.length === 16 ? `${value}:00` : value;
}

// Renditjet jashtë komponentit: referenca e qëndrueshme nuk e rinis
// ngarkimin e listës në çdo render.
const byCode = (a: Course, b: Course) => a.code.localeCompare(b.code);

const byDayAndTime = (a: Schedule, b: Schedule) =>
  DAY_ORDER.indexOf(a.day_of_week) - DAY_ORDER.indexOf(b.day_of_week) ||
  a.start_time.localeCompare(b.start_time);

const byExamDate = (a: Exam, b: Exam) =>
  a.exam_date.localeCompare(b.exam_date);

const byDueDate = (a: Deadline, b: Deadline) =>
  a.due_date.localeCompare(b.due_date);

const newestFirst = (a: Notification, b: Notification) =>
  b.created_at.localeCompare(a.created_at);

export default function ManagePage() {
  const [courses, setCourses] = useState<Course[] | null>(null);
  const [programs, setPrograms] = useState<Program[]>([]);
  const [professors, setProfessors] = useState<Professor[]>([]);
  const [error, setError] = useState<string | null>(null);

  const loadLookups = useCallback(async () => {
    try {
      const [loadedCourses, loadedPrograms, loadedProfessors] =
        await Promise.all([
          admin.courses.list(),
          admin.programs.list(),
          api.professors(),
        ]);

      setCourses([...loadedCourses].sort(byCode));
      setPrograms(loadedPrograms);
      setProfessors(loadedProfessors);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Të dhënat nuk u ngarkuan.",
      );
    }
  }, []);

  useEffect(() => {
    void loadLookups();
  }, [loadLookups]);

  const courseOptions = useMemo(
    () =>
      (courses ?? []).map((course) => ({
        value: String(course.id),
        label: `${course.code} — ${course.name}`,
      })),
    [courses],
  );

  const programOptions = useMemo(
    () =>
      programs.map((program) => ({
        value: String(program.id),
        label: program.name,
      })),
    [programs],
  );

  const professorOptions = useMemo(
    () => [
      { value: NONE, label: "Pa profesor" },
      ...professors.map((professor) => ({
        value: String(professor.id),
        label: professor.full_name,
      })),
    ],
    [professors],
  );

  if (!courses) {
    return error ? <ErrorState message={error} /> : <LoadingState />;
  }

  const courseCode = (id: number) =>
    courses.find((course) => course.id === id)?.code ?? `#${id}`;

  const programName = (id: number | null) =>
    id === null
      ? "Të gjitha programet"
      : programs.find((program) => program.id === id)?.name ?? `#${id}`;

  const professorName = (id: number | null) =>
    id === null
      ? "—"
      : professors.find((professor) => professor.id === id)?.full_name ??
        `#${id}`;

  const courseFields: FieldDef[] = [
    { name: "code", label: "Kodi", type: "text", required: true, placeholder: "CS301" },
    { name: "name", label: "Emri", type: "text", required: true },
    { name: "ects", label: "ECTS", type: "number", required: true },
    { name: "semester", label: "Semestri", type: "number", required: true },
    { name: "program_id", label: "Programi", type: "select", required: true, options: programOptions },
    { name: "professor_id", label: "Profesori", type: "select", options: professorOptions },
    { name: "description", label: "Përshkrimi", type: "textarea", wide: true },
    { name: "syllabus", label: "Syllabus-i", type: "textarea", wide: true },
  ];

  const scheduleFields: FieldDef[] = [
    { name: "course_id", label: "Lënda", type: "select", required: true, options: courseOptions },
    { name: "day_of_week", label: "Dita", type: "select", required: true, options: DAY_OPTIONS },
    { name: "start_time", label: "Fillon", type: "time", required: true },
    { name: "end_time", label: "Mbaron", type: "time", required: true },
    { name: "room", label: "Salla", type: "text", placeholder: "A-201" },
  ];

  const examFields: FieldDef[] = [
    { name: "course_id", label: "Lënda", type: "select", required: true, options: courseOptions },
    { name: "exam_type", label: "Lloji", type: "select", required: true, options: EXAM_TYPES },
    { name: "exam_date", label: "Data dhe ora", type: "datetime", required: true },
    { name: "room", label: "Salla", type: "text", placeholder: "A-201" },
  ];

  const deadlineFields: FieldDef[] = [
    { name: "title", label: "Titulli", type: "text", required: true },
    { name: "deadline_type", label: "Lloji", type: "select", required: true, options: DEADLINE_TYPES },
    { name: "due_date", label: "Afati", type: "datetime", required: true },
    {
      name: "program_id",
      label: "Programi",
      type: "select",
      options: [{ value: NONE, label: "Të gjitha programet" }, ...programOptions],
    },
    { name: "description", label: "Përshkrimi", type: "textarea", wide: true },
  ];

  const notificationFields: FieldDef[] = [
    { name: "title", label: "Titulli", type: "text", required: true },
    { name: "severity", label: "Rëndësia", type: "select", required: true, options: SEVERITIES },
    {
      name: "program_id",
      label: "Për programin",
      type: "select",
      options: [{ value: NONE, label: "Të gjitha programet" }, ...programOptions],
    },
    { name: "is_active", label: "Statusi", type: "select", options: ACTIVE_OPTIONS, editOnly: true },
    { name: "body", label: "Teksti", type: "textarea", required: true, wide: true },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Menaxhimi akademik"
        description="Lëndët, orari, provimet, afatet, njoftimet dhe llogaritë. Ndryshimet i sheh menjëherë edhe asistenti AI."
      />

      <Tabs defaultValue="courses" className="space-y-6">
        <TabsList className="h-auto flex-wrap justify-start">
          <TabsTrigger value="courses">Lëndët</TabsTrigger>
          <TabsTrigger value="schedules">Orari</TabsTrigger>
          <TabsTrigger value="exams">Provimet</TabsTrigger>
          <TabsTrigger value="deadlines">Afatet</TabsTrigger>
          <TabsTrigger value="notifications">Njoftimet</TabsTrigger>
          <TabsTrigger value="users">Përdoruesit</TabsTrigger>
        </TabsList>

        <TabsContent value="courses">
          <ResourceManager<Course>
            title="Lëndët"
            description="Katalogu i lëndëve me ECTS, profesorin dhe syllabus-in."
            singular="lëndë"
            resource={admin.courses}
            fields={courseFields}
            sort={byCode}
            onChange={() => void loadLookups()}
            deleteWarning="Fshirja e lëndës fshin edhe orarin, provimet dhe regjistrimet e studentëve në të. Veprimi nuk kthehet mbrapsht."
            emptyForm={{
              code: "",
              name: "",
              ects: "6",
              semester: "1",
              program_id: programOptions[0]?.value ?? "",
              professor_id: NONE,
              description: "",
              syllabus: "",
            }}
            toForm={(course) => ({
              code: course.code,
              name: course.name,
              ects: String(course.ects),
              semester: String(course.semester),
              program_id: String(course.program_id),
              professor_id: idOrNone(course.professor_id),
              description: course.description ?? "",
              syllabus: course.syllabus ?? "",
            })}
            toPayload={(values: FormValues) => ({
              code: values.code.trim(),
              name: values.name.trim(),
              ects: Number(values.ects),
              semester: Number(values.semester),
              program_id: Number(values.program_id),
              professor_id: optionalId(values.professor_id),
              description: optionalText(values.description),
              syllabus: optionalText(values.syllabus),
            })}
            columns={[
              { header: "Kodi", cell: (course) => <span className="font-medium">{course.code}</span> },
              { header: "Emri", cell: (course) => course.name },
              { header: "ECTS", cell: (course) => course.ects, className: "tabular-nums" },
              { header: "Sem.", cell: (course) => course.semester, className: "tabular-nums" },
              { header: "Profesori", cell: (course) => professorName(course.professor_id) },
            ]}
          />
        </TabsContent>

        <TabsContent value="schedules">
          <ResourceManager<Schedule>
            title="Orari javor"
            description="Ligjëratat e çdo lënde sipas ditës dhe orës."
            singular="orar"
            resource={admin.schedules}
            fields={scheduleFields}
            sort={byDayAndTime}
            emptyForm={{
              course_id: courseOptions[0]?.value ?? "",
              day_of_week: "Monday",
              start_time: "09:00",
              end_time: "10:30",
              room: "",
            }}
            toForm={(slot) => ({
              course_id: String(slot.course_id),
              day_of_week: slot.day_of_week,
              start_time: formatTime(slot.start_time),
              end_time: formatTime(slot.end_time),
              room: slot.room ?? "",
            })}
            toPayload={(values) => ({
              course_id: Number(values.course_id),
              day_of_week: values.day_of_week,
              start_time: toApiTime(values.start_time),
              end_time: toApiTime(values.end_time),
              room: optionalText(values.room),
            })}
            columns={[
              { header: "Dita", cell: (slot) => DAY_LABELS[slot.day_of_week] ?? slot.day_of_week },
              {
                header: "Ora",
                cell: (slot) => `${formatTime(slot.start_time)}–${formatTime(slot.end_time)}`,
                className: "tabular-nums",
              },
              { header: "Lënda", cell: (slot) => courseCode(slot.course_id) },
              { header: "Salla", cell: (slot) => slot.room ?? "—" },
            ]}
          />
        </TabsContent>

        <TabsContent value="exams">
          <ResourceManager<Exam>
            title="Provimet"
            description="Afatet e provimeve për secilën lëndë."
            singular="provim"
            resource={admin.exams}
            fields={examFields}
            sort={byExamDate}
            emptyForm={{
              course_id: courseOptions[0]?.value ?? "",
              exam_type: "FINAL",
              exam_date: "",
              room: "",
            }}
            toForm={(exam) => ({
              course_id: String(exam.course_id),
              exam_type: exam.exam_type,
              exam_date: toInputDateTime(exam.exam_date),
              room: exam.room ?? "",
            })}
            toPayload={(values) => ({
              course_id: Number(values.course_id),
              exam_type: values.exam_type,
              exam_date: toApiDateTime(values.exam_date),
              room: optionalText(values.room),
            })}
            columns={[
              { header: "Data", cell: (exam) => formatDateTime(exam.exam_date), className: "tabular-nums" },
              { header: "Lënda", cell: (exam) => courseCode(exam.course_id) },
              {
                header: "Lloji",
                cell: (exam) => <Badge variant="outline">{labelOf(EXAM_TYPES, exam.exam_type)}</Badge>,
              },
              { header: "Salla", cell: (exam) => exam.room ?? "—" },
            ]}
          />
        </TabsContent>

        <TabsContent value="deadlines">
          <ResourceManager<Deadline>
            title="Afatet administrative"
            description="Regjistrimet, pagesat dhe afatet e tjera që u shfaqen studentëve."
            singular="afat"
            resource={admin.deadlines}
            fields={deadlineFields}
            sort={byDueDate}
            emptyForm={{
              title: "",
              deadline_type: "REGISTRATION",
              due_date: "",
              program_id: NONE,
              description: "",
            }}
            toForm={(deadline) => ({
              title: deadline.title,
              deadline_type: deadline.deadline_type,
              due_date: toInputDateTime(deadline.due_date),
              program_id: idOrNone(deadline.program_id),
              description: deadline.description ?? "",
            })}
            toPayload={(values) => ({
              title: values.title.trim(),
              deadline_type: values.deadline_type,
              due_date: toApiDateTime(values.due_date),
              program_id: optionalId(values.program_id),
              description: optionalText(values.description),
            })}
            columns={[
              { header: "Afati", cell: (deadline) => formatDateTime(deadline.due_date), className: "tabular-nums" },
              { header: "Titulli", cell: (deadline) => <span className="font-medium">{deadline.title}</span> },
              {
                header: "Lloji",
                cell: (deadline) => (
                  <Badge variant="outline">{labelOf(DEADLINE_TYPES, deadline.deadline_type)}</Badge>
                ),
              },
              { header: "Programi", cell: (deadline) => programName(deadline.program_id) },
            ]}
          />
        </TabsContent>

        <TabsContent value="notifications">
          <ResourceManager<Notification>
            title="Njoftimet"
            description="Njoftimet aktive u shfaqen studentëve te paneli dhe i lexon edhe asistenti."
            singular="njoftim"
            resource={admin.notifications}
            fields={notificationFields}
            sort={newestFirst}
            emptyForm={{
              title: "",
              severity: "INFO",
              program_id: NONE,
              is_active: "true",
              body: "",
            }}
            toForm={(notification) => ({
              title: notification.title,
              severity: notification.severity,
              program_id: idOrNone(notification.program_id),
              is_active: String(notification.is_active),
              body: notification.body,
            })}
            toPayload={(values) => ({
              title: values.title.trim(),
              severity: values.severity,
              program_id: optionalId(values.program_id),
              body: values.body.trim(),
              // `NotificationCreate` e injoron; njoftimi i ri është gjithmonë aktiv.
              is_active: values.is_active === "true",
            })}
            columns={[
              { header: "Titulli", cell: (notification) => <span className="font-medium">{notification.title}</span> },
              {
                header: "Rëndësia",
                cell: (notification) => (
                  <Badge variant={notification.severity === "INFO" ? "secondary" : "warning"}>
                    {labelOf(SEVERITIES, notification.severity)}
                  </Badge>
                ),
              },
              { header: "Programi", cell: (notification) => programName(notification.program_id) },
              {
                header: "Statusi",
                cell: (notification) =>
                  notification.is_active ? (
                    <Badge variant="success">Aktiv</Badge>
                  ) : (
                    <Badge variant="outline">Joaktiv</Badge>
                  ),
              },
            ]}
          />
        </TabsContent>

        <TabsContent value="users">
          <UsersManager />
        </TabsContent>
      </Tabs>
    </div>
  );
}
