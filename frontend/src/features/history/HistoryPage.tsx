import { useQuery } from "@tanstack/react-query";
import { Navigate, useNavigate, useParams, useSearchParams } from "react-router";

import { useNow } from "../../shared/useNow";
import { IncidentDrawer } from "../incidents/IncidentDrawer";
import { parseIncidentId } from "../incidents/incidentId";
import { HISTORY_PAGE_SIZE, historyQueryOptions } from "./api";
import { historySearchParams, pageCount, parseHistoryFilters } from "./filters";
import { HistoryView } from "./HistoryView";

export function HistoryPage() {
  const [params, setParams] = useSearchParams();
  const filters = parseHistoryFilters(params);
  const query = useQuery(historyQueryOptions(filters));
  const now = useNow(60_000);
  const navigate = useNavigate();
  const { incidentId } = useParams();
  const openId = parseIncidentId(incidentId);
  const search = params.toString();
  const historyPath = `/historico${search === "" ? "" : `?${search}`}`;

  if (incidentId !== undefined && openId === null) return <Navigate to={historyPath} replace />;

  // A page past the end (an old link, or fewer incidents now) shows the last one instead of nothing.
  const lastPage = query.data === undefined ? 1 : pageCount(query.data.total, HISTORY_PAGE_SIZE);
  if (query.data !== undefined && !query.isPlaceholderData && filters.page > lastPage) {
    const lastPageSearch = historySearchParams({ ...filters, page: lastPage }).toString();
    return <Navigate to={`/historico?${lastPageSearch}`} replace />;
  }

  return (
    <>
      <HistoryView
        state={query.isPending ? "loading" : query.data === undefined ? "error" : "ready"}
        errorMessage={query.error?.message}
        onRetry={() => {
          void query.refetch();
        }}
        items={query.data?.items ?? []}
        total={query.data?.total ?? 0}
        filters={filters}
        onFiltersChange={(next) => {
          setParams(historySearchParams(next));
        }}
        hrefFor={(id) => `/historico/${String(id)}${search === "" ? "" : `?${search}`}`}
        now={now}
      />
      {openId !== null && (
        <IncidentDrawer
          key={openId}
          incidentId={openId}
          onClose={() => {
            void navigate(historyPath);
          }}
        />
      )}
    </>
  );
}
