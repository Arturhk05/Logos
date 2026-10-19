import { queryOptions, useQuery, type QueryClient } from "@tanstack/react-query";
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

export const LOGIN_PATH = "/login";

/**
 * Called on any 401 outside the login: the session is gone. The cache is left alone here, because the
 * screens of the old session are still mounted until the navigation commits; LoginPage clears it.
 */
export function handleUnauthorized(
  queryClient: QueryClient,
  navigate: Navigate,
  currentPath: string,
): void {
  if (currentPath === LOGIN_PATH) return;
  // Without a cached user this is a first visit, not an expired session.
  const expired = queryClient.getQueryData(ME_KEY) !== undefined;
  navigate(LOGIN_PATH, { state: { expired } });
}

/** The logged-in user, inside routes that SessionGate already protects. */
export function useCurrentUser(): CurrentUser {
  const { data } = useQuery(meQueryOptions);
  if (data === undefined) throw new Error("useCurrentUser must be used inside SessionGate");
  return data;
}

export function useLogout(): () => void {
  const navigate = useNavigate();
  return () => {
    // Even if the request fails, this device stops showing the user's data: LoginPage clears the cache.
    void logout()
      .catch(() => undefined)
      .finally(() => {
        void navigate(LOGIN_PATH, { replace: true });
      });
  };
}
