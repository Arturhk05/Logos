import { Link } from "react-router";

import { formatDateTime } from "../../shared/format";
import { CATEGORY_LABELS } from "../../shared/labels";
import { CategoryIcon } from "../../shared/ui/CategoryIcon";
import { CriticalityBadge } from "../../shared/ui/CriticalityBadge";
import { TableSkeleton } from "../../shared/ui/Skeleton";
import { EmptyState, ErrorState } from "../../shared/ui/StateMessage";
import { StatusLabel } from "../../shared/ui/StatusLabel";
import type { QueueItem } from "../queue/api";

export interface MyReportsViewProps {
  state: "loading" | "error" | "ready";
  errorMessage?: string;
  onRetry: () => void;
  items: QueueItem[];
  now: Date;
}

export function MyReportsView({ state, errorMessage, onRetry, items, now }: MyReportsViewProps) {
  return (
    <section className="flex flex-col gap-4">
      <h1 className="text-xl font-bold tracking-tight">Meus reportes</h1>
      {state === "loading" && <TableSkeleton rows={4} />}
      {state === "error" && <ErrorState message={errorMessage ?? ""} onRetry={onRetry} />}
      {state === "ready" && items.length === 0 && (
        <EmptyState
          message="Você ainda não reportou nenhum incidente."
          action={
            <Link
              to="/reportar"
              className="flex min-h-11 items-center rounded-lg bg-accent px-4 font-semibold text-on-accent"
            >
              Reportar incidente
            </Link>
          }
        />
      )}
      {state === "ready" && items.length > 0 && (
        // In the order the API sends: the most recent first (US-09).
        <ul className="flex flex-col gap-2">
          {items.map((item) => (
            <li
              key={item.id}
              className="flex flex-col gap-2 rounded-xl border border-line bg-surface p-3"
            >
              <div className="flex items-start justify-between gap-2">
                <span className="flex items-center gap-2 font-semibold">
                  <CategoryIcon category={item.category} className="size-4 text-muted" />
                  {CATEGORY_LABELS[item.category]}
                </span>
                <span className="text-sm text-muted tabular-nums">#{item.id}</span>
              </div>
              <span className="text-sm">
                {item.location} ·{" "}
                <span className="text-muted">{formatDateTime(item.created_at, now)}</span>
              </span>
              <div className="flex items-center justify-between gap-2 text-sm">
                <StatusLabel status={item.status} />
                <CriticalityBadge criticality={item.criticality} />
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
