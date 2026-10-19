import type { IncidentDetail } from "../../api/client";
import type { CurrentUser } from "../../app/session";

/** Says what changed while the user was looking (RN-08), so they understand why their action was refused. */
export function conflictMessage(
  current: IncidentDetail,
  user: Pick<CurrentUser, "id">,
  fallback: string,
): string {
  if (current.closed_by !== null) {
    return `Este incidente foi encerrado por ${current.closed_by.username}.`;
  }
  if (current.assignee !== null && current.assignee.id !== user.id) {
    return `${current.assignee.username} assumiu este incidente antes de você.`;
  }
  return fallback;
}
