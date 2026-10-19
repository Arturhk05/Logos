import { Link } from "react-router";

import { formatElapsed } from "../../shared/format";
import { CATEGORY_LABELS, type Criticality } from "../../shared/labels";
import { Button } from "../../shared/ui/Button";
import { CategoryIcon } from "../../shared/ui/CategoryIcon";
import { CriticalityBadge } from "../../shared/ui/CriticalityBadge";
import { TableSkeleton } from "../../shared/ui/Skeleton";
import { EmptyState, ErrorState } from "../../shared/ui/StateMessage";
import { StatusLabel } from "../../shared/ui/StatusLabel";
import type { QueueItem } from "./api";
import { CategoryFilter } from "./CategoryFilter";
import { CriticalityCounters } from "./CriticalityCounters";
import { hasFilters, toggle, type QueueFilters } from "./filters";
import { UpdatedAgo } from "./UpdatedAgo";

export interface QueueViewProps {
  state: "loading" | "error" | "ready";
  errorMessage?: string;
  onRetry: () => void;
  items: QueueItem[];
  counts: Partial<Record<Criticality, number>>;
  filters: QueueFilters;
  onFiltersChange: (filters: QueueFilters) => void;
  hrefFor: (id: number) => string;
  now: Date;
  updatedAt?: Date;
  refreshFailed: boolean;
  refreshing: boolean;
  onRefresh: () => void;
}

const NO_FILTERS: QueueFilters = { criticality: [], category: [] };

export function QueueView(props: QueueViewProps) {
  const { filters, onFiltersChange } = props;
  const filtered = hasFilters(filters);
  const clearFilters = () => {
    onFiltersChange(NO_FILTERS);
  };

  return (
    <section className="flex flex-col gap-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h1 className="text-2xl font-bold tracking-tight">Fila de incidentes</h1>
        <UpdatedAgo
          updatedAt={props.updatedAt}
          failed={props.refreshFailed}
          refreshing={props.refreshing}
          onRefresh={props.onRefresh}
        />
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <CriticalityCounters
          counts={props.counts}
          selected={filters.criticality}
          onToggle={(criticality) => {
            onFiltersChange({ ...filters, criticality: toggle(filters.criticality, criticality) });
          }}
        />
        <CategoryFilter
          selected={filters.category}
          onChange={(category) => {
            onFiltersChange({ ...filters, category });
          }}
        />
        {filtered && (
          <Button variant="ghost" onClick={clearFilters}>
            Limpar filtros
          </Button>
        )}
      </div>

      <QueueContent {...props} filtered={filtered} onClearFilters={clearFilters} />
    </section>
  );
}

function QueueContent({
  state,
  errorMessage,
  onRetry,
  items,
  hrefFor,
  now,
  filtered,
  onClearFilters,
}: QueueViewProps & { filtered: boolean; onClearFilters: () => void }) {
  if (state === "loading") return <TableSkeleton />;
  if (state === "error") return <ErrorState message={errorMessage ?? ""} onRetry={onRetry} />;
  if (items.length === 0) {
    return filtered ? (
      <EmptyState
        message="Nenhum incidente com esses filtros."
        action={
          <Button variant="secondary" onClick={onClearFilters}>
            Limpar filtros
          </Button>
        }
      />
    ) : (
      <EmptyState message="Nenhum incidente ativo no momento." />
    );
  }

  return (
    <>
      <table className="hidden w-full table-fixed border-separate border-spacing-0 overflow-hidden rounded-xl border border-line bg-surface text-sm md:table">
        {/* Fixed widths: filtering never makes the columns jump to fit the remaining rows. */}
        <colgroup>
          <col className="w-32" />
          <col className="w-[28%]" />
          <col />
          <col className="w-44" />
          <col className="w-36" />
          <col className="w-28" />
        </colgroup>
        <thead className="text-left text-xs text-muted">
          <tr>
            {["Criticidade", "Categoria", "Local", "Status", "Responsável", "Aberto há"].map(
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
          {items.map((item) => {
            const high = item.criticality === "HIGH";
            return (
              <tr
                key={item.id}
                className={`relative transition-colors ${high ? "bg-critical-soft hover:bg-critical-hover" : "hover:bg-canvas"}`}
                data-criticality={item.criticality}
              >
                <td
                  className={`border-b border-line px-4 py-3 ${high ? "shadow-[inset_3px_0_0_var(--color-critical)]" : ""}`}
                >
                  <CriticalityBadge criticality={item.criticality} />
                </td>
                <td className="border-b border-line px-4 py-3">
                  {/* The link covers the whole row, so a click anywhere opens the incident. */}
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
                <td className="border-b border-line px-4 py-3">
                  {item.assignee?.username ?? <span className="text-muted">—</span>}
                </td>
                <td className="border-b border-line px-4 py-3 whitespace-nowrap text-muted">
                  {formatElapsed(item.created_at, now)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      <ul className="flex flex-col gap-2 md:hidden">
        {items.map((item) => {
          const high = item.criticality === "HIGH";
          return (
            <li
              key={item.id}
              className={`rounded-xl border ${high ? "border-critical-line bg-critical-soft shadow-[inset_3px_0_0_var(--color-critical)]" : "border-line bg-surface"}`}
              data-criticality={item.criticality}
            >
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
                    {item.assignee?.username ?? "Sem responsável"} ·{" "}
                    {formatElapsed(item.created_at, now)}
                  </span>
                </div>
              </Link>
            </li>
          );
        })}
      </ul>
    </>
  );
}
