import { queryOptions, useQuery, useQueryClient, type QueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router";

import { api, request } from "../api/client";
import type { components } from "../api/schema";
import type { UserRole } from "../shared/labels";

export type CurrentUser = components["schemas"]["UserResponse"];
export type Area = "central" | "driver";

const ME_KEY = ["me"] as const;

export const meQueryOptions = queryOptions({
  queryKey: ME_KEY,
  queryFn: () => request(api.GET("/api/me")),
  // The user only changes on login and logout, which write the cache themselves.
  staleTime: Infinity,
});

export function login(credentials: { username: string; password: string }): Promise<CurrentUser> {
  return request(api.POST("/api/auth/login", { body: credentials }));
}

export function logout(): Promise<void> {
  return request(api.POST("/api/auth/logout"));
}

export function homePathFor(role: UserRole): "/fila" | "/reportar" {
  return role === "DRIVER" ? "/reportar" : "/fila";
}

export function canAccess(role: UserRole, area: Area): boolean {
  return area === "driver" ? role === "DRIVER" : role !== "DRIVER";
}

type Navigate = (to: string, options: { state: { expired: boolean } }) => void;

/** Called on any 401 outside the login: the session is gone, so the cached data of that user goes too. */
export function handleUnauthorized(queryClient: QueryClient, navigate: Navigate): void {
  // Without a cached user this is a first visit, not an expired session.
  const expired = queryClient.getQueryData(ME_KEY) !== undefined;
  queryClient.clear();
  navigate("/login", { state: { expired } });
}

/** The logged-in user, inside routes that SessionGate already protects. */
export function useCurrentUser(): CurrentUser {
  const { data } = useQuery(meQueryOptions);
  if (data === undefined) throw new Error("useCurrentUser must be used inside SessionGate");
  return data;
}

export function useLogout(): () => void {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  return () => {
    // Even if the request fails, this device stops showing the user's data.
    void logout()
      .catch(() => undefined)
      .finally(() => {
        queryClient.clear();
        void navigate("/login", { replace: true });
      });
  };
}
