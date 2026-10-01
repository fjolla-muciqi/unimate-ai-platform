"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import Link from "next/link";
import { Search } from "lucide-react";

import { PageHeader } from "@/components/layout/page-header";
import {
  EmptyState,
  ErrorState,
  LoadingState,
} from "@/components/layout/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
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
import { admin } from "@/lib/api";
import type { AdminStudentRow, Program } from "@/lib/types";

const ALL = "__all";

export default function StudentsPage() {
  const [students, setStudents] = useState<AdminStudentRow[] | null>(null);
  const [programs, setPrograms] = useState<Program[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [programId, setProgramId] = useState(ALL);

  const load = useCallback(async (text: string, program: string) => {
    setError(null);

    try {
      setStudents(
        await admin.students({
          search: text.trim() || undefined,
          programId: program === ALL ? undefined : program,
        }),
      );
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Studentët nuk u ngarkuan.",
      );
    }
  }, []);

  useEffect(() => {
    admin.programs
      .list()
      .then(setPrograms)
      .catch(() => setPrograms([]));
  }, []);

  // Programi zbatohet menjëherë; kërkimi me "Kërko", që të mos dërgohet
  // një kërkesë për çdo shkronjë.
  useEffect(() => {
    void load(search, programId);
  }, [programId, load]);

  function handleSearch(event: FormEvent) {
    event.preventDefault();
    void load(search, programId);
  }

  const withoutProfile =
    students?.filter((student) => student.student_profile_id === null)
      .length ?? 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Studentët"
        description="Profili akademik dhe lëndët e çdo studenti. Kliko një student për t'i menaxhuar lëndët dhe grupet."
      />

      <form onSubmit={handleSearch} className="flex flex-wrap items-center gap-2">
        <Input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Emri, email-i ose numri i studentit"
          className="w-full sm:w-80"
          aria-label="Kërko student"
        />

        <Button type="submit" variant="outline">
          <Search className="size-4" />
          Kërko
        </Button>

        <Select value={programId} onValueChange={setProgramId}>
          <SelectTrigger className="w-full sm:w-72" aria-label="Programi">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>Të gjitha programet</SelectItem>
            {programs.map((program) => (
              <SelectItem key={program.id} value={String(program.id)}>
                {program.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </form>

      {error ? <ErrorState message={error} /> : null}

      {students === null ? (
        error ? null : <LoadingState />
      ) : students.length === 0 ? (
        <EmptyState title="Asnjë student nuk përputhet me kërkimin" />
      ) : (
        <Card>
          <CardContent className="overflow-x-auto px-0">
            <p className="px-6 pb-2 pt-4 text-sm text-muted-foreground">
              {students.length} studentë
              {withoutProfile
                ? ` · ${withoutProfile} pa profil akademik të plotësuar`
                : ""}
            </p>

            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Studenti</TableHead>
                  <TableHead>Numri</TableHead>
                  <TableHead>Programi</TableHead>
                  <TableHead>Viti / Sem.</TableHead>
                  <TableHead>Lëndë</TableHead>
                  <TableHead>Statusi</TableHead>
                </TableRow>
              </TableHeader>

              <TableBody>
                {students.map((student) => (
                  <TableRow key={student.user_id}>
                    <TableCell>
                      <Link
                        href={`/admin/students/${student.user_id}`}
                        className="font-medium text-primary hover:underline"
                      >
                        {student.full_name}
                      </Link>
                      <p className="text-xs text-muted-foreground">
                        {student.email}
                      </p>
                    </TableCell>

                    <TableCell className="tabular-nums">
                      {student.student_number ?? "—"}
                    </TableCell>

                    <TableCell>
                      {student.program_name ?? (
                        <Badge variant="warning">Pa profil</Badge>
                      )}
                    </TableCell>

                    <TableCell className="tabular-nums">
                      {student.study_year
                        ? `${student.study_year} / ${student.semester}`
                        : "—"}
                    </TableCell>

                    <TableCell className="tabular-nums">
                      {student.course_count}
                    </TableCell>

                    <TableCell>
                      {student.is_active ? (
                        <Badge variant="success">Aktiv</Badge>
                      ) : (
                        <Badge variant="outline">Joaktiv</Badge>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
