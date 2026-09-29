"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type FormEvent,
} from "react";
import { Loader2, MapPin, RefreshCw, Trash2, Upload, X } from "lucide-react";

import { MaterialsUpload } from "@/components/documents/materials-upload";
import {
  DocumentStatusBadge,
  isInFlight,
} from "@/components/documents/status-badge";
import { PageHeader } from "@/components/layout/page-header";
import {
  EmptyState,
  ErrorState,
  LoadingState,
} from "@/components/layout/states";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
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
import { useAuth } from "@/lib/auth-context";
import type {
  Course,
  CourseGroup,
  Faculty,
  Program,
  UniDocument,
} from "@/lib/types";
import { formatDate } from "@/lib/utils";

const DOCUMENT_TYPES = [
  { value: "REGULATION", label: "Rregullore" },
  { value: "SYLLABUS", label: "Syllabus" },
  { value: "GUIDE", label: "Udhëzues" },
  { value: "ANNOUNCEMENT", label: "Njoftim" },
  { value: "OTHER", label: "Tjetër" },
];

// Sa shpesh rifreskohet lista sa kohë ka dokumente në përpunim.
const POLL_INTERVAL_MS = 3000;

// Radix Select nuk pranon "" si vlerë.
const UNIVERSITY = "__university";
const ALL = "__all";
const NO_COURSE = "__none";

interface Group {
  key: string;
  title: string;
  subtitle?: string;
  documents: UniDocument[];
}

function errorMessage(caught: unknown, fallback: string): string {
  return caught instanceof Error ? caught.message : fallback;
}

