import { FileText } from "lucide-react";

import type { Source } from "@/lib/types";

/**
 * Burimet e një përgjigjeje RAG.
 *
 * Numri i çdo burimi përputhet me citimin [1], [2] brenda tekstit,
 * kështu që studenti mund ta ndjekë pretendimin deri te faqja e
 * dokumentit. Pa këtë, "e ka thënë AI-ja" mbetet e paverifikueshme.
 */
export function Sources({ sources }: { sources: Source[] }) {
  if (sources.length === 0) {
    return null;
  }

  return (
    <div className="mt-3 border-t pt-3">
      <p className="mb-2 text-xs font-medium text-muted-foreground">
        Burimet
      </p>

      <ul className="space-y-1.5">
        {sources.map((source) => (
          <li
            key={`${source.number}-${source.document_id}`}
            className="flex items-start gap-2 text-xs"
          >
            <span className="mt-0.5 flex size-4 shrink-0 items-center justify-center rounded bg-primary/10 text-[10px] font-semibold text-primary">
              {source.number}
            </span>

            <FileText className="mt-0.5 size-3.5 shrink-0 text-muted-foreground" />

            <span className="text-muted-foreground">
              <span className="font-medium text-foreground">
                {source.title ?? source.file_name ?? "Dokument"}
              </span>
              {source.page_number !== null
                ? `, f. ${source.page_number}`
                : ""}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
