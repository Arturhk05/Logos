import { LogOut } from "lucide-react";
import { NavLink, Outlet } from "react-router";

import { ROLE_LABELS } from "../shared/labels";
import { Button } from "../shared/ui/Button";
import { useCurrentUser, useLogout } from "./session";

const TAB =
  "flex h-full items-center border-b-2 px-1 text-sm transition-colors aria-[current=page]:border-accent aria-[current=page]:font-semibold aria-[current=page]:text-ink";

export function CentralLayout() {
  const user = useCurrentUser();
  const logout = useLogout();

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="sticky top-0 z-10 border-b border-line bg-surface">
        <div className="mx-auto flex h-14 max-w-7xl items-center gap-6 px-4">
          <span className="text-lg font-extrabold tracking-tight">Logos</span>
          <nav aria-label="Principal" className="flex h-full gap-5">
            <NavLink to="/fila" className={`${TAB} border-transparent text-muted hover:text-ink`}>
              Fila
            </NavLink>
            <NavLink
              to="/historico"
              className={`${TAB} border-transparent text-muted hover:text-ink`}
            >
              Histórico
            </NavLink>
          </nav>
          <div className="ml-auto flex items-center gap-3 text-sm">
            <span className="hidden text-muted sm:inline">
              <span className="font-medium text-ink">{user.username}</span> ·{" "}
              {ROLE_LABELS[user.role]}
            </span>
            <Button variant="ghost" onClick={logout}>
              <LogOut aria-hidden className="size-4" />
              Sair
            </Button>
          </div>
        </div>
      </header>
      <div className="mx-auto w-full max-w-7xl flex-1 px-4 py-6">
        <Outlet />
      </div>
    </div>
  );
}
