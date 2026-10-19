import { RefreshCw, WifiOff } from "lucide-react";

import { useNow } from "../../shared/useNow";

function since(updatedAt: Date, now: Date): string {
  const seconds = Math.max(0, Math.floor((now.getTime() - updatedAt.getTime()) / 1000));
  if (seconds < 5) return "agora";
  if (seconds < 60) return `há ${String(seconds)} s`;
  return `há ${String(Math.floor(seconds / 60))} min`;
}

interface UpdatedAgoProps {
  updatedAt?: Date;
  failed: boolean;
  refreshing: boolean;
  onRefresh: () => void;
}

/**
 * Tells the analyst the list is live, or that it stopped updating; a click refreshes it right away.
 * Always rendered: while a new filter loads there is no date yet, and hiding it made the header jump.
 */
export function UpdatedAgo({ updatedAt, failed, refreshing, onRefresh }: UpdatedAgoProps) {
  const now = useNow(1000);

  const Icon = failed && !refreshing ? WifiOff : RefreshCw;
  return (
    <button
      type="button"
      onClick={onRefresh}
      disabled={refreshing}
      aria-busy={refreshing || undefined}
      title="Atualizar agora"
      className={`flex min-h-9 items-center gap-1.5 rounded-lg px-2 text-sm transition-colors hover:bg-surface hover:text-ink disabled:cursor-default ${
        failed ? "text-ink" : "text-muted"
      }`}
    >
      <Icon aria-hidden className={`size-3.5 ${refreshing ? "animate-spin" : ""}`} />
      {updatedAt === undefined
        ? "Atualizando…"
        : failed
          ? `Não foi possível atualizar. Última atualização ${since(updatedAt, now)}.`
          : `Atualizado ${since(updatedAt, now)}`}
    </button>
  );
}
