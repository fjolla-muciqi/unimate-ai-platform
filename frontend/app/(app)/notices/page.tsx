"use client";

import { useEffect, useState } from "react";
import { BellRing, CalendarClock } from "lucide-react";

import { PageHeader } from "@/components/layout/page-header";
import { ErrorState, LoadingState } from "@/components/layout/states";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { api } from "@/lib/api";
import type { Deadline, Notification } from "@/lib/types";
import { daysUntil, formatDate, formatDateTime } from "@/lib/utils";

const DEADLINE_TYPES: Record<string, string> = {
  REGISTRATION: "Regjistrim",
  PAYMENT: "Pagesë",
  GRADUATION: "Diplomim",
  EVENT: "Event",
  OTHER: "Tjetër",
};

const SEVERITIES: Record<
  string,
  { label: string; variant: "secondary" | "warning" | "destructive" }
> = {
  INFO: { label: "Informacion", variant: "secondary" },
  WARNING: { label: "Paralajmërim", variant: "warning" },
  URGENT: { label: "Urgjent", variant: "destructive" },
};

function daysLeftLabel(days: number): string {
  if (days === 0) return "Sot";
  if (days === 1) return "Nesër";

  return `Pas ${days} ditësh`;
}

export default function NoticesPage() {
  const [deadlines, setDeadlines] = useState<Deadline[] | null>(null);
  const [notifications, setNotifications] = useState<Notification[] | null>(
    null,
  );
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.deadlines(true), api.notifications()])
      .then(([loadedDeadlines, loadedNotifications]) => {
        setDeadlines(
          [...loadedDeadlines].sort((a, b) =>
            a.due_date.localeCompare(b.due_date),
          ),
        );
        setNotifications(
          [...loadedNotifications].sort((a, b) =>
            b.created_at.localeCompare(a.created_at),
          ),
        );
      })
      .catch((caught: unknown) =>
        setError(
          caught instanceof Error
            ? caught.message
            : "Afatet dhe njoftimet nuk u ngarkuan.",
        ),
      );
  }, []);

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!deadlines || !notifications) {
    return <LoadingState />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Afate dhe njoftime"
        description="Afatet e ardhshme të programit tënd dhe njoftimet aktive të administratës."
      />

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CalendarClock className="size-5 text-primary" />
              Afatet ({deadlines.length})
            </CardTitle>
            <CardDescription>
              Regjistrime, pagesa, diplomim dhe evente, sipas datës.
            </CardDescription>
          </CardHeader>

          <CardContent>
            {deadlines.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">
                Nuk ka afate të ardhshme.
              </p>
            ) : (
              <ul className="divide-y">
                {deadlines.map((deadline) => {
                  const days = daysUntil(deadline.due_date);

                  return (
                    <li key={deadline.id} className="space-y-1 py-3">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="flex-1 text-sm font-medium">
                          {deadline.title}
                        </p>
                        <Badge variant={days <= 7 ? "warning" : "secondary"}>
                          {daysLeftLabel(days)}
                        </Badge>
                      </div>

                      <p className="text-xs text-muted-foreground">
                        {DEADLINE_TYPES[deadline.deadline_type] ??
                          deadline.deadline_type}{" "}
                        · {formatDateTime(deadline.due_date)}
                      </p>

                      {deadline.description ? (
                        <p className="text-sm text-muted-foreground">
                          {deadline.description}
                        </p>
                      ) : null}
                    </li>
                  );
                })}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BellRing className="size-5 text-primary" />
              Njoftimet ({notifications.length})
            </CardTitle>
            <CardDescription>Më të rejat në krye.</CardDescription>
          </CardHeader>

          <CardContent>
            {notifications.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">
                Nuk ka njoftime aktive.
              </p>
            ) : (
              <ul className="divide-y">
                {notifications.map((notification) => {
                  const severity = SEVERITIES[notification.severity] ?? {
                    label: notification.severity,
                    variant: "secondary" as const,
                  };

                  return (
                    <li key={notification.id} className="space-y-1 py-3">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="flex-1 text-sm font-medium">
                          {notification.title}
                        </p>
                        <Badge variant={severity.variant}>
                          {severity.label}
                        </Badge>
                      </div>

                      <p className="text-sm text-muted-foreground">
                        {notification.body}
                      </p>

                      <p className="text-xs text-muted-foreground">
                        {formatDate(notification.created_at)}
                      </p>
                    </li>
                  );
                })}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
