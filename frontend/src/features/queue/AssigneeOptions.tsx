import { UserCheck, Users, UserX, type LucideIcon } from "lucide-react";

import type { AssigneeFilter } from "./filters";

const OPTIONS: { value: AssigneeFilter | null; label: string; Icon: LucideIcon }[] = [
  { value: null, label: "Todos", Icon: Users },
  { value: "none", label: "Sem responsável", Icon: UserX },
  { value: "me", label: "Assumidos por mim", Icon: UserCheck },
];

interface AssigneeOptionsProps {
  selected: AssigneeFilter | null;
  onChange: (assignee: AssigneeFilter | null) => void;
}

/** One choice at a time: "unassigned" and "assigned to me" together would always be empty. */
export function AssigneeOptions({ selected, onChange }: AssigneeOptionsProps) {
  // On a phone the three options share the full width, without icons, and a label may wrap
  // instead of pushing the page sideways.
  return (
    <div
      role="group"
      aria-label="Filtrar por responsável"
      className="flex w-full rounded-lg border border-line bg-surface p-0.5 sm:w-auto"
    >
      {OPTIONS.map(({ value, label, Icon }) => {
        const pressed = selected === value;
        return (
          <button
            key={label}
            type="button"
            aria-pressed={pressed}
            className={`flex min-h-8.5 min-w-0 flex-1 items-center justify-center gap-2 rounded-md px-2 py-1 text-center text-sm leading-tight transition active:scale-[0.97] sm:flex-none sm:px-3 sm:whitespace-nowrap ${pressed ? "bg-accent text-on-accent" : "hover:bg-canvas"}`}
            onClick={() => {
              onChange(value);
            }}
          >
            <Icon
              aria-hidden
              className={`hidden size-4 shrink-0 sm:block ${pressed ? "" : "text-muted"}`}
            />
            {label}
          </button>
        );
      })}
    </div>
  );
}
