"use client";

import {
  useCallback,
  useEffect,
  useState,
  type FormEvent,
  type ReactNode,
} from "react";
import { Loader2, Pencil, Plus, Trash2, X } from "lucide-react";

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
import { Textarea } from "@/components/ui/textarea";
import type { Resource } from "@/lib/api";
import { cn } from "@/lib/utils";

/** Vlerat e formës mbahen si tekst, siç i jep një `<input>`. */
export type FormValues = Record<string, string>;

/**
 * Radix Select nuk pranon `""` si vlerë opsioni, prandaj "asnjë"
 * shënohet me këtë vlerë dhe përkthehet në `null` te `toPayload`.
 */
export const NONE = "__none";

export interface FieldOption {
  value: string;
  label: string;
}

export interface FieldDef {
  name: string;
  label: string;
  type: "text" | "textarea" | "number" | "select" | "time" | "datetime";
  required?: boolean;
  options?: FieldOption[];
  placeholder?: string;

  /** Fusha shfaqet vetëm gjatë ndryshimit, p.sh. aktiv/joaktiv. */
  editOnly?: boolean;

  /** Zë gjithë gjerësinë e formës. */
  wide?: boolean;
}

export interface Column<T> {
  header: string;
  cell: (row: T) => ReactNode;
  className?: string;
}

interface ResourceManagerProps<T extends { id: number }> {
  title: string;
  description: string;

  /** Emri i një rreshti, për butonat: "Shto lëndë". */
  singular: string;

  resource: Resource<T>;
  fields: FieldDef[];
  columns: Column<T>[];
  emptyForm: FormValues;
  toForm: (row: T) => FormValues;
  toPayload: (values: FormValues) => Record<string, unknown>;
  sort?: (a: T, b: T) => number;

  /** Thirret pas çdo ndryshimi, që faqja të rifreskojë listat e varura. */
  onChange?: () => void;

  /** Shfaqet para konfirmimit kur fshirja prek edhe të dhëna të tjera. */
  deleteWarning?: string;
}

function errorMessage(caught: unknown, fallback: string): string {
  return caught instanceof Error ? caught.message : fallback;
}

