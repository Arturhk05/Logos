import { CircleAlert, TriangleAlert } from "lucide-react";

import { Button } from "../../shared/ui/Button";
import { Dialog } from "../../shared/ui/Dialog";
import { acceptsReason, needsReason, type ConfirmedAction } from "./actions";

const REASON_MAX_LENGTH = 500;

const COPY: Record<ConfirmedAction, { title: string; confirm: string; example: string }> = {
  close: {
    title: "Fechar incidente",
    confirm: "Fechar incidente",
    example: "Ex.: pista liberada pela concessionária.",
  },
  inconclusive: {
    title: "Marcar como inconclusivo",
    confirm: "Marcar como inconclusivo",
    example: "Ex.: pista liberada pela concessionária.",
  },
  reopen: {
    title: "Devolver à fila?",
    confirm: "Devolver à fila",
    example: "Ex.: analista saiu do turno.",
  },
};

export interface ActionDialogProps {
  open: boolean;
  action: ConfirmedAction;
  /** Username of the current assignee, who leaves the incident when it goes back to the queue. */
  assignee?: string;
  assigneeIsUser: boolean;
  reason: string;
  onReasonChange: (value: string) => void;
  onConfirm: () => void;
  onCancel: () => void;
  pending: boolean;
  conflict?: string;
  error?: string;
  canConfirm: boolean;
  /** The incident changed since the dialog opened, and this action is no longer one of its options. */
  unavailable: boolean;
}

/**
 * Confirms a status change. Closing always records why (RN-05); sending back to the queue warns that
 * the assignee leaves and takes an optional reason (RN-11). A conflict or a failure keeps what was typed.
 */
export function ActionDialog(props: ActionDialogProps) {
  const copy = COPY[props.action];
  return (
    <Dialog open={props.open} onClose={props.onCancel} title={copy.title}>
      <form
        className="flex flex-col gap-4"
        onSubmit={(event) => {
          event.preventDefault();
          if (props.canConfirm) props.onConfirm();
        }}
      >
        {(props.conflict !== undefined || props.unavailable) && (
          <p
            role="alert"
            className="flex gap-2 rounded-lg border border-warning-line bg-warning-soft px-3 py-2.5 text-sm text-warning-ink"
          >
            <TriangleAlert aria-hidden className="mt-0.5 size-4 shrink-0" />
            <span>
              {props.conflict}
              {props.conflict !== undefined && props.unavailable && " "}
              {props.unavailable && "Este incidente mudou e esta ação não está mais disponível."}
            </span>
          </p>
        )}

        {needsReason(props.action) ? null : props.assignee === undefined ? (
          <p className="text-sm">
            O incidente volta para <strong className="font-semibold">Aberto</strong>, sem
            responsável.
          </p>
        ) : (
          <p className="text-sm">
            O incidente volta para <strong className="font-semibold">Aberto</strong> e{" "}
            {props.assigneeIsUser ? "você" : <strong>{props.assignee}</strong>} deixa de ser o
            responsável. Qualquer analista poderá assumi-lo.
          </p>
        )}

        {acceptsReason(props.action) && (
          <label className="flex flex-col gap-1.5 text-sm font-medium">
            {needsReason(props.action) ? "Motivo" : "Motivo (opcional)"}
            <textarea
              className="min-h-28 rounded-lg border border-line bg-surface p-3 font-normal text-ink focus:border-accent focus:outline-none"
              maxLength={REASON_MAX_LENGTH}
              required={needsReason(props.action)}
              value={props.reason}
              placeholder={copy.example}
              onChange={(event) => {
                props.onReasonChange(event.target.value);
              }}
            />
            <span className="self-end text-xs font-normal text-muted tabular-nums">
              {props.reason.length}/{REASON_MAX_LENGTH}
            </span>
          </label>
        )}

        {/* Always rendered with room for one line, so a message never moves the buttons. */}
        <p
          role="alert"
          className="flex min-h-5 items-start gap-2 text-sm leading-5 text-critical-ink"
        >
          {props.error !== undefined && (
            <>
              <CircleAlert aria-hidden className="mt-0.5 size-4 shrink-0" />
              {props.error}
            </>
          )}
        </p>

        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={props.onCancel}>
            Cancelar
          </Button>
          <Button type="submit" pending={props.pending} disabled={!props.canConfirm}>
            {copy.confirm}
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
