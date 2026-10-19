import { CircleCheck, CircleHelp, FilePlus, Undo2, UserCheck, type LucideIcon } from "lucide-react";

import { formatDateTime } from "../../shared/format";
import { eventLabel, type IncidentEvent } from "./timeline";

const CHANGE_ICONS: Record<IncidentEvent["to_status"], LucideIcon> = {
  OPEN: Undo2,
  INVESTIGATING: UserCheck,
  CLOSED: CircleCheck,
  INCONCLUSIVE: CircleHelp,
};

/** Who changed the incident, when and why, oldest first (RN-12). Each entry has an icon and text. */
export function IncidentTimeline({ events, now }: { events: IncidentEvent[]; now: Date }) {
  if (events.length === 0) return null;
  return (
    <section aria-labelledby="incident-timeline" className="flex flex-col gap-3">
      <h4 id="incident-timeline" className="text-sm font-semibold">
        Linha do tempo
      </h4>
      <ol className="flex flex-col gap-3">
        {events.map((event, index) => {
          const Icon = event.from_status === null ? FilePlus : CHANGE_ICONS[event.to_status];
          return (
            <li key={index} className="flex gap-3 text-sm">
              <Icon aria-hidden className="mt-0.5 size-4 shrink-0 text-muted" />
              <div className="flex min-w-0 flex-col gap-0.5">
                <p>
                  <span className="font-medium">{eventLabel(event)}</span> por{" "}
                  {event.actor.username}
                </p>
                <time dateTime={event.created_at} className="text-xs text-muted">
                  {formatDateTime(event.created_at, now)}
                </time>
                {event.reason !== null && (
                  <p className="break-words whitespace-pre-line text-muted">“{event.reason}”</p>
                )}
              </div>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
