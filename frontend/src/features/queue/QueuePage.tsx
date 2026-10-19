import { useQuery } from "@tanstack/react-query";
import { Navigate, useNavigate, useParams, useSearchParams } from "react-router";

import { IncidentDrawer } from "../incidents/IncidentDrawer";
import { parseIncidentId } from "../incidents/incidentId";
import { useNow } from "../../shared/useNow";
import { queueQueryOptions } from "./api";
import { parseQueueFilters, queueSearchParams } from "./filters";
import { QueueView } from "./QueueView";

export function QueuePage() {
  const [params, setParams] = useSearchParams();
  const filters = parseQueueFilters(params);
  const query = useQuery(queueQueryOptions(filters));
  const now = useNow(30_000);
  const navigate = useNavigate();
  const { incidentId } = useParams();
  const openId = parseIncidentId(incidentId);
  const search = params.toString();
  const queuePath = `/fila${search === "" ? "" : `?${search}`}`;

  if (incidentId !== undefined && openId === null) return <Navigate to={queuePath} replace />;

  return (
    <>
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
      {openId !== null && (
        <IncidentDrawer
          // A new incident starts with a clean drawer: no reason, conflict or error from the previous one.
          key={openId}
          incidentId={openId}
          onClose={() => {
            void navigate(queuePath);
          }}
        />
      )}
    </>
  );
}
