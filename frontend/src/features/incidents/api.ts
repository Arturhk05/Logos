import { queryOptions } from "@tanstack/react-query";

import { api, request, type IncidentDetail } from "../../api/client";
import type { IncidentStatus } from "../../shared/labels";

// Same pace as the queue: the version on screen stays close to the current one (ADR-02).
const DETAIL_REFRESH_MS = 15_000;

export function incidentQueryOptions(id: number) {
  return queryOptions({
    queryKey: ["incidents", "detail", id],
    queryFn: ({ signal }) =>
      request(
        api.GET("/api/incidents/{incident_id}", {
          params: { path: { incident_id: id } },
          signal,
        }),
      ),
    refetchInterval: DETAIL_REFRESH_MS,
  });
}

/** Sends the version the user saw; a change by someone else in between makes the API answer 409. */
export function assumeIncident(incident: IncidentDetail): Promise<IncidentDetail> {
  return request(
    api.POST("/api/incidents/{incident_id}/assume", {
      params: { path: { incident_id: incident.id } },
      body: { version: incident.version },
    }),
  );
}

export function changeStatus(
  incident: IncidentDetail,
  status: IncidentStatus,
  reason?: string,
): Promise<IncidentDetail> {
  return request(
    api.PATCH("/api/incidents/{incident_id}/status", {
      params: { path: { incident_id: incident.id } },
      body: { version: incident.version, status, ...(reason === undefined ? {} : { reason }) },
    }),
  );
}
