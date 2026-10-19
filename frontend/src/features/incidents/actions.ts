import type { IncidentDetail } from "../../api/client";
import type { CurrentUser } from "../../app/session";
import type { IncidentStatus } from "../../shared/labels";

export type IncidentAction = "assume" | "close" | "inconclusive" | "reopen";
export type ReasonAction = "close" | "inconclusive";
export type ConfirmedAction = Exclude<IncidentAction, "assume">;

export const ACTION_TARGET: Record<ConfirmedAction, IncidentStatus> = {
  close: "CLOSED",
  inconclusive: "INCONCLUSIVE",
  reopen: "OPEN",
};

/**
 * What the user may do with the incident, so the screen only offers what the API would accept.
 * The API still checks every rule (RNF-09); this only hides what would be refused.
 */
export function availableActions(
  incident: Pick<IncidentDetail, "status" | "assignee">,
  user: Pick<CurrentUser, "id" | "role">,
): IncidentAction[] {
  if (user.role === "DRIVER") return [];
  if (incident.status === "OPEN" && incident.assignee === null) return ["assume"];
  const mayChange = user.role === "SUPERVISOR" || incident.assignee?.id === user.id;
  if (incident.status === "INVESTIGATING" && mayChange) return ["close", "inconclusive", "reopen"];
  return [];
}

export function needsReason(action: IncidentAction): action is ReasonAction {
  return action === "close" || action === "inconclusive";
}

/** Closing requires a reason (RN-05); sending back to the queue takes an optional one (RN-11). */
export function acceptsReason(action: IncidentAction): boolean {
  return needsReason(action) || action === "reopen";
}

/** The reason as the API should receive it: trimmed, and left out when there is none. */
export function reasonToSend(action: ConfirmedAction, reason: string): string | undefined {
  const trimmed = reason.trim();
  return acceptsReason(action) && trimmed !== "" ? trimmed : undefined;
}

/** Status changes are confirmed in a dialog: they end or undo someone's work. Assuming is one click. */
export function needsConfirmation(action: IncidentAction): action is ConfirmedAction {
  return action !== "assume";
}

/** Whether a dialog's confirm button works, judged on the incident as it is now, not as it was opened. */
export function confirmationState(
  action: ConfirmedAction,
  current: Pick<IncidentDetail, "status" | "assignee"> | undefined,
  user: Pick<CurrentUser, "id" | "role">,
  reason: string,
): { unavailable: boolean; canConfirm: boolean } {
  const unavailable = current === undefined || !availableActions(current, user).includes(action);
  const reasonMissing = needsReason(action) && reason.trim() === "";
  return { unavailable, canConfirm: !unavailable && !reasonMissing };
}
