import { SignalHigh, SignalLow, SignalMedium, type LucideIcon } from "lucide-react";

import { CRITICALITIES, CRITICALITY_LABELS, type Criticality } from "../../shared/labels";

const ICONS: Record<Criticality, LucideIcon> = {
  HIGH: SignalHigh,
  MEDIUM: SignalMedium,
  LOW: SignalLow,
};

interface CriticalityCountersProps {
  counts: Partial<Record<Criticality, number>>;
  selected: readonly Criticality[];
  onToggle: (criticality: Criticality) => void;
}

/** How many active incidents of each criticality exist; each counter also turns its filter on and off. */
export function CriticalityCounters({ counts, selected, onToggle }: CriticalityCountersProps) {
  return (
    <div role="group" aria-label="Filtrar por criticidade" className="flex flex-wrap gap-2">
      {CRITICALITIES.map((criticality) => {
        const Icon = ICONS[criticality];
        const pressed = selected.includes(criticality);
        const high = criticality === "HIGH";
        // On: filled (red only for high criticality); off: outlined, with feedback on hover and press.
        const look = pressed
          ? high
            ? "border-critical bg-critical text-white"
            : "border-accent bg-accent text-on-accent"
          : "border-line bg-surface hover:border-line-strong hover:bg-canvas";
        return (
          <button
            key={criticality}
            type="button"
            aria-pressed={pressed}
            className={`flex min-h-10 items-center gap-2 rounded-lg border px-3 text-sm transition active:scale-[0.97] ${look}`}
            onClick={() => {
              onToggle(criticality);
            }}
          >
            <Icon
              aria-hidden
              className={`size-4 ${pressed ? "" : high ? "text-critical" : "text-muted"}`}
            />
            <span>{CRITICALITY_LABELS[criticality]}</span>
            <span
              className={`text-base font-bold tabular-nums ${!pressed && high ? "text-critical" : ""}`}
            >
              {counts[criticality] ?? 0}
            </span>
          </button>
        );
      })}
    </div>
  );
}
