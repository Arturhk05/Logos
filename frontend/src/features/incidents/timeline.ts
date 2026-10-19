import type { IncidentDetail } from "../../api/client";

export type IncidentEvent = IncidentDetail["events"][number];

const CHANGE_LABELS: Record<IncidentEvent["to_status"], string> = {
  OPEN: "Devolvido à fila",
  INVESTIGATING: "Assumido",
  CLOSED: "Fechado",
  INCONCLUSIVE: "Marcado como inconclusivo",
};

/** What a change log entry means to the user. No previous status means the incident was reported (RN-12). */
export function eventLabel(event: Pick<IncidentEvent, "from_status" | "to_status">): string {
  return event.from_status === null ? "Reportado" : CHANGE_LABELS[event.to_status];
}
