import { CircleCheck, CircleDot, CircleHelp, Search, type LucideIcon } from "lucide-react";

import { STATUS_LABELS, type IncidentStatus } from "../labels";

const ICONS: Record<IncidentStatus, LucideIcon> = {
  OPEN: CircleDot,
  INVESTIGATING: Search,
  CLOSED: CircleCheck,
  INCONCLUSIVE: CircleHelp,
};

export function StatusLabel({ status }: { status: IncidentStatus }) {
  const Icon = ICONS[status];
  return (
    <span className="inline-flex items-center gap-1.5 whitespace-nowrap">
      <Icon aria-hidden className="size-4 text-muted" />
      {STATUS_LABELS[status]}
    </span>
  );
}
