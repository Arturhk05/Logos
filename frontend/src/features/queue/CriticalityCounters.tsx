import { SignalHigh, SignalLow, SignalMedium, type LucideIcon } from "lucide-react";

import { CRITICALITIES, CRITICALITY_LABELS, type Criticality } from "../../shared/labels";
import { ToggleButton } from "../../shared/ui/ToggleButton";

const ICONS: Record<Criticality, LucideIcon> = {
  HIGH: SignalHigh,
  MEDIUM: SignalMedium,
  LOW: SignalLow,
};

interface CriticalityCountersProps {
  /** Without counts (e.g. in the history), only the toggles are shown. */
  counts?: Partial<Record<Criticality, number>>;
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
        return (
          <ToggleButton
            key={criticality}
            pressed={pressed}
            tone={high ? "critical" : "default"}
            onToggle={() => {
              onToggle(criticality);
            }}
          >
            <Icon
              aria-hidden
              className={`size-4 ${pressed ? "" : high ? "text-critical-ink" : "text-muted"}`}
            />
            <span>{CRITICALITY_LABELS[criticality]}</span>
            {counts !== undefined && (
              <span
                className={`text-base font-bold tabular-nums ${!pressed && high ? "text-critical-ink" : ""}`}
              >
                {counts[criticality] ?? 0}
              </span>
            )}
          </ToggleButton>
        );
      })}
    </div>
  );
}
