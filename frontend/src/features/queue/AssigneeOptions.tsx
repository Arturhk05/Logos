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
  return (
    <div
      role="group"
      aria-label="Filtrar por responsável"
      className="flex rounded-lg border border-line bg-surface p-0.5"
    >
      {OPTIONS.map(({ value, label, Icon }) => {
        const pressed = selected === value;
        return (
          <button
            key={label}
            type="button"
            aria-pressed={pressed}
            className={`flex min-h-8.5 items-center gap-2 rounded-md px-3 text-sm whitespace-nowrap transition active:scale-[0.97] ${pressed ? "bg-accent text-on-accent" : "hover:bg-canvas"}`}
            onClick={() => {
              onChange(value);
            }}
          >
            <Icon aria-hidden className={`size-4 ${pressed ? "" : "text-muted"}`} />
            {label}
          </button>
        );
      })}
    </div>
  );
}
