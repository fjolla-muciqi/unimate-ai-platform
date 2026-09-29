"use client";

import { useRef, useState, type FormEvent } from "react";
import { Loader2, Upload } from "lucide-react";

import { ErrorState } from "@/components/layout/states";
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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { api } from "@/lib/api";
import type { Course, CourseGroup } from "@/lib/types";

const ALL_GROUPS = "__all";
const FROM_NAME = "__name";

const TYPE_LABELS: Record<string, string> = {
  LECTURE: "Ligjëratë",
  EXERCISE: "Ushtrime",
  OTHER: "Material",
};

/** E njëjta logjikë si `naming.py`; vetëm për parashikimin para ngarkimit,
 * sepse java përfundimtare e vendos backend-i. */
function normalize(fileName: string): string {
  return fileName
    .replace(/\.[^.]+$/, "")
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[̀-ͯ]/g, "");
}

function previewWeek(fileName: string): number | null {
  const text = normalize(fileName);
  const prefixed = text.match(
    /(?<![a-z])(?:java|jav|week|wk|w|ligjerata|ligjerate|leksioni|leksion|lecture|ushtrimet|ushtrime|ushtrimi|exercise|lab|tutorial)[\s_\-.]*0*(\d{1,2})(?!\d)/,
  );
  const leading = text.match(/^0*(\d{1,2})(?!\d)/);
  const week = Number((prefixed ?? leading)?.[1]);

  return week >= 1 && week <= 15 ? week : null;
}

function previewType(fileName: string): string | null {
  const text = normalize(fileName);

  if (/ushtrim|exercise|lab|tutorial|detyr/.test(text)) {
    return "EXERCISE";
  }

  if (/ligjerat|leksion|lecture|slides|prezantim/.test(text)) {
    return "LECTURE";
  }

  return null;
}

export function MaterialsUpload({
  courses,
  groups,
  onUploaded,
}: {
  courses: Course[];
  groups: CourseGroup[];
  onUploaded: () => void;
}) {
  const [courseId, setCourseId] = useState("");
  const [groupId, setGroupId] = useState(ALL_GROUPS);
  const [materialType, setMaterialType] = useState(FROM_NAME);
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const fileRef = useRef<HTMLInputElement>(null);

  const courseGroups = groups.filter(
    (group) => String(group.course_id) === courseId,
  );

  const sortedFiles = [...files].sort(
    (a, b) =>
      (previewWeek(a.name) ?? 99) - (previewWeek(b.name) ?? 99) ||
      a.name.localeCompare(b.name),
  );

  const withoutWeek = files.filter((file) => previewWeek(file.name) === null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();

    if (!courseId || files.length === 0) {
      setError("Zgjidh lëndën dhe të paktën një skedar.");

      return;
    }

    const form = new FormData();

    form.append("course_id", courseId);

    if (groupId !== ALL_GROUPS) {
      form.append("group_id", groupId);
    }

    if (materialType !== FROM_NAME) {
      form.append("material_type", materialType);
    }

    for (const file of files) {
      form.append("files", file);
    }

    setUploading(true);
    setError(null);
    setNotice(null);

    try {
      const uploaded = await api.uploadMaterials(form);

      setNotice(
        `${uploaded.length} materiale u ngarkuan. Indeksimi vazhdon në ` +
          "sfond — statusi përditësohet vetë.",
      );
      setFiles([]);

      if (fileRef.current) {
        fileRef.current.value = "";
      }

      onUploaded();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Ngarkimi dështoi.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Ngarko materialet e lëndës</CardTitle>
        <CardDescription>
          Ligjëratat dhe ushtrimet e një lënde njëherësh. Java dhe lloji
          lexohen nga emri i skedarit, p.sh. “Java03_Ligjerata.pdf”.
          Materialet e një grupi i përdorin vetëm studentët e atij grupi.
        </CardDescription>
      </CardHeader>

      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="materials-course">Lënda</Label>
              <Select
                value={courseId}
                onValueChange={(value) => {
                  setCourseId(value);
                  setGroupId(ALL_GROUPS);
                }}
              >
                <SelectTrigger id="materials-course">
                  <SelectValue placeholder="Zgjidh lëndën" />
                </SelectTrigger>
                <SelectContent>
                  {courses.map((course) => (
                    <SelectItem key={course.id} value={String(course.id)}>
                      Sem {course.semester} · {course.code} — {course.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="materials-group">Grupi (profesori)</Label>
              <Select
                value={groupId}
                onValueChange={setGroupId}
                disabled={!courseId}
              >
                <SelectTrigger id="materials-group">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL_GROUPS}>Për të gjitha grupet</SelectItem>
                  {courseGroups.map((group) => (
                    <SelectItem key={group.id} value={String(group.id)}>
                      {group.name}
                      {group.professor_name ? ` — ${group.professor_name}` : ""}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="materials-type">Lloji</Label>
              <Select value={materialType} onValueChange={setMaterialType}>
                <SelectTrigger id="materials-type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={FROM_NAME}>Nga emri i skedarit</SelectItem>
                  <SelectItem value="LECTURE">Ligjëratë</SelectItem>
                  <SelectItem value="EXERCISE">Ushtrime</SelectItem>
                  <SelectItem value="OTHER">Material tjetër</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="materials-files">Skedarët (PDF, DOCX, TXT)</Label>
            <Input
              id="materials-files"
              type="file"
              multiple
              accept=".pdf,.docx,.txt"
              ref={fileRef}
              onChange={(event) =>
                setFiles(Array.from(event.target.files ?? []))
              }
            />
          </div>

          {files.length ? (
            <div className="rounded-md border p-3 text-sm">
              <p className="mb-2 font-medium">
                {files.length} skedarë — si do të emërtohen:
              </p>
              <ul className="space-y-1">
                {sortedFiles.map((file) => {
                  const week = previewWeek(file.name);
                  const kind =
                    previewType(file.name) ??
                    (materialType === FROM_NAME ? null : materialType);

                  return (
                    <li key={file.name} className="flex flex-wrap items-center gap-2">
                      <span className="text-muted-foreground">{file.name}</span>
                      <span aria-hidden>→</span>
                      {week ? (
                        <Badge variant="secondary">Java {week}</Badge>
                      ) : (
                        <Badge variant="warning">pa javë</Badge>
                      )}
                      {kind ? <Badge variant="outline">{TYPE_LABELS[kind]}</Badge> : null}
                    </li>
                  );
                })}
              </ul>

              {withoutWeek.length ? (
                <p className="mt-2 text-xs text-muted-foreground">
                  Skedarët pa javë ngarkohen me emrin e tyre. Për javë,
                  riemërtoji p.sh. “Java04_Ligjerata.pdf”.
                </p>
              ) : null}
            </div>
          ) : null}

          {error ? <ErrorState message={error} /> : null}

          {notice ? (
            <Alert variant="success">
              <AlertDescription>{notice}</AlertDescription>
            </Alert>
          ) : null}

          <Button type="submit" disabled={uploading || !courseId || !files.length}>
            {uploading ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Upload className="size-4" />
            )}
            Ngarko {files.length ? `${files.length} materiale` : "materialet"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