export default function DocumentsPage() {
  const { user } = useAuth();

  // Stafi akademik ngarkon dokumente; profesori menaxhon vetëm ato që
  // ka ngarkuar vetë, dhe backend-i e zbaton këtë pavarësisht UI-t.
  const isAdmin = user?.role === "ADMIN";
  const isStaff = isAdmin || user?.role === "PROFESSOR";

  const [documents, setDocuments] = useState<UniDocument[] | null>(null);
  const [faculties, setFaculties] = useState<Faculty[]>([]);
  const [programs, setPrograms] = useState<Program[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [courseGroupList, setCourseGroupList] = useState<CourseGroup[]>([]);

  // Profesori mund të zgjedhë vetëm lëndët që ligjëron.
  const [myCourseIds, setMyCourseIds] = useState<Set<number> | null>(null);

  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const [title, setTitle] = useState("");
  const [documentType, setDocumentType] = useState("REGULATION");
  const [description, setDescription] = useState("");
  const [academicYear, setAcademicYear] = useState("");
  const [uploadFaculty, setUploadFaculty] = useState(UNIVERSITY);
  const [uploadCourse, setUploadCourse] = useState(NO_COURSE);
  const [uploading, setUploading] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);

  const [filterFaculty, setFilterFaculty] = useState(ALL);
  const [filterSemester, setFilterSemester] = useState(ALL);

  // Dokumenti që po i ndryshohet vendi (fakulteti / lënda).
  const [editing, setEditing] = useState<{
    id: number;
    faculty: string;
    course: string;
  } | null>(null);

  const fileRef = useRef<HTMLInputElement>(null);

  const refresh = useCallback(async () => {
    try {
      setDocuments(await api.documents());
    } catch (caught) {
      setError(errorMessage(caught, "Dokumentet nuk u ngarkuan."));
    }
  }, []);

  useEffect(() => {
    void refresh();

    Promise.all([
      admin.faculties.list(),
      admin.programs.list(),
      api.courses(),
      admin.courseGroups.list(),
    ])
      .then(([loadedFaculties, loadedPrograms, loadedCourses, loadedGroups]) => {
        setCourseGroupList(loadedGroups);
        setFaculties(
          [...loadedFaculties].sort((a, b) => a.name.localeCompare(b.name)),
        );
        setPrograms(loadedPrograms);
        setCourses(loadedCourses);
      })
      .catch((caught) =>
        setError(errorMessage(caught, "Fakultetet nuk u ngarkuan.")),
      );
  }, [refresh]);

  useEffect(() => {
    if (user?.role !== "PROFESSOR") {
      return;
    }

    api
      .professorCourses()
      .then((mine) => setMyCourseIds(new Set(mine.map((course) => course.id))))
      .catch(() => setMyCourseIds(new Set()));
  }, [user]);

  // Ingestimi ndodh në sfond, prandaj lista rifreskohet vetë derisa
  // çdo dokument të mbërrijë në një status përfundimtar.
  useEffect(() => {
    if (!documents?.some((document) => isInFlight(document.status))) {
      return;
    }

    const timer = setInterval(() => void refresh(), POLL_INTERVAL_MS);

    return () => clearInterval(timer);
  }, [documents, refresh]);

  const facultyOfCourse = useCallback(
    (course: Course) =>
      programs.find((program) => program.id === course.program_id)
        ?.faculty_id ?? null,
    [programs],
  );

  const courseById = useMemo(
    () => new Map(courses.map((course) => [course.id, course])),
    [courses],
  );

  const facultyName = (id: number | null) =>
    faculties.find((faculty) => faculty.id === id)?.name ?? "Pa fakultet";

  /** Lëndët që mund të zgjidhen, sipas fakultetit dhe rolit. */
  function courseOptions(faculty: string): Course[] {
    return courses
      .filter(
        (course) =>
          faculty === UNIVERSITY ||
          faculty === ALL ||
          String(facultyOfCourse(course)) === faculty,
      )
      .filter((course) => !myCourseIds || myCourseIds.has(course.id))
      .sort(
        (a, b) => a.semester - b.semester || a.code.localeCompare(b.code),
      );
  }

  function scopeOf(faculty: string, course: string) {
    return {
      faculty_id:
        faculty === UNIVERSITY || faculty === ALL ? null : Number(faculty),
      course_id: course === NO_COURSE ? null : Number(course),
    };
  }

  async function handleUpload(event: FormEvent) {
    event.preventDefault();

    const file = fileRef.current?.files?.[0];

    if (!file) {
      setError("Zgjidh një skedar PDF, DOCX ose TXT.");

      return;
    }

    const form = new FormData();
    const scope = scopeOf(uploadFaculty, uploadCourse);

    form.append("title", title);
    form.append("document_type", documentType);
    form.append("file", file);

    if (description) {
      form.append("description", description);
    }

    if (academicYear) {
      form.append("academic_year", academicYear);
    }

    if (scope.faculty_id !== null) {
      form.append("faculty_id", String(scope.faculty_id));
    }

    if (scope.course_id !== null) {
      form.append("course_id", String(scope.course_id));
    }

    setUploading(true);
    setError(null);
    setNotice(null);

    try {
      await api.uploadDocument(form);

      setNotice(
        "Dokumenti u ngarkua. Indeksimi po vazhdon në sfond — " +
          "statusi përditësohet vetë.",
      );

      setTitle("");
      setDescription("");
      setAcademicYear("");
      setUploadCourse(NO_COURSE);

      if (fileRef.current) {
        fileRef.current.value = "";
      }

      await refresh();
    } catch (caught) {
      setError(errorMessage(caught, "Ngarkimi dështoi."));
    } finally {
      setUploading(false);
    }
  }

  async function saveScope() {
    if (!editing) {
      return;
    }

    setBusyId(editing.id);
    setError(null);

    try {
      await api.updateDocumentScope(
        editing.id,
        scopeOf(editing.faculty, editing.course),
      );
      setEditing(null);
      await refresh();
    } catch (caught) {
      setError(errorMessage(caught, "Ndryshimi dështoi."));
    } finally {
      setBusyId(null);
    }
  }

  async function reindex(id: number) {
    setBusyId(id);
    setError(null);

    try {
      await api.reindexDocument(id);
      await refresh();
    } catch (caught) {
      setError(errorMessage(caught, "Ri-indeksimi dështoi."));
    } finally {
      setBusyId(null);
    }
  }

  async function remove(id: number) {
    setBusyId(id);
    setError(null);

    try {
      await api.deleteDocument(id);
      await refresh();
    } catch (caught) {
      setError(errorMessage(caught, "Fshirja dështoi."));
    } finally {
      setBusyId(null);
    }
  }

  /** Universiteti, pastaj çdo fakultet: dokumentet e fakultetit dhe
   * dokumentet e lëndëve sipas semestrit. */
  const groups = useMemo<Group[]>(() => {
    if (!documents) {
      return [];
    }

    const visible = documents.filter((document) => {
      const course = document.course_id
        ? courseById.get(document.course_id)
        : undefined;

      if (filterFaculty === UNIVERSITY && document.faculty_id !== null) {
        return false;
      }

      if (
        filterFaculty !== ALL &&
        filterFaculty !== UNIVERSITY &&
        String(document.faculty_id) !== filterFaculty
      ) {
        return false;
      }

      if (filterSemester !== ALL && String(course?.semester) !== filterSemester) {
        return false;
      }

      return true;
    });

    const result: Group[] = [];

    const university = visible.filter(
      (document) => document.faculty_id === null && document.course_id === null,
    );

    if (university.length) {
      result.push({
        key: "university",
        title: "Gjithë universiteti",
        subtitle: "Të dukshme për të gjithë studentët dhe stafin",
        documents: university,
      });
    }

    for (const faculty of faculties) {
      const own = visible.filter(
        (document) =>
          document.faculty_id === faculty.id && document.course_id === null,
      );

      if (own.length) {
        result.push({
          key: `faculty-${faculty.id}`,
          title: faculty.name,
          subtitle: "Dokumente të fakultetit",
          documents: own,
        });
      }

      const byCourse = new Map<number, UniDocument[]>();

      for (const document of visible) {
        if (document.faculty_id === faculty.id && document.course_id) {
          byCourse.set(document.course_id, [
            ...(byCourse.get(document.course_id) ?? []),
            document,
          ]);
        }
      }

      const courseGroups = [...byCourse.entries()]
        .map(([courseId, list]) => ({ course: courseById.get(courseId), list }))
        .sort(
          (a, b) =>
            (a.course?.semester ?? 0) - (b.course?.semester ?? 0) ||
            (a.course?.code ?? "").localeCompare(b.course?.code ?? ""),
        );

      for (const { course, list } of courseGroups) {
        // Materialet javë pas jave; dokumentet pa javë (syllabus-i) në fund.
        list.sort(
          (a, b) =>
            (a.week ?? 99) - (b.week ?? 99) || a.title.localeCompare(b.title),
        );

        result.push({
          key: `course-${course?.id}`,
          title: course
            ? `Semestri ${course.semester} · ${course.code} — ${course.name}`
            : "Lëndë e panjohur",
          subtitle: faculty.name,
          documents: list,
        });
      }
    }

    // Lëndë në një program pa fakultet: pa këtë grup, dokumentet e tyre
    // nuk do të shfaqeshin askund.
    const orphaned = visible.filter(
      (document) => document.faculty_id === null && document.course_id !== null,
    );

    if (orphaned.length) {
      result.push({
        key: "orphaned",
        title: "Lëndë pa fakultet",
        subtitle: "Lidhe programin e lëndës me një fakultet te Menaxhimi",
        documents: orphaned,
      });
    }

    return result;
  }, [documents, faculties, courseById, filterFaculty, filterSemester]);

  if (!documents) {
    return error ? <ErrorState message={error} /> : <LoadingState />;
  }

  const facultySelectItems = (includeAll: boolean) => (
    <>
      {includeAll ? <SelectItem value={ALL}>Të gjitha</SelectItem> : null}
      <SelectItem value={UNIVERSITY}>Gjithë universiteti</SelectItem>
      {faculties.map((faculty) => (
        <SelectItem key={faculty.id} value={String(faculty.id)}>
          {faculty.name}
        </SelectItem>
      ))}
    </>
  );

  const courseSelectItems = (faculty: string) => (
    <>
      <SelectItem value={NO_COURSE}>
        {faculty === UNIVERSITY ? "—" : "Gjithë fakulteti"}
      </SelectItem>
      {faculty === UNIVERSITY
        ? null
        : courseOptions(faculty).map((course) => (
            <SelectItem key={course.id} value={String(course.id)}>
              Sem {course.semester} · {course.code} — {course.name}
            </SelectItem>
          ))}
    </>
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dokumentet e universitetit"
        description="Rregulloret, syllabuset dhe udhëzuesit që ushqejnë përgjigjet e asistentit. Çdo student kërkon vetëm te dokumentet e universitetit, të fakultetit dhe të lëndëve të programit të vet."
      >
        <Button variant="outline" onClick={() => void refresh()}>
          <RefreshCw className="size-4" />
          Rifresko
        </Button>
      </PageHeader>

      {error ? <ErrorState message={error} /> : null}

      {notice ? (
        <Alert variant="success">
          <AlertDescription>{notice}</AlertDescription>
        </Alert>
      ) : null}

      {isStaff ? (
        <Card>
          <CardHeader>
            <CardTitle>Ngarko dokument</CardTitle>
            <CardDescription>
              Pas ngarkimit nis automatikisht pipeline-i: ekstraktim →
              chunking → embeddings → Qdrant.
            </CardDescription>
          </CardHeader>

          <CardContent>
            <form onSubmit={handleUpload} className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="title">Titulli</Label>
                  <Input
                    id="title"
                    required
                    value={title}
                    onChange={(event) => setTitle(event.target.value)}
                    placeholder="Rregullorja e Studimeve Bachelor"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="type">Lloji</Label>
                  <Select value={documentType} onValueChange={setDocumentType}>
                    <SelectTrigger id="type">
                      <SelectValue />
                    </SelectTrigger>

                    <SelectContent>
                      {DOCUMENT_TYPES.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="faculty">I përket</Label>
                  <Select
                    value={uploadFaculty}
                    onValueChange={(value) => {
                      setUploadFaculty(value);
                      setUploadCourse(NO_COURSE);
                    }}
                  >
                    <SelectTrigger id="faculty">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>{facultySelectItems(false)}</SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="course">Lënda</Label>
                  <Select
                    value={uploadCourse}
                    onValueChange={setUploadCourse}
                    disabled={uploadFaculty === UNIVERSITY}
                  >
                    <SelectTrigger id="course">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>{courseSelectItems(uploadFaculty)}</SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="year">Viti akademik</Label>
                  <Input
                    id="year"
                    value={academicYear}
                    onChange={(event) => setAcademicYear(event.target.value)}
                    placeholder="2025/2026"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="file">Skedari</Label>
                  <Input
                    id="file"
                    type="file"
                    ref={fileRef}
                    accept=".pdf,.docx,.txt"
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Përshkrimi</Label>
                <Input
                  id="description"
                  value={description}
                  onChange={(event) => setDescription(event.target.value)}
                  placeholder="Opsional"
                />
              </div>

              <Button type="submit" disabled={uploading}>
                {uploading ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <Upload className="size-4" />
                )}
                Ngarko
              </Button>
            </form>
          </CardContent>
        </Card>
      ) : null}

      {isStaff ? (
        <MaterialsUpload
          courses={courseOptions(ALL)}
          groups={courseGroupList}
          onUploaded={() => void refresh()}
        />
      ) : null}

      <div className="flex flex-wrap items-end gap-3">
        <div className="w-full space-y-1 sm:w-72">
          <Label htmlFor="filter-faculty">Fakulteti</Label>
          <Select value={filterFaculty} onValueChange={setFilterFaculty}>
            <SelectTrigger id="filter-faculty">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>{facultySelectItems(true)}</SelectContent>
          </Select>
        </div>

        <div className="w-full space-y-1 sm:w-44">
          <Label htmlFor="filter-semester">Semestri</Label>
          <Select value={filterSemester} onValueChange={setFilterSemester}>
            <SelectTrigger id="filter-semester">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL}>Të gjithë</SelectItem>
              {[1, 2, 3, 4, 5, 6].map((semester) => (
                <SelectItem key={semester} value={String(semester)}>
                  Semestri {semester}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <p className="pb-2 text-sm text-muted-foreground">
          {documents.length} dokumente ·{" "}
          {documents.filter((item) => item.status === "INDEXED").length} të
          indeksuara
        </p>
      </div>

      {groups.length === 0 ? (
        <EmptyState
          title="Nuk ka dokumente për këtë filtër"
          description={isStaff ? "Ngarko një dokument më sipër." : undefined}
        />
      ) : (
        groups.map((group) => (
          <Card key={group.key}>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">{group.title}</CardTitle>
              {group.subtitle ? (
                <CardDescription>{group.subtitle}</CardDescription>
              ) : null}
            </CardHeader>

            <CardContent className="overflow-x-auto px-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Dokumenti</TableHead>
                    <TableHead>Lloji</TableHead>
                    <TableHead>Statusi</TableHead>
                    <TableHead>Fragmente</TableHead>
                    <TableHead>Ngarkuar</TableHead>
                    {isStaff ? <TableHead /> : null}
                  </TableRow>
                </TableHeader>

                <TableBody>
                  {group.documents.map((document) => (
                    <TableRow key={document.id}>
                      <TableCell>
                        <p className="font-medium">{document.title}</p>
                        <p className="text-xs text-muted-foreground">
                          {document.file_name}
                          {document.academic_year
                            ? ` · ${document.academic_year}`
                            : ""}
                        </p>

                        {document.status === "FAILED" &&
                        document.status_detail ? (
                          <p className="mt-1 text-xs text-destructive">
                            {document.status_detail}
                          </p>
                        ) : null}

                        {editing?.id === document.id ? (
                          <div className="mt-2 flex flex-wrap items-center gap-2">
                            <Select
                              value={editing.faculty}
                              onValueChange={(value) =>
                                setEditing({
                                  ...editing,
                                  faculty: value,
                                  course: NO_COURSE,
                                })
                              }
                            >
                              <SelectTrigger className="h-8 w-56 text-xs">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>{facultySelectItems(false)}</SelectContent>
                            </Select>

                            <Select
                              value={editing.course}
                              onValueChange={(value) =>
                                setEditing({ ...editing, course: value })
                              }
                              disabled={editing.faculty === UNIVERSITY}
                            >
                              <SelectTrigger className="h-8 w-64 text-xs">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                {courseSelectItems(editing.faculty)}
                              </SelectContent>
                            </Select>

                            <Button
                              size="sm"
                              className="h-8"
                              disabled={busyId === document.id}
                              onClick={() => void saveScope()}
                            >
                              Ruaj
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="size-8"
                              onClick={() => setEditing(null)}
                              aria-label="Anulo"
                            >
                              <X className="size-3.5" />
                            </Button>
                          </div>
                        ) : null}
                      </TableCell>

                      <TableCell className="text-xs uppercase text-muted-foreground">
                        {document.document_type}
                      </TableCell>

                      <TableCell>
                        <DocumentStatusBadge status={document.status} />
                      </TableCell>

                      <TableCell className="tabular-nums">
                        {document.chunk_count}
                      </TableCell>

                      <TableCell className="tabular-nums text-muted-foreground">
                        {formatDate(document.uploaded_at)}
                      </TableCell>

                      {isStaff ? (
                        <TableCell>
                          <div className="flex justify-end gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="size-8"
                              disabled={busyId === document.id}
                              onClick={() =>
                                setEditing({
                                  id: document.id,
                                  faculty:
                                    document.faculty_id === null
                                      ? UNIVERSITY
                                      : String(document.faculty_id),
                                  course:
                                    document.course_id === null
                                      ? NO_COURSE
                                      : String(document.course_id),
                                })
                              }
                              aria-label="Ndrysho vendin"
                              title={`Vendi: ${
                                document.faculty_id === null
                                  ? "gjithë universiteti"
                                  : facultyName(document.faculty_id)
                              }`}
                            >
                              <MapPin className="size-3.5" />
                            </Button>

                            <Button
                              variant="ghost"
                              size="icon"
                              className="size-8"
                              disabled={busyId === document.id}
                              onClick={() => void reindex(document.id)}
                              aria-label="Ri-indekso"
                              title="Ri-indekso"
                            >
                              <RefreshCw className="size-3.5" />
                            </Button>

                            <Button
                              variant="ghost"
                              size="icon"
                              className="size-8 text-destructive"
                              disabled={busyId === document.id}
                              onClick={() => void remove(document.id)}
                              aria-label="Fshi"
                              title="Fshi"
                            >
                              <Trash2 className="size-3.5" />
                            </Button>
                          </div>
                        </TableCell>
                      ) : null}
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
