import { CircleCheck, CircleHelp, type LucideIcon } from "lucide-react";
import { Link } from "react-router";

import { formatDateTime } from "../../shared/format";
import { CATEGORY_LABELS, STATUS_LABELS } from "../../shared/labels";
import { Button } from "../../shared/ui/Button";
import { CategoryIcon } from "../../shared/ui/CategoryIcon";
import { CriticalityBadge } from "../../shared/ui/CriticalityBadge";
import { TableSkeleton } from "../../shared/ui/Skeleton";
import { EmptyState, ErrorState } from "../../shared/ui/StateMessage";
import { StatusLabel } from "../../shared/ui/StatusLabel";
import { ToggleButton } from "../../shared/ui/ToggleButton";
import { CategoryFilter } from "../queue/CategoryFilter";
import { CriticalityCounters } from "../queue/CriticalityCounters";
import { hasIncidentFilters, toggle } from "../queue/filters";
import { HISTORY_PAGE_SIZE, type HistoryItem } from "./api";
import { CLOSED_STATUSES, pageCount, type ClosedStatus, type HistoryFilters } from "./filters";
import { Pagination } from "./Pagination";

export interface HistoryViewProps {
  state: "loading" | "error" | "ready";
  errorMessage?: string;
  onRetry: () => void;
  items: HistoryItem[];
  total: number;
  filters: HistoryFilters;
  onFiltersChange: (filters: HistoryFilters) => void;
  hrefFor: (id: number) => string;
  now: Date;
}

const STATUS_ICONS: Record<ClosedStatus, LucideIcon> = {
  CLOSED: CircleCheck,
  INCONCLUSIVE: CircleHelp,
};

const NO_FILTERS: HistoryFilters = { status: [], criticality: [], category: [], page: 1 };

export function HistoryView(props: HistoryViewProps) {
  const { filters } = props;
  const filtered = filters.status.length > 0 || hasIncidentFilters(filters);
  // Any filter change goes back to the first page, which always exists.
  const change = (next: Partial<HistoryFilters>) => {
    props.onFiltersChange({ ...filters, ...next, page: 1 });
  };
  const clearFilters = () => {
    props.onFiltersChange(NO_FILTERS);
  };

  return (
    <section className="flex flex-col gap-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h1 className="text-2xl font-bold tracking-tight">Histórico</h1>
        {props.state === "ready" && props.total > 0 && (
          <p className="text-sm text-muted">
            {props.total} {props.total === 1 ? "incidente encerrado" : "incidentes encerrados"}
          </p>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <div role="group" aria-label="Filtrar por status" className="flex flex-wrap gap-2">
          {CLOSED_STATUSES.map((status) => {
            const Icon = STATUS_ICONS[status];
            return (
              <ToggleButton
                key={status}
                pressed={filters.status.includes(status)}
                onToggle={() => {
                  change({ status: toggle(filters.status, status) });
                }}
              >
                <Icon aria-hidden className="size-4" />
                {STATUS_LABELS[status]}
              </ToggleButton>
            );
          })}
        </div>
        <CriticalityCounters
          selected={filters.criticality}
          onToggle={(criticality) => {
            change({ criticality: toggle(filters.criticality, criticality) });
          }}
        />
        <CategoryFilter
          selected={filters.category}
          onChange={(category) => {
            change({ category });
          }}
        />
        {filtered && (
          <Button variant="ghost" onClick={clearFilters}>
            Limpar filtros
          </Button>
        )}
      </div>

      <HistoryContent {...props} filtered={filtered} onClearFilters={clearFilters} />
    </section>
  );
}

function HistoryContent({
  state,
  errorMessage,
  onRetry,
  items,
  total,
  filters,
  onFiltersChange,
  hrefFor,
  now,
  filtered,
  onClearFilters,
}: HistoryViewProps & { filtered: boolean; onClearFilters: () => void }) {
  if (state === "loading") return <TableSkeleton />;
  if (state === "error") return <ErrorState message={errorMessage ?? ""} onRetry={onRetry} />;
  if (items.length === 0) {
    return filtered ? (
      <EmptyState
        message="Nenhum incidente encerrado com esses filtros."
        action={
          <Button variant="secondary" onClick={onClearFilters}>
            Limpar filtros
          </Button>
        }
      />
    ) : (
      <EmptyState message="Nenhum incidente encerrado até agora." />
    );
  }

  return (
    <>
      <table className="hidden w-full table-fixed border-separate border-spacing-0 overflow-hidden rounded-xl border border-line bg-surface text-sm md:table">
        <colgroup>
          <col className="w-32" />
          <col className="w-[28%]" />
          <col />
          <col className="w-36" />
          <col className="w-36" />
          <col className="w-36" />
        </colgroup>
        <thead className="text-left text-xs text-muted">
          <tr>
            {["Criticidade", "Categoria", "Local", "Status", "Encerrado por", "Encerrado em"].map(
              (column) => (
                <th
                  key={column}
                  scope="col"
                  className="border-b border-line px-4 py-2.5 font-medium"
                >
                  {column}
                </th>
              ),
            )}
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id} className="relative transition-colors hover:bg-canvas">
              <td className="border-b border-line px-4 py-3">
                <CriticalityBadge criticality={item.criticality} />
              </td>
              <td className="border-b border-line px-4 py-3">
                <Link
                  to={hrefFor(item.id)}
                  className="flex items-center gap-2 font-semibold after:absolute after:inset-0 focus-visible:outline-none focus-visible:after:outline-2 focus-visible:after:-outline-offset-2 focus-visible:after:outline-accent"
                >
                  <CategoryIcon category={item.category} className="size-4 text-muted" />
                  {CATEGORY_LABELS[item.category]}
                </Link>
              </td>
              <td className="border-b border-line px-4 py-3 break-words">{item.location}</td>
              <td className="border-b border-line px-4 py-3">
                <StatusLabel status={item.status} />
              </td>
              <td className="border-b border-line px-4 py-3">{item.closed_by?.username ?? "—"}</td>
              <td className="border-b border-line px-4 py-3 whitespace-nowrap text-muted">
                {item.closed_at === null ? "—" : formatDateTime(item.closed_at, now)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <ul className="flex flex-col gap-2 md:hidden">
        {items.map((item) => (
          <li key={item.id} className="rounded-xl border border-line bg-surface">
            <Link to={hrefFor(item.id)} className="flex flex-col gap-2 p-3">
              <div className="flex items-start justify-between gap-2">
                <span className="flex items-center gap-2 font-semibold">
                  <CategoryIcon category={item.category} className="size-4 text-muted" />
                  {CATEGORY_LABELS[item.category]}
                </span>
                <CriticalityBadge criticality={item.criticality} />
              </div>
              <span className="text-sm">{item.location}</span>
              <div className="flex items-center justify-between gap-2 text-sm text-muted">
                <StatusLabel status={item.status} />
                <span>
                  {item.closed_by?.username ?? "—"}
                  {item.closed_at !== null && ` · ${formatDateTime(item.closed_at, now)}`}
                </span>
              </div>
            </Link>
          </li>
        ))}
      </ul>

      <Pagination
        page={filters.page}
        pageCount={pageCount(total, HISTORY_PAGE_SIZE)}
        onPage={(page) => {
          onFiltersChange({ ...filters, page });
        }}
      />
    </>
  );
}
