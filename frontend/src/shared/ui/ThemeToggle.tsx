import { Moon, Sun } from "lucide-react";

import { nextTheme, type Theme } from "../theme";

const LABELS: Record<Theme, string> = {
  light: "Tema claro. Mudar para o escuro",
  dark: "Tema escuro. Mudar para o claro",
};

interface ThemeToggleProps {
  theme: Theme;
  onChange: (theme: Theme) => void;
}

/** Switches between the light and the dark theme; the icon shows the current one. */
export function ThemeToggle({ theme, onChange }: ThemeToggleProps) {
  const Icon = theme === "light" ? Sun : Moon;
  return (
    <button
      type="button"
      aria-label={LABELS[theme]}
      title={LABELS[theme]}
      onClick={() => {
        onChange(nextTheme(theme));
      }}
      className="inline-flex size-11 shrink-0 items-center justify-center rounded-lg text-muted transition-colors hover:bg-canvas hover:text-ink"
    >
      <Icon aria-hidden className="size-5" />
    </button>
  );
}
