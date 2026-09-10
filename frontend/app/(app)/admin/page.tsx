"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  BookOpen,
  FileText,
  MessageSquare,
  ShieldAlert,
  Users,
} from "lucide-react";

import { PageHeader } from "@/components/layout/page-header";
import { ErrorState, LoadingState } from "@/components/layout/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { api } from "@/lib/api";
import type { AdminOverview, AuditLog } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

/** Ngjarjet e sigurisë, siç i emërton `AuditEvent` në backend. */
const EVENT_LABELS: Record<string, string> = {
  guardrail_block: "Bllokim guardrail",
  prompt_injection_detected: "Prompt injection",
  unauthorized_access_attempt: "Akses i paautorizuar",
  output_blocked: "Përgjigje e bllokuar",
};

function StatCard({
  label,
  value,
  hint,
  icon: Icon,
}: {
  label: string;
  value: number;
  hint?: string;
  icon: typeof Users;
}) {
  return (
    <Card>
      <CardContent className="flex items-start justify-between gap-4 p-5">
        <div className="space-y-1">
          <p className="text-sm text-muted-foreground">{label}</p>
          <p className="text-3xl font-semibold tabular-nums">{value}</p>

          {hint ? (
            <p className="text-xs text-muted-foreground">{hint}</p>
          ) : null}
        </div>

        <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
          <Icon className="size-5" />
        </div>
      </CardContent>
    </Card>
  );
}

export default function AdminPage() {
  const [overview, setOverview] = useState<AdminOverview | null>(null);
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.adminOverview(), api.auditLogs(25)])
      .then(([adminOverview, auditLogs]) => {
        setOverview(adminOverview);
        setLogs(auditLogs);
      })
      .catch((caught: unknown) =>
        setError(
          caught instanceof Error
            ? caught.message
            : "Paneli nuk u ngarkua.",
        ),
      );
  }, []);

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!overview) {
    return <LoadingState />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Paneli i administratorit"
        description="Gjendja e platformës dhe regjistri i ngjarjeve të sigurisë."
      >
        <div className="flex gap-2">
          <Button asChild variant="outline">
            <Link href="/documents">Menaxho dokumentet</Link>
          </Button>

          <Button asChild>
            <Link href="/analytics">Analitika e asistentit</Link>
          </Button>
        </div>
      </PageHeader>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Studentë"
          value={overview.total_students}
          hint={`${overview.total_professors} profesorë, ${overview.total_admins} admin`}
          icon={Users}
        />
        <StatCard
          label="Lëndë"
          value={overview.total_courses}
          hint={`${overview.total_programs} programe studimi`}
          icon={BookOpen}
        />
        <StatCard
          label="Dokumente"
          value={overview.total_documents}
          hint={`${overview.indexed_documents} të indeksuara, ${overview.total_chunks} fragmente`}
          icon={FileText}
        />
        <StatCard
          label="Pyetje (30 ditë)"
          value={overview.questions_last_30_days}
          hint={`${overview.blocked_last_30_days} të bllokuara nga guardrail-i`}
          icon={MessageSquare}
        />
      </div>

      {overview.failed_documents > 0 || overview.pending_documents > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Gjendja e indeksimit</CardTitle>
            <CardDescription>
              Dokumentet e padisponueshme për asistentin.
            </CardDescription>
          </CardHeader>

          <CardContent className="flex flex-wrap items-center gap-3">
            {overview.pending_documents > 0 ? (
              <Badge variant="warning">
                {overview.pending_documents} në përpunim
              </Badge>
            ) : null}

            {overview.failed_documents > 0 ? (
              <Badge variant="destructive">
                {overview.failed_documents} të dështuara
              </Badge>
            ) : null}

            <Button asChild variant="outline" size="sm">
              <Link href="/documents">Shko te dokumentet</Link>
            </Button>
          </CardContent>
        </Card>
      ) : null}

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <ShieldAlert className="size-4 text-muted-foreground" />
            <CardTitle>Regjistri i sigurisë</CardTitle>
          </div>

          <CardDescription>
            Çdo bllokim nga Guardrail Agent-i dhe çdo tentativë aksesi
            te të dhënat e një studenti tjetër.
          </CardDescription>
        </CardHeader>

        <CardContent className="px-0">
          {logs.length === 0 ? (
            <p className="px-6 py-6 text-center text-sm text-muted-foreground">
              Asnjë ngjarje sigurie e regjistruar.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Koha</TableHead>
                  <TableHead>Përdoruesi</TableHead>
                  <TableHead>Ngjarja</TableHead>
                  <TableHead>Rregulla</TableHead>
                  <TableHead>Detaji</TableHead>
                </TableRow>
              </TableHeader>

              <TableBody>
                {logs.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell className="whitespace-nowrap tabular-nums text-muted-foreground">
                      {formatDateTime(log.created_at)}
                    </TableCell>

                    <TableCell>{log.user_email ?? "—"}</TableCell>

                    <TableCell>
                      <Badge variant="destructive">
                        {EVENT_LABELS[log.event_type] ??
                          log.event_type}
                      </Badge>
                    </TableCell>

                    <TableCell className="text-xs text-muted-foreground">
                      {log.rule ?? "—"}
                    </TableCell>

                    <TableCell className="max-w-md text-xs text-muted-foreground">
                      {log.detail}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
