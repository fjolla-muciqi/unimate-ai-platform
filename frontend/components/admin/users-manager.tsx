"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Loader2, Search } from "lucide-react";

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
import { useAuth } from "@/lib/auth-context";
import type { AdminUser, UserRole } from "@/lib/types";
import { formatDate } from "@/lib/utils";

const ALL = "ALL";

const ROLE_LABELS: Record<UserRole, string> = {
  STUDENT: "Student",
  PROFESSOR: "Profesor",
  ADMIN: "Administrator",
};

export function UsersManager() {
  const { user: me } = useAuth();

  const [users, setUsers] = useState<AdminUser[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [role, setRole] = useState<string>(ALL);
  const [search, setSearch] = useState("");
  const [busyId, setBusyId] = useState<number | null>(null);

  const load = useCallback(async (roleFilter: string, text: string) => {
    setError(null);

    try {
      setUsers(
        await admin.users({
          role: roleFilter === ALL ? undefined : roleFilter,
          search: text.trim() || undefined,
        }),
      );
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Përdoruesit nuk u ngarkuan.",
      );
    }
  }, []);

  // Filtri i rolit zbatohet menjëherë; kërkimi me "Kërko", që të mos
  // dërgohet një kërkesë për çdo shkronjë.
  useEffect(() => {
    void load(role, search);
  }, [role, load]);

  function handleSearch(event: FormEvent) {
    event.preventDefault();
    void load(role, search);
  }

  async function toggle(target: AdminUser) {
    setBusyId(target.id);
    setError(null);

    try {
      const updated = await admin.setUserActive(
        target.id,
        !target.is_active,
      );

      setUsers(
        (current) =>
          current?.map((item) =>
            item.id === updated.id ? updated : item,
          ) ?? null,
      );
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Ndryshimi dështoi.",
      );
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="space-y-4">
      <div className="space-y-1">
        <h2 className="text-lg font-semibold">Përdoruesit</h2>
        <p className="text-sm text-muted-foreground">
          Një llogari e çaktivizuar nuk mund të kyçet. Roli nuk ndryshohet
          këtu, sepse lidhet me profilin akademik të studentit ose të
          profesorit.
        </p>
      </div>

      <form
        onSubmit={handleSearch}
        className="flex flex-wrap items-center gap-2"
      >
        <Input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Emri ose email-i"
          className="w-full sm:w-64"
          aria-label="Kërko përdorues"
        />

        <Button type="submit" variant="outline">
          <Search className="size-4" />
          Kërko
        </Button>

        <Select value={role} onValueChange={setRole}>
          <SelectTrigger className="w-full sm:w-44" aria-label="Roli">
            <SelectValue />
          </SelectTrigger>

          <SelectContent>
            <SelectItem value={ALL}>Të gjitha rolet</SelectItem>
            {Object.entries(ROLE_LABELS).map(([value, label]) => (
              <SelectItem key={value} value={value}>
                {label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </form>

      {error ? <ErrorState message={error} /> : null}

      {users === null ? (
        error ? null : <LoadingState />
      ) : users.length === 0 ? (
        <EmptyState title="Asnjë përdorues nuk përputhet me filtrin" />
      ) : (
        <Card>
          <CardContent className="overflow-x-auto px-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Emri</TableHead>
                  <TableHead>Roli</TableHead>
                  <TableHead>Krijuar</TableHead>
                  <TableHead>Statusi</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>

              <TableBody>
                {users.map((item) => {
                  const isMe = item.id === me?.id;

                  return (
                    <TableRow key={item.id}>
                      <TableCell>
                        <p className="font-medium">
                          {item.first_name} {item.last_name}
                          {isMe ? (
                            <span className="text-muted-foreground">
                              {" "}
                              (ti)
                            </span>
                          ) : null}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {item.email}
                        </p>
                      </TableCell>

                      <TableCell>{ROLE_LABELS[item.role]}</TableCell>

                      <TableCell className="tabular-nums text-muted-foreground">
                        {formatDate(item.created_at)}
                      </TableCell>

                      <TableCell>
                        {item.is_active ? (
                          <Badge variant="success">Aktiv</Badge>
                        ) : (
                          <Badge variant="outline">Joaktiv</Badge>
                        )}
                      </TableCell>

                      <TableCell className="text-right">
                        {/* Admini nuk e çaktivizon veten: backend-i e
                            refuzon, dhe butoni nuk ofrohet fare. */}
                        {isMe ? null : (
                          <Button
                            variant={item.is_active ? "outline" : "default"}
                            size="sm"
                            disabled={busyId === item.id}
                            onClick={() => void toggle(item)}
                          >
                            {busyId === item.id ? (
                              <Loader2 className="size-3.5 animate-spin" />
                            ) : null}
                            {item.is_active ? "Çaktivizo" : "Aktivizo"}
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
