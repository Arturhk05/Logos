import {
  incidentSearchParams,
  parseIncidentFilters,
  pick,
  type IncidentFilters,
} from "../queue/filters";

export type ClosedStatus = "CLOSED" | "INCONCLUSIVE";
export const CLOSED_STATUSES: readonly ClosedStatus[] = ["CLOSED", "INCONCLUSIVE"];

export interface HistoryFilters extends IncidentFilters {
  status: ClosedStatus[];
  page: number;
}

export function parseHistoryFilters(params: URLSearchParams): HistoryFilters {
  const page = params.get("page") ?? "";
  return {
    ...parseIncidentFilters(params),
    status: pick(params.getAll("status"), CLOSED_STATUSES),
    page: /^\d+$/.test(page) && Number(page) >= 1 ? Number(page) : 1,
  };
}

export function historySearchParams(filters: HistoryFilters): URLSearchParams {
  const params = new URLSearchParams();
  for (const value of filters.status) params.append("status", value);
  for (const [name, value] of incidentSearchParams(filters)) params.append(name, value);
  if (filters.page > 1) params.set("page", String(filters.page));
  return params;
}

export function pageCount(total: number, pageSize: number): number {
  return Math.max(1, Math.ceil(total / pageSize));
}
