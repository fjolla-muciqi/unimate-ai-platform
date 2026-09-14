import { Badge } from "@/components/ui/badge";
import type { DocumentStatus } from "@/lib/types";

const STATUS_LABELS: Record<
  DocumentStatus,
  { label: string; variant: "secondary" | "warning" | "success" | "destructive" }
> = {
  PENDING: { label: "Në pritje", variant: "secondary" },
  PROCESSING: { label: "Duke u indeksuar", variant: "warning" },
  INDEXED: { label: "I indeksuar", variant: "success" },
  FAILED: { label: "Dështoi", variant: "destructive" },
};

export function DocumentStatusBadge({
  status,
}: {
  status: DocumentStatus;
}) {
  const entry = STATUS_LABELS[status] ?? {
    label: status,
    variant: "secondary" as const,
  };

  return <Badge variant={entry.variant}>{entry.label}</Badge>;
}

/** True kur statusi ende mund të ndryshojë vetë. */
export function isInFlight(status: DocumentStatus): boolean {
  return status === "PENDING" || status === "PROCESSING";
}
