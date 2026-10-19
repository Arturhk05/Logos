import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import type { IncidentDetail } from "../../api/client";
import { ApiError, type ApiErrorKind } from "../../api/errors";
import { useCurrentUser } from "../../app/session";
import { Dialog } from "../../shared/ui/Dialog";
import { useNow } from "../../shared/useNow";
import { ActionDialog } from "./ActionDialog";
import {
  ACTION_TARGET,
  availableActions,
  confirmationState,
  needsConfirmation,
  needsReason,
  type ConfirmedAction,
  type IncidentAction,
} from "./actions";
import { assumeIncident, changeStatus, incidentQueryOptions } from "./api";
import { conflictMessage } from "./conflict";
import { IncidentDrawerView } from "./IncidentDrawerView";

interface Attempt {
  action: IncidentAction;
  // The incident as the user saw it: a retry sends the same version, so a change in between is a conflict.
  incident: IncidentDetail;
  reason?: string;
}

const TEMPORARY_FAILURES: ReadonlySet<ApiErrorKind> = new Set([
  "network",
  "timeout",
  "unavailable",
  "server",
]);
const SAVE_FAILED_MESSAGE = "Não foi possível salvar.";

function save({ action, incident, reason }: Attempt): Promise<IncidentDetail> {
  return action === "assume"
    ? assumeIncident(incident)
    : changeStatus(incident, ACTION_TARGET[action], reason);
}

/**
 * The incident drawer. What the user is doing (the open dialog, the typed reason, a conflict)
 * lives in local state, never in the query data, so the periodic refresh cannot wipe it.
 */
export function IncidentDrawer({
  incidentId,
  onClose,
}: {
  incidentId: number;
  onClose: () => void;
}) {
  const user = useCurrentUser();
  const queryClient = useQueryClient();
  const detail = incidentQueryOptions(incidentId);
  const query = useQuery(detail);
  const now = useNow(30_000);

  // The incident as it was when the dialog opened: confirming sends that version, so a change made
  // while the user was typing is reported as a conflict instead of being overwritten (ADR-02).
  const [dialogFor, setDialogFor] = useState<{ action: ConfirmedAction; seen: IncidentDetail }>();
  const [reason, setReason] = useState("");
  const [conflict, setConflict] = useState<string>();
  const [saveError, setSaveError] = useState<string>();

  const mutation = useMutation({
    mutationFn: save,
    onSuccess: (updated) => {
      queryClient.setQueryData(detail.queryKey, updated);
      void queryClient.invalidateQueries({ queryKey: ["incidents"] });
      setConflict(undefined);
      setDialogFor(undefined);
      setReason("");
    },
    onError: (error) => {
      if (error instanceof ApiError && error.kind === "conflict" && error.current !== undefined) {
        const current = error.current;
        queryClient.setQueryData(detail.queryKey, current);
        void queryClient.invalidateQueries({ queryKey: ["incidents", "queue"] });
        setConflict(conflictMessage(current, user, error.message));
        // Having seen the conflict, the user now decides on the current version.
        setDialogFor((open) => (open === undefined ? undefined : { ...open, seen: current }));
        return;
      }
      const temporary = error instanceof ApiError && TEMPORARY_FAILURES.has(error.kind);
      setSaveError(temporary ? SAVE_FAILED_MESSAGE : error.message);
    },
  });

  const incident = query.data;
  const actions = incident === undefined ? [] : availableActions(incident, user);

  const attempt = (next: Attempt) => {
    setSaveError(undefined);
    setConflict(undefined);
    mutation.mutate(next);
  };

  const onAction = (action: IncidentAction) => {
    if (incident === undefined) return;
    if (needsConfirmation(action)) {
      setSaveError(undefined);
      setConflict(undefined);
      setDialogFor({ action, seen: incident });
      return;
    }
    attempt({ action, incident });
  };

  const inDialog = dialogFor !== undefined;

  return (
    <Dialog open onClose={onClose} title={`Incidente #${String(incidentId)}`} variant="drawer">
      <IncidentDrawerView
        state={query.isPending ? "loading" : incident === undefined ? "error" : "ready"}
        errorMessage={query.error?.message}
        incident={incident}
        actions={actions}
        pendingAction={mutation.isPending ? mutation.variables.action : undefined}
        conflict={inDialog ? undefined : conflict}
        saveError={inDialog ? undefined : saveError}
        onAction={onAction}
        onRetrySave={() => {
          // Mutation variables keep the version of the failed attempt.
          if (mutation.variables !== undefined) attempt(mutation.variables);
        }}
        now={now}
      />
      {dialogFor !== undefined && (
        <ActionDialog
          open
          action={dialogFor.action}
          assignee={dialogFor.seen.assignee?.username}
          assigneeIsUser={dialogFor.seen.assignee?.id === user.id}
          reason={reason}
          onReasonChange={setReason}
          onCancel={() => {
            setDialogFor(undefined);
            setSaveError(undefined);
          }}
          onConfirm={() => {
            attempt({
              action: dialogFor.action,
              incident: dialogFor.seen,
              reason: needsReason(dialogFor.action) ? reason.trim() : undefined,
            });
          }}
          pending={mutation.isPending}
          conflict={conflict}
          error={saveError}
          {...confirmationState(dialogFor.action, incident, user, reason)}
        />
      )}
    </Dialog>
  );
}
