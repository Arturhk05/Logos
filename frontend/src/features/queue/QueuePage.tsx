import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router";

import { useNow } from "../../shared/useNow";
import { queueQueryOptions } from "./api";
import { parseQueueFilters, queueSearchParams } from "./filters";
import { QueueView } from "./QueueView";

export function QueuePage() {
  const [params, setParams] = useSearchParams();
  const filters = parseQueueFilters(params);
  const query = useQuery(queueQueryOptions(filters));
  const now = useNow(30_000);
  const search = params.toString();

  return (
    <QueueView
      state={query.isPending ? "loading" : query.data === undefined ? "error" : "ready"}
      errorMessage={query.error?.message}
      onRetry={() => {
        void query.refetch();
      }}
      items={query.data?.items ?? []}
      counts={query.data?.counts ?? {}}
      filters={filters}
      onFiltersChange={(next) => {
        // Replaced, not pushed: going back leaves the queue instead of undoing one click at a time.
        setParams(queueSearchParams(next), { replace: true });
      }}
      hrefFor={(id) => `/fila/${String(id)}${search === "" ? "" : `?${search}`}`}
      now={now}
      updatedAt={query.dataUpdatedAt > 0 ? new Date(query.dataUpdatedAt) : undefined}
      refreshFailed={query.isRefetchError}
      refreshing={query.isFetching}
      onRefresh={() => {
        void query.refetch();
      }}
    />
  );
}
