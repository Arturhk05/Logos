import type { ReactNode } from "react";

interface ToggleButtonProps {
  pressed: boolean;
  onToggle: () => void;
  /** "critical" fills red when on: only for high criticality. */
  tone?: "default" | "critical";
  children: ReactNode;
}

/** A filter that is on or off: filled when on, outlined with hover and press feedback when off. */
export function ToggleButton({ pressed, onToggle, tone = "default", children }: ToggleButtonProps) {
  const look = pressed
    ? tone === "critical"
      ? "border-critical bg-critical text-white"
      : "border-accent bg-accent text-on-accent"
    : "border-line bg-surface hover:border-line-strong hover:bg-canvas";
  return (
    <button
      type="button"
      aria-pressed={pressed}
      className={`flex min-h-10 items-center gap-2 rounded-lg border px-3 text-sm transition active:scale-[0.97] ${look}`}
      onClick={onToggle}
    >
      {children}
    </button>
  );
}
