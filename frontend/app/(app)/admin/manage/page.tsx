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
  AcademicPeriod,
  Course,
  CourseGroup,
  Deadline,
  Exam,
  Faculty,
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

const ECTS_STATUS = [
  { value: "false", label: "Demonstrative" },
  { value: "true", label: "Zyrtare" },
];

const TERMS = [
  { value: "WINTER", label: "Dimërore (semestrat tek)" },
  { value: "SUMMER", label: "Verore (semestrat çift)" },
];

const CURRENT_OPTIONS = [
  { value: "false", label: "Jo" },
  { value: "true", label: "Po, periudha aktuale" },
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

const byName = (a: { name: string }, b: { name: string }) =>
  a.name.localeCompare(b.name);

const byLastName = (a: Professor, b: Professor) =>
  a.last_name.localeCompare(b.last_name) ||
  a.first_name.localeCompare(b.first_name);

const byPeriod = (a: AcademicPeriod, b: AcademicPeriod) =>
  b.start_date.localeCompare(a.start_date);

const byGroup = (a: CourseGroup, b: CourseGroup) =>
  (a.course_code ?? "").localeCompare(b.course_code ?? "") ||
  a.name.localeCompare(b.name);

const DEGREE_LEVELS = [
  { value: "BACHELOR", label: "Bachelor" },
  { value: "MASTER", label: "Master" },
  { value: "PHD", label: "Doktoraturë" },
];

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
  const [faculties, setFaculties] = useState<Faculty[]>([]);
  const [groups, setGroups] = useState<CourseGroup[]>([]);
  const [error, setError] = useState<string | null>(null);

  const loadLookups = useCallback(async () => {
    try {
      const [
        loadedCourses,
        loadedPrograms,
        loadedProfessors,
        loadedFaculties,
        loadedGroups,
      ] = await Promise.all([
        admin.courses.list(),
        admin.programs.list(),
        admin.professors.list(),
        admin.faculties.list(),
        admin.courseGroups.list(),
      ]);

      setGroups(loadedGroups);
      setFaculties([...loadedFaculties].sort(byName));
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

  const facultyOptions = useMemo(
    () => [
      { value: NONE, label: "Pa fakultet" },
      ...faculties.map((faculty) => ({
        value: String(faculty.id),
        label: faculty.name,
      })),
    ],
    [faculties],
  );

  const groupOptions = useMemo(
    () => [
      { value: NONE, label: "Gjithë lënda (e përbashkët)" },
      ...groups.map((group) => ({
        value: String(group.id),
        label: `${group.course_code} · ${group.name}${
          group.professor_name ? ` — ${group.professor_name}` : ""
        }`,
      })),
    ],
    [groups],
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

  const facultyName = (id: number | null) =>
    id === null
      ? "—"
      : faculties.find((faculty) => faculty.id === id)?.name ?? `#${id}`;

  const programLabel = (id: number) =>
    programs.find((program) => program.id === id)?.name ?? `#${id}`;

  const facultyFields: FieldDef[] = [
    { name: "name", label: "Emri", type: "text", required: true, wide: true },
    { name: "description", label: "Përshkrimi", type: "textarea", wide: true },
  ];

  const programFields: FieldDef[] = [
    { name: "name", label: "Emri", type: "text", required: true },
    { name: "faculty_id", label: "Fakulteti", type: "select", options: facultyOptions },
    { name: "degree_level", label: "Niveli", type: "select", required: true, options: DEGREE_LEVELS },
    { name: "specialization", label: "Drejtimi", type: "text" },
    { name: "total_ects", label: "ECTS gjithsej", type: "number", required: true },
    { name: "ects_is_official", label: "ECTS-të e lëndëve", type: "select", options: ECTS_STATUS },
    { name: "duration_years", label: "Kohëzgjatja (vite)", type: "number", required: true },
    { name: "description", label: "Përshkrimi", type: "textarea", wide: true },
  ];

  const periodFields: FieldDef[] = [
    { name: "academic_year", label: "Viti akademik", type: "text", required: true, placeholder: "2026/2027" },
    { name: "term", label: "Periudha", type: "select", required: true, options: TERMS },
    { name: "start_date", label: "Fillimi", type: "date", required: true },
    { name: "end_date", label: "Mbarimi", type: "date", required: true },
    { name: "is_current", label: "Aktuale", type: "select", options: CURRENT_OPTIONS },
  ];

  const professorFields: FieldDef[] = [
    { name: "first_name", label: "Emri", type: "text", required: true },
    { name: "last_name", label: "Mbiemri", type: "text", required: true },
    { name: "title", label: "Titulli", type: "text", placeholder: "Prof. Dr." },
    { name: "email", label: "Email-i (për kyçje)", type: "email" },
    { name: "faculty_id", label: "Fakulteti", type: "select", options: facultyOptions },
    { name: "office", label: "Zyra", type: "text", placeholder: "B-210" },
    {
      name: "password",
      label: "Fjalëkalimi i llogarisë",
      type: "password",
      placeholder: "Bosh: pa llogari / pa ndryshim",
    },
    { name: "consultation_hours", label: "Konsultimet", type: "text", placeholder: "E martë 12:00-14:00" },
  ];

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

  const groupName = (id: number | null) =>
    id === null ? "E përbashkët" : groups.find((group) => group.id === id)?.name ?? `#${id}`;

  const groupFields: FieldDef[] = [
    { name: "course_id", label: "Lënda", type: "select", required: true, options: courseOptions },
    { name: "name", label: "Emri i grupit", type: "text", required: true, placeholder: "Grupi B" },
    { name: "professor_id", label: "Profesori", type: "select", options: professorOptions },
    { name: "capacity", label: "Kapaciteti", type: "number", placeholder: "Pa kufi" },
  ];

  const scheduleFields: FieldDef[] = [
    { name: "course_id", label: "Lënda", type: "select", required: true, options: courseOptions },
    { name: "group_id", label: "Grupi", type: "select", options: groupOptions },
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
          <TabsTrigger value="faculties">Fakultetet</TabsTrigger>
          <TabsTrigger value="programs">Programet</TabsTrigger>
          <TabsTrigger value="periods">Periudhat</TabsTrigger>
          <TabsTrigger value="professors">Profesorët</TabsTrigger>
          <TabsTrigger value="courses">Lëndët</TabsTrigger>
          <TabsTrigger value="groups">Grupet</TabsTrigger>
          <TabsTrigger value="schedules">Orari</TabsTrigger>
          <TabsTrigger value="exams">Provimet</TabsTrigger>
          <TabsTrigger value="deadlines">Afatet</TabsTrigger>
          <TabsTrigger value="notifications">Njoftimet</TabsTrigger>
          <TabsTrigger value="users">Përdoruesit</TabsTrigger>
        </TabsList>

        <TabsContent value="faculties">
          <ResourceManager<Faculty>
            title="Fakultetet"
            description="Çdo fakultet ka programet dhe dokumentet e veta; studentët kërkojnë vetëm te dokumentet e fakultetit të tyre."
            singular="fakultet"
            resource={admin.faculties}
            fields={facultyFields}
            sort={byName}
            onChange={() => void loadLookups()}
            deleteWarning="Programet dhe profesorët e këtij fakulteti mbeten, por pa fakultet, dhe dokumentet e tij kalojnë te gjithë universiteti."
            emptyForm={{ name: "", description: "" }}
            toForm={(faculty) => ({
              name: faculty.name,
              description: faculty.description ?? "",
            })}
            toPayload={(values) => ({
              name: values.name.trim(),
              description: optionalText(values.description),
            })}
            columns={[
              { header: "Fakulteti", cell: (faculty) => <span className="font-medium">{faculty.name}</span> },
              {
                header: "Programe",
                cell: (faculty) =>
                  programs.filter((program) => program.faculty_id === faculty.id).length,
                className: "tabular-nums",
              },
            ]}
          />
        </TabsContent>

        <TabsContent value="programs">
          <ResourceManager<Program>
            title="Programet e studimit"
            description="Programi lidh studentët dhe lëndët me fakultetin."
            singular="program"
            resource={admin.programs}
            fields={programFields}
            sort={byName}
            onChange={() => void loadLookups()}
            deleteWarning="Fshirja e programit fshin edhe lëndët e tij, me orarin, provimet dhe regjistrimet e tyre."
            emptyForm={{
              name: "",
              faculty_id: facultyOptions[1]?.value ?? NONE,
              degree_level: "BACHELOR",
              specialization: "",
              total_ects: "180",
              ects_is_official: "false",
              duration_years: "3",
              description: "",
            }}
            toForm={(program) => ({
              name: program.name,
              faculty_id: idOrNone(program.faculty_id),
              degree_level: program.degree_level,
              specialization: program.specialization ?? "",
              total_ects: String(program.total_ects),
              ects_is_official: String(program.ects_is_official),
              duration_years: String(program.duration_years),
              description: program.description ?? "",
            })}
            toPayload={(values) => ({
              name: values.name.trim(),
              faculty_id: optionalId(values.faculty_id),
              degree_level: values.degree_level,
              specialization: optionalText(values.specialization),
              total_ects: Number(values.total_ects),
              ects_is_official: values.ects_is_official === "true",
              duration_years: Number(values.duration_years),
              description: optionalText(values.description),
            })}
            columns={[
              { header: "Programi", cell: (program) => <span className="font-medium">{program.name}</span> },
              { header: "Fakulteti", cell: (program) => facultyName(program.faculty_id) },
              { header: "Niveli", cell: (program) => labelOf(DEGREE_LEVELS, program.degree_level) },
              {
                header: "ECTS",
                cell: (program) => (
                  <span className="tabular-nums">
                    {program.total_ects}{" "}
                    {program.ects_is_official ? null : (
                      <Badge variant="outline">demonstrative</Badge>
                    )}
                  </span>
                ),
              },
              {
                header: "Semestra",
                cell: (program) => program.duration_years * 2,
                className: "tabular-nums",
              },
              {
                header: "Lëndë",
                cell: (program) =>
                  (courses ?? []).filter((course) => course.program_id === program.id).length,
                className: "tabular-nums",
              },
            ]}
          />
        </TabsContent>

        <TabsContent value="periods">
          <ResourceManager<AcademicPeriod>
            title="Periudhat akademike"
            description="Viti akademik (p.sh. 2026/2027) ndahet në periudhën dimërore, ku mbahen semestrat tek, dhe atë verore, ku mbahen semestrat çift. Regjistrimet e reja marrin periudhën e vitit akademik aktual që i përgjigjet semestrit të lëndës."
            singular="periudhë"
            resource={admin.periods}
            fields={periodFields}
            sort={byPeriod}
            deleteWarning="Regjistrimet mbeten, por pa periudhë."
            emptyForm={{
              academic_year: "",
              term: "WINTER",
              start_date: "",
              end_date: "",
              is_current: "false",
            }}
            toForm={(period) => ({
              academic_year: period.academic_year,
              term: period.term,
              start_date: period.start_date,
              end_date: period.end_date,
              is_current: String(period.is_current),
            })}
            toPayload={(values) => ({
              academic_year: values.academic_year.trim(),
              term: values.term,
              start_date: values.start_date,
              end_date: values.end_date,
              is_current: values.is_current === "true",
            })}
            columns={[
              { header: "Viti akademik", cell: (period) => <span className="font-medium">{period.academic_year}</span> },
              { header: "Periudha", cell: (period) => labelOf(TERMS, period.term) },
              {
                header: "Kohëzgjatja",
                cell: (period) => `${period.start_date} – ${period.end_date}`,
                className: "tabular-nums",
              },
              {
                header: "Statusi",
                cell: (period) =>
                  period.is_current ? <Badge variant="success">Aktuale</Badge> : null,
              },
            ]}
          />
        </TabsContent>

        <TabsContent value="professors">
          <ResourceManager<Professor>
            title="Profesorët"
            description="Me fjalëkalim krijohet edhe llogaria e kyçjes, me të cilën profesori sheh grupet e veta dhe ngarkon materialet e tyre. Fjalëkalimi i ri te ndryshimi e rivendos."
            singular="profesor"
            resource={admin.professors}
            fields={professorFields}
            sort={byLastName}
            onChange={() => void loadLookups()}
            deleteWarning="Lëndët dhe grupet e profesorit mbeten pa profesor, dhe llogaria e tij çaktivizohet (nuk fshihet, që dokumentet e tij të ruhen)."
            emptyForm={{
              first_name: "",
              last_name: "",
              title: "",
              email: "",
              faculty_id: facultyOptions[1]?.value ?? NONE,
              office: "",
              password: "",
              consultation_hours: "",
            }}
            toForm={(professor) => ({
              first_name: professor.first_name,
              last_name: professor.last_name,
              title: professor.title ?? "",
              email: professor.email ?? "",
              faculty_id: idOrNone(professor.faculty_id),
              office: professor.office ?? "",
              password: "",
              consultation_hours: professor.consultation_hours ?? "",
            })}
            toPayload={(values) => ({
              first_name: values.first_name.trim(),
              last_name: values.last_name.trim(),
              title: optionalText(values.title),
              email: optionalText(values.email),
              faculty_id: optionalId(values.faculty_id),
              office: optionalText(values.office),
              consultation_hours: optionalText(values.consultation_hours),
              // Vetëm kur plotësohet: bosh do të thotë "mos e prek llogarinë".
              ...(values.password ? { password: values.password } : {}),
            })}
            columns={[
              {
                header: "Profesori",
                cell: (professor) => (
                  <span className="font-medium">
                    {[professor.title, professor.full_name].filter(Boolean).join(" ")}
                  </span>
                ),
              },
              { header: "Fakulteti", cell: (professor) => facultyName(professor.faculty_id) },
              { header: "Email", cell: (professor) => professor.email ?? "—" },
              {
                header: "Llogaria",
                cell: (professor) =>
                  !professor.has_account ? (
                    <Badge variant="outline">Pa llogari</Badge>
                  ) : professor.account_active ? (
                    <Badge variant="success">Aktive</Badge>
                  ) : (
                    <Badge variant="warning">Joaktive</Badge>
                  ),
              },
            ]}
          />
        </TabsContent>

        <TabsContent value="courses">
          <ResourceManager<Course>
            title="Lëndët"
            description="Katalogu i lëndëve me ECTS, profesorin dhe syllabus-in. Semestri është ai i kurrikulës (1-6): viti i studimit N përmban semestrat 2N-1 dhe 2N. ECTS-të janë demonstrative kur programi nuk i ka shënuar si zyrtare."
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
              { header: "Programi", cell: (course) => programLabel(course.program_id) },
              { header: "ECTS", cell: (course) => course.ects, className: "tabular-nums" },
              {
                header: "Viti / Sem.",
                cell: (course) => `${Math.ceil(course.semester / 2)} / ${course.semester}`,
                className: "tabular-nums",
              },
              { header: "Profesori", cell: (course) => professorName(course.professor_id) },
            ]}
          />
        </TabsContent>

        <TabsContent value="groups">
          <ResourceManager<CourseGroup>
            title="Grupet e lëndëve"
            description="E njëjta lëndë mund të jepet nga disa profesorë, secili te grupi i vet. Studenti sheh profesorin dhe ushtrimet e grupit të tij."
            singular="grup"
            resource={admin.courseGroups}
            fields={groupFields}
            sort={byGroup}
            onChange={() => void loadLookups()}
            deleteWarning="Studentët e grupit mbeten të regjistruar në lëndë, por pa grup; orari i veçantë i grupit fshihet."
            emptyForm={{
              course_id: courseOptions[0]?.value ?? "",
              name: "",
              professor_id: NONE,
              capacity: "",
            }}
            toForm={(group) => ({
              course_id: String(group.course_id),
              name: group.name,
              professor_id: idOrNone(group.professor_id),
              capacity: group.capacity === null ? "" : String(group.capacity),
            })}
            toPayload={(values) => ({
              course_id: Number(values.course_id),
              name: values.name.trim(),
              professor_id: optionalId(values.professor_id),
              capacity: values.capacity.trim() ? Number(values.capacity) : null,
            })}
            columns={[
              { header: "Lënda", cell: (group) => <span className="font-medium">{group.course_code}</span> },
              { header: "Grupi", cell: (group) => group.name },
              { header: "Profesori", cell: (group) => group.professor_name ?? "—" },
              { header: "Studentë", cell: (group) => group.student_count, className: "tabular-nums" },
              {
                header: "Kapaciteti",
                cell: (group) => group.capacity ?? "Pa kufi",
                className: "tabular-nums",
              },
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
              group_id: NONE,
              day_of_week: "Monday",
              start_time: "09:00",
              end_time: "10:30",
              room: "",
            }}
            toForm={(slot) => ({
              course_id: String(slot.course_id),
              group_id: idOrNone(slot.group_id),
              day_of_week: slot.day_of_week,
              start_time: formatTime(slot.start_time),
              end_time: formatTime(slot.end_time),
              room: slot.room ?? "",
            })}
            toPayload={(values) => ({
              course_id: Number(values.course_id),
              group_id: optionalId(values.group_id),
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
              { header: "Grupi", cell: (slot) => groupName(slot.group_id) },
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
