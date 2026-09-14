"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
} from "react";
import { Loader2, RefreshCw, Trash2, Upload } from "lucide-react";

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
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { UniDocument } from "@/lib/types";
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

export default function DocumentsPage() {
  const { user } = useAuth();

  // Stafi akademik ngarkon dokumente; profesori menaxhon vetëm ato
  // që ka ngarkuar vetë, dhe backend-i e zbaton këtë pavarësisht UI-t.
  const isAdmin = user?.role === "ADMIN";
  const isStaff = isAdmin || user?.role === "PROFESSOR";

  const [documents, setDocuments] = useState<UniDocument[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const [title, setTitle] = useState("");
  const [documentType, setDocumentType] = useState("REGULATION");
  const [description, setDescription] = useState("");
  const [academicYear, setAcademicYear] = useState("");
  const [uploading, setUploading] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);

  const fileRef = useRef<HTMLInputElement>(null);

  const refresh = useCallback(async () => {
    try {
      setDocuments(await api.documents());
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Dokumentet nuk u ngarkuan.",
      );
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  // Ingestimi ndodh në sfond, prandaj lista rifreskohet vetë derisa
  // çdo dokument të mbërrijë në një status përfundimtar.
  useEffect(() => {
    if (!documents?.some((document) => isInFlight(document.status))) {
      return;
    }

    const timer = setInterval(() => void refresh(), POLL_INTERVAL_MS);

    return () => clearInterval(timer);
  }, [documents, refresh]);

  async function handleUpload(event: FormEvent) {
    event.preventDefault();

    const file = fileRef.current?.files?.[0];

    if (!file) {
      setError("Zgjidh një skedar PDF, DOCX ose TXT.");

      return;
    }

    const form = new FormData();

    form.append("title", title);
    form.append("document_type", documentType);
    form.append("file", file);

    if (description) {
      form.append("description", description);
    }

    if (academicYear) {
      form.append("academic_year", academicYear);
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

      if (fileRef.current) {
        fileRef.current.value = "";
      }

      await refresh();
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Ngarkimi dështoi.",
      );
    } finally {
      setUploading(false);
    }
  }

  async function reindex(id: number) {
    setBusyId(id);
    setError(null);

    try {
      await api.reindexDocument(id);
      await refresh();
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Ri-indeksimi dështoi.",
      );
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
      setError(
        caught instanceof Error ? caught.message : "Fshirja dështoi.",
      );
    } finally {
      setBusyId(null);
    }
  }

  if (!documents) {
    return error ? <ErrorState message={error} /> : <LoadingState />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dokumentet e universitetit"
        description="Rregulloret, syllabuset dhe udhëzuesit që ushqejnë përgjigjet e asistentit."
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
                  <Select
                    value={documentType}
                    onValueChange={setDocumentType}
                  >
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
                  <Label htmlFor="year">Viti akademik</Label>
                  <Input
                    id="year"
                    value={academicYear}
                    onChange={(event) =>
                      setAcademicYear(event.target.value)
                    }
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
                  onChange={(event) =>
                    setDescription(event.target.value)
                  }
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

      {documents.length === 0 ? (
        <EmptyState
          title="Nuk ka dokumente"
          description="Administratori i ngarkon nga kjo faqe."
        />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>
              {documents.length} dokumente ·{" "}
              {
                documents.filter((item) => item.status === "INDEXED")
                  .length
              }{" "}
              të indeksuara
            </CardTitle>
          </CardHeader>

          <CardContent className="px-0">
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
                {documents.map((document) => (
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
      )}
    </div>
  );
}
