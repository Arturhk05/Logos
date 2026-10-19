import { SignalHigh, SignalLow, SignalMedium, type LucideIcon } from "lucide-react";

import { CRITICALITY_LABELS, type Criticality } from "../labels";

const ICONS: Record<Criticality, LucideIcon> = {
  HIGH: SignalHigh,
  MEDIUM: SignalMedium,
  LOW: SignalLow,
};

// Only high criticality gets color; medium and low differ by weight, so the exception stands out.
const STYLES: Record<Criticality, string> = {
  HIGH: "bg-critical text-white",
  MEDIUM: "border border-line-strong text-ink",
  LOW: "text-muted",
};

export function CriticalityBadge({ criticality }: { criticality: Criticality }) {
  const Icon = ICONS[criticality];
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold whitespace-nowrap ${STYLES[criticality]}`}
    >
      <Icon aria-hidden className="size-3.5" />
      {CRITICALITY_LABELS[criticality]}
    </span>
  );
}
