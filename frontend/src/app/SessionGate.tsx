import { useQuery } from "@tanstack/react-query";
import { LoaderCircle } from "lucide-react";
import { Navigate, Outlet } from "react-router";

import { ApiError } from "../api/errors";
import { ErrorState } from "../shared/ui/StateMessage";
import { LOGIN_PATH, meQueryOptions } from "./session";

/** Lets the routes below render only for a logged-in user. */
export function SessionGate() {
  const { error, isPending, refetch } = useQuery(meQueryOptions);

  if (isPending) {
    return (
      <div aria-busy="true" className="flex min-h-dvh items-center justify-center text-muted">
        <LoaderCircle aria-hidden className="size-6 animate-spin" />
        <span className="sr-only">Carregando</span>
      </div>
    );
  }
  if (error instanceof ApiError && error.kind === "unauthorized") {
    return <Navigate to={LOGIN_PATH} replace />;
  }
  if (error !== null) {
    return (
      <ErrorState
        message={error.message}
        onRetry={() => {
          void refetch();
        }}
      />
    );
  }
  return <Outlet />;
}
