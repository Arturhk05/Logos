import { ChevronDown } from "lucide-react";
import { useEffect, useId, useRef, useState } from "react";

import { CATEGORIES, CATEGORY_LABELS, type IncidentCategory } from "../../shared/labels";
import { CategoryIcon } from "../../shared/ui/CategoryIcon";
import { toggle } from "./filters";

interface CategoryFilterProps {
  selected: readonly IncidentCategory[];
  onChange: (categories: IncidentCategory[]) => void;
}

export function CategoryFilter({ selected, onChange }: CategoryFilterProps) {
  const [open, setOpen] = useState(false);
  const container = useRef<HTMLDivElement>(null);
  const panelId = useId();

  useEffect(() => {
    if (!open) return;
    const closeOutside = (event: MouseEvent) => {
      if (!container.current?.contains(event.target as Node)) setOpen(false);
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", closeOutside);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("mousedown", closeOutside);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [open]);

  const [first] = selected;
  const summary =
    first === undefined
      ? "todas"
      : selected.length === 1
        ? CATEGORY_LABELS[first]
        : `${String(selected.length)} selecionadas`;

  return (
    <div ref={container} className="relative">
      <button
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => {
          setOpen((current) => !current);
        }}
        className={`flex min-h-10 items-center gap-2 rounded-lg border bg-surface px-3 text-sm hover:bg-canvas ${
          selected.length > 0 ? "border-accent ring-1 ring-accent" : "border-line"
        }`}
      >
        <span className="text-muted">Categoria:</span>
        <span className="max-w-48 truncate">{summary}</span>
        <ChevronDown aria-hidden className="size-4 text-muted" />
      </button>
      {open && (
        <fieldset
          id={panelId}
          className="absolute top-full left-0 z-20 mt-1 w-72 rounded-lg border border-line bg-surface p-1 shadow-lg"
        >
          <legend className="sr-only">Filtrar por categoria</legend>
          {CATEGORIES.map((category) => (
            <label
              key={category}
              className="flex min-h-10 cursor-pointer items-center gap-3 rounded-md px-2 text-sm hover:bg-canvas"
            >
              <input
                type="checkbox"
                className="size-4 accent-accent"
                checked={selected.includes(category)}
                onChange={() => {
                  onChange(toggle(selected, category));
                }}
              />
              <CategoryIcon category={category} className="size-4 text-muted" />
              {CATEGORY_LABELS[category]}
            </label>
          ))}
        </fieldset>
      )}
    </div>
  );
}
