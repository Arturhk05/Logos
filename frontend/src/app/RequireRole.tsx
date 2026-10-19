import { Navigate, Outlet } from "react-router";

import { canAccess, homePathFor, useCurrentUser, type Area } from "./session";

/** A screen of another role sends the user to their own home (US-11). */
export function RequireRole({ area }: { area: Area }) {
  const user = useCurrentUser();
  return canAccess(user.role, area) ? <Outlet /> : <Navigate to={homePathFor(user.role)} replace />;
}

export function HomeRedirect() {
  const user = useCurrentUser();
  return <Navigate to={homePathFor(user.role)} replace />;
}
