import { CirclePlus, List, LogOut } from "lucide-react";
import { NavLink, Outlet } from "react-router";

import { Button } from "../shared/ui/Button";
import { ThemeSwitch } from "../shared/ui/ThemeSwitch";
import { useCurrentUser, useLogout } from "./session";

// Tabs at the bottom, within reach of the thumb; each one is taller than the 44 px minimum (RNF-07).
const TAB =
  "flex min-h-14 flex-1 flex-col items-center justify-center gap-0.5 text-xs text-muted aria-[current=page]:font-semibold aria-[current=page]:text-ink";

export function DriverLayout() {
  const user = useCurrentUser();
  const logout = useLogout();

  return (
    <div className="mx-auto flex min-h-dvh max-w-md flex-col bg-surface">
      <header className="flex items-center justify-between border-b border-line px-4 py-2">
        <span className="text-lg font-extrabold tracking-tight">Logos</span>
        <div className="flex items-center gap-1 text-sm text-muted">
          <span>{user.username}</span>
          <ThemeSwitch />
          <Button variant="ghost" onClick={logout} className="min-h-11">
            <LogOut aria-hidden className="size-4" />
            Sair
          </Button>
        </div>
      </header>
      <main className="flex-1 px-4 pt-4 pb-24">
        <Outlet />
      </main>
      <nav
        aria-label="Principal"
        className="fixed inset-x-0 bottom-0 mx-auto flex max-w-md border-t border-line bg-surface"
      >
        <NavLink viewTransition to="/reportar" className={TAB}>
          <CirclePlus aria-hidden className="size-5" />
          Reportar
        </NavLink>
        <NavLink viewTransition to="/meus-reportes" className={TAB}>
          <List aria-hidden className="size-5" />
          Meus reportes
        </NavLink>
      </nav>
    </div>
  );
}
