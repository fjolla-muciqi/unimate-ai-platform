"use client";

import { useEffect, useState } from "react";

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
import { Progress } from "@/components/ui/progress";
import { api } from "@/lib/api";
import type { AnalyticsOverview } from "@/lib/types";
import { formatDateTime, percent } from "@/lib/utils";

function Metric({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <Card>
      <CardContent className="space-y-1 p-5">
        <p className="text-sm text-muted-foreground">{label}</p>
        <p className="text-3xl font-semibold tabular-nums">{value}</p>

        {hint ? (
          <p className="text-xs text-muted-foreground">{hint}</p>
        ) : null}
      </CardContent>
    </Card>
  );
}

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsOverview | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .analytics()
      .then(setData)
      .catch((caught: unknown) =>
        setError(
          caught instanceof Error
            ? caught.message
            : "Analitika nuk u ngarkua.",
        ),
      );
  }, []);

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!data) {
    return <LoadingState />;
  }

  const maxAgentCount = Math.max(
    1,
    ...data.agent_usage.map((usage) => usage.count),
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Analitika e asistentit"
        description="Matjet që dëshmojnë sjelljen e arkitekturës multi-agent."
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Metric
          label="Pyetje gjithsej"
          value={String(data.total_questions)}
          hint={`${data.total_conversations} biseda`}
        />
        <Metric
          label="Përgjigje me citim"
          value={percent(data.citation_rate)}
          hint={`${data.answers_with_sources} nga ${data.total_answers}`}
        />
        <Metric
          label="Pyetje pa përgjigje"
          value={percent(data.unanswered_rate)}
          hint={`${data.unanswered_count} raste`}
        />
        <Metric
          label="Koha mesatare"
          value={
            data.average_latency_ms
              ? `${(data.average_latency_ms / 1000).toFixed(1)}s`
              : "—"
          }
          hint={
            data.median_latency_ms
              ? `Mediana ${(data.median_latency_ms / 1000).toFixed(1)}s`
              : undefined
          }
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Përdorimi i agjentëve</CardTitle>
            <CardDescription>
              Sa herë u aktivizua secili agjent, sipas tools të
              thirrura.
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            {data.agent_usage.map((usage) => (
              <div key={usage.agent} className="space-y-1.5">
                <div className="flex items-baseline justify-between gap-2">
                  <span className="text-sm font-medium">
                    {usage.label}
                  </span>
                  <span className="text-sm tabular-nums text-muted-foreground">
                    {usage.count}
                  </span>
                </div>

                <Progress
                  value={(usage.count / maxAgentCount) * 100}
                />
              </div>
            ))}

            <div className="rounded-lg bg-muted/50 p-3">
              <p className="text-sm font-medium">
                Multi-Agent Collaboration
              </p>
              <p className="mt-1 text-sm text-muted-foreground">
                {data.multi_agent_answers} përgjigje (
                {percent(data.multi_agent_rate)}) aktivizuan më shumë
                se një agjent.
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Vlerësimet e studentëve</CardTitle>
            <CardDescription>
              Reagimi i drejtpërdrejtë mbi dobishmërinë e përgjigjeve.
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            <div className="grid grid-cols-3 gap-3 text-center">
              <div className="rounded-lg border p-3">
                <p className="text-2xl font-semibold tabular-nums text-success">
                  {data.ratings.positive}
                </p>
                <p className="text-xs text-muted-foreground">
                  Pozitive
                </p>
              </div>

              <div className="rounded-lg border p-3">
                <p className="text-2xl font-semibold tabular-nums text-destructive">
                  {data.ratings.negative}
                </p>
                <p className="text-xs text-muted-foreground">
                  Negative
                </p>
              </div>

              <div className="rounded-lg border p-3">
                <p className="text-2xl font-semibold tabular-nums text-muted-foreground">
                  {data.ratings.unrated}
                </p>
                <p className="text-xs text-muted-foreground">
                  Pa vlerësim
                </p>
              </div>
            </div>

            {data.ratings.satisfaction !== null ? (
              <div>
                <div className="mb-2 flex items-baseline justify-between">
                  <span className="text-sm">Kënaqësia</span>
                  <span className="text-sm font-medium tabular-nums">
                    {percent(data.ratings.satisfaction)}
                  </span>
                </div>

                <Progress value={data.ratings.satisfaction * 100} />
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                Ende pa vlerësime.
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Pyetjet më të shpeshta</CardTitle>
          </CardHeader>

          <CardContent>
            {data.frequent_questions.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                Ende pa të dhëna.
              </p>
            ) : (
              <ul className="space-y-2">
                {data.frequent_questions.map((item) => (
                  <li
                    key={item.question}
                    className="flex items-start justify-between gap-3 text-sm"
                  >
                    <span className="min-w-0 flex-1">
                      {item.question}
                    </span>
                    <Badge variant="secondary">{item.count}</Badge>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Pyetjet pa përgjigje</CardTitle>
            <CardDescription>
              Boshllëqe në dokumentacion që administrata duhet t&apos;i
              mbulojë.
            </CardDescription>
          </CardHeader>

          <CardContent>
            {data.recent_unanswered.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                Asnjë pyetje pa përgjigje.
              </p>
            ) : (
              <ul className="space-y-3">
                {data.recent_unanswered.map((item) => (
                  <li key={item.message_id} className="text-sm">
                    <p>{item.question}</p>
                    <p className="text-xs tabular-nums text-muted-foreground">
                      {formatDateTime(item.created_at)}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
