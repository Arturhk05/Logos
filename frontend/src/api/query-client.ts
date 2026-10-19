import { QueryClient } from "@tanstack/react-query";

import { ApiError, type ApiErrorKind } from "./errors";

const MAX_RETRIES = 3;
const BASE_DELAY_MS = 1000;
// Caps the wait a Retry-After can ask for, so a wrong header never leaves the screen waiting for minutes.
const MAX_DELAY_MS = 60_000;

// Failures that may succeed on a new attempt; the others would only repeat (RNF-03).
const TEMPORARY_FAILURES: ReadonlySet<ApiErrorKind> = new Set([
  "network",
  "timeout",
  "unavailable",
  "server",
  "rate_limited",
]);

export function shouldRetry(failureCount: number, error: Error): boolean {
  return (
    failureCount < MAX_RETRIES && error instanceof ApiError && TEMPORARY_FAILURES.has(error.kind)
  );
}

export function retryDelay(failureCount: number, error: Error): number {
  if (error instanceof ApiError && error.retryAfterSeconds !== undefined) {
    return Math.min(error.retryAfterSeconds * 1000, MAX_DELAY_MS);
  }
  return BASE_DELAY_MS * 2 ** failureCount;
}

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: shouldRetry, retryDelay },
    // Repeating an assume or a status change behind the user's back could confuse them; retrying is their choice.
    mutations: { retry: false },
  },
});
