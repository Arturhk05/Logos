import { SignalHigh, SignalLow, SignalMedium, type LucideIcon } from "lucide-react";

import { CRITICALITY_LABELS, type Criticality } from "../labels";

const ICONS: Record<Criticality, LucideIcon> = {
  HIGH: SignalHigh,
  MEDIUM: SignalMedium,
  LOW: SignalLow,
};

// Only high criticality gets color; medium and low differ by the weight of the outline and the text,
// so the exception stands out.
const STYLES: Record<Criticality, string> = {
  HIGH: "border-critical bg-critical text-on-critical",
  MEDIUM: "border-line-strong text-ink",
  LOW: "border-line text-muted",
};

export function CriticalityBadge({ criticality }: { criticality: Criticality }) {
  const Icon = ICONS[criticality];
  // A fixed width, so a column of badges lines up whatever the label: the icon stays on the left and
  // the label is centered in the space left.
  return (
    <span
      className={`inline-flex w-20 items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-semibold whitespace-nowrap ${STYLES[criticality]}`}
    >
      <Icon aria-hidden className="size-3.5 shrink-0" />
      <span className="flex-1 text-center">{CRITICALITY_LABELS[criticality]}</span>
    </span>
  );
}