export function ResourceManager<T extends { id: number }>({
  title,
  description,
  singular,
  resource,
  fields,
  columns,
  emptyForm,
  toForm,
  toPayload,
  sort,
  onChange,
  deleteWarning,
}: ResourceManagerProps<T>) {
  const [rows, setRows] = useState<T[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  // `null` = forma e mbyllur, 0 = rresht i ri, tjetër = id që ndryshohet.
  const [editingId, setEditingId] = useState<number | null>(null);
  const [values, setValues] = useState<FormValues>(emptyForm);
  const [saving, setSaving] = useState(false);

  // Fshirja kërkon një klikim të dytë te i njëjti rresht.
  const [confirmId, setConfirmId] = useState<number | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  const refresh = useCallback(async () => {
    try {
      const loaded = await resource.list();

      setRows(sort ? [...loaded].sort(sort) : loaded);
    } catch (caught) {
      setError(errorMessage(caught, "Të dhënat nuk u ngarkuan."));
    }
  }, [resource, sort]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  function openCreate() {
    setEditingId(0);
    setValues(emptyForm);
    setNotice(null);
    setError(null);
  }

  function openEdit(row: T) {
    setEditingId(row.id);
    setValues(toForm(row));
    setNotice(null);
    setError(null);
  }

  function closeForm() {
    setEditingId(null);
    setValues(emptyForm);
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();

    setSaving(true);
    setError(null);

    const payload = toPayload(values);
    const isNew = editingId === 0;

    try {
      if (isNew) {
        await resource.create(payload);
      } else if (editingId !== null) {
        await resource.update(editingId, payload);
      }

      setNotice(isNew ? "U shtua me sukses." : "Ndryshimet u ruajtën.");
      closeForm();
      await refresh();
      onChange?.();
    } catch (caught) {
      setError(errorMessage(caught, "Ruajtja dështoi."));
    } finally {
      setSaving(false);
    }
  }

  async function remove(id: number) {
    setBusyId(id);
    setError(null);
    setNotice(null);

    try {
      await resource.remove(id);

      setConfirmId(null);
      setNotice("U fshi.");
      await refresh();
      onChange?.();
    } catch (caught) {
      setError(errorMessage(caught, "Fshirja dështoi."));
    } finally {
      setBusyId(null);
    }
  }

  function setField(name: string, value: string) {
    setValues((current) => ({ ...current, [name]: value }));
  }

  function renderField(field: FieldDef) {
    const id = `field-${field.name}`;
    const value = values[field.name] ?? "";

    if (field.type === "select") {
      return (
        <Select
          value={value}
          onValueChange={(next) => setField(field.name, next)}
          required={field.required}
        >
          <SelectTrigger id={id}>
            <SelectValue placeholder={field.placeholder ?? "Zgjidh…"} />
          </SelectTrigger>

          <SelectContent>
            {field.options?.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      );
    }

    if (field.type === "textarea") {
      return (
        <Textarea
          id={id}
          value={value}
          required={field.required}
          placeholder={field.placeholder}
          rows={3}
          onChange={(event) => setField(field.name, event.target.value)}
        />
      );
    }

    const inputType =
      field.type === "datetime" ? "datetime-local" : field.type;

    return (
      <Input
        id={id}
        type={inputType}
        value={value}
        required={field.required}
        placeholder={field.placeholder}
        onChange={(event) => setField(field.name, event.target.value)}
      />
    );
  }

  const isEditing = editingId !== null && editingId !== 0;

  const visibleFields = fields.filter(
    (field) => !field.editOnly || isEditing,
  );

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="space-y-1">
          <h2 className="text-lg font-semibold">{title}</h2>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>

        {editingId === null ? (
          <Button onClick={openCreate}>
            <Plus className="size-4" />
            Shto {singular}
          </Button>
        ) : null}
      </div>

      {error ? <ErrorState message={error} /> : null}

      {notice ? (
        <Alert variant="success">
          <AlertDescription>{notice}</AlertDescription>
        </Alert>
      ) : null}

      {editingId !== null ? (
        <Card>
          <CardHeader>
            <CardTitle>
              {isEditing ? `Ndrysho ${singular}` : `Shto ${singular}`}
            </CardTitle>
            <CardDescription>
              Fushat me * janë të detyrueshme.
            </CardDescription>
          </CardHeader>

          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                {visibleFields.map((field) => (
                  <div
                    key={field.name}
                    className={cn("space-y-2", field.wide && "md:col-span-2")}
                  >
                    <Label htmlFor={`field-${field.name}`}>
                      {field.label}
                      {field.required ? " *" : ""}
                    </Label>
                    {renderField(field)}
                  </div>
                ))}
              </div>

              <div className="flex gap-2">
                <Button type="submit" disabled={saving}>
                  {saving ? (
                    <Loader2 className="size-4 animate-spin" />
                  ) : null}
                  Ruaj
                </Button>

                <Button
                  type="button"
                  variant="outline"
                  onClick={closeForm}
                  disabled={saving}
                >
                  Anulo
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      ) : null}

      {confirmId !== null && deleteWarning ? (
        <Alert variant="destructive">
          <AlertDescription>{deleteWarning}</AlertDescription>
        </Alert>
      ) : null}

      {rows === null ? (
        error ? null : <LoadingState />
      ) : rows.length === 0 ? (
        <EmptyState
          title="Nuk ka ende të dhëna"
          description={`Shtyp "Shto ${singular}" për të filluar.`}
        />
      ) : (
        <Card>
          <CardContent className="overflow-x-auto px-0">
            <Table>
              <TableHeader>
                <TableRow>
                  {columns.map((column) => (
                    <TableHead key={column.header}>{column.header}</TableHead>
                  ))}
                  <TableHead />
                </TableRow>
              </TableHeader>

              <TableBody>
                {rows.map((row) => (
                  <TableRow key={row.id}>
                    {columns.map((column) => (
                      <TableCell
                        key={column.header}
                        className={column.className}
                      >
                        {column.cell(row)}
                      </TableCell>
                    ))}

                    <TableCell>
                      <div className="flex justify-end gap-1">
                        {confirmId === row.id ? (
                          <>
                            <Button
                              variant="destructive"
                              size="sm"
                              disabled={busyId === row.id}
                              onClick={() => void remove(row.id)}
                            >
                              {busyId === row.id ? (
                                <Loader2 className="size-3.5 animate-spin" />
                              ) : null}
                              Konfirmo fshirjen
                            </Button>

                            <Button
                              variant="ghost"
                              size="icon"
                              className="size-8"
                              onClick={() => setConfirmId(null)}
                              aria-label="Anulo"
                              title="Anulo"
                            >
                              <X className="size-3.5" />
                            </Button>
                          </>
                        ) : (
                          <>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="size-8"
                              onClick={() => openEdit(row)}
                              aria-label="Ndrysho"
                              title="Ndrysho"
                            >
                              <Pencil className="size-3.5" />
                            </Button>

                            <Button
                              variant="ghost"
                              size="icon"
                              className="size-8 text-destructive"
                              onClick={() => setConfirmId(row.id)}
                              aria-label="Fshi"
                              title="Fshi"
                            >
                              <Trash2 className="size-3.5" />
                            </Button>
                          </>
                        )}
                      </div>
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
