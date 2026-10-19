import createClient, { type Middleware } from "openapi-fetch";

import { ApiError } from "./errors";
import type { components, paths } from "./schema";

export type IncidentDetail = components["schemas"]["IncidentDetail"];

export const REQUEST_TIMEOUT_MS = 15_000;

// Wrong credentials answer 401 too; the login screen shows them instead of redirecting.
const LOGIN_PATH = "/api/auth/login";

type UnauthorizedHandler = () => void;

let onUnauthorized: UnauthorizedHandler | undefined;

export function setUnauthorizedHandler(handler: UnauthorizedHandler | undefined): void {
  onUnauthorized = handler;
}

const unauthorizedMiddleware: Middleware = {
  onResponse({ response, schemaPath }) {
    if (response.status === 401 && schemaPath !== LOGIN_PATH) onUnauthorized?.();
  },
};

// The timeout covers the wait for the response headers; JSON bodies are small enough not to stall.
// fetch is looked up on each call, so the MSW interceptor installed by the tests is used.
async function fetchWithTimeout(request: Request): Promise<Response> {
  const timeout = new AbortController();
  const timer = setTimeout(() => {
    timeout.abort(new DOMException("The request timed out", "TimeoutError"));
  }, REQUEST_TIMEOUT_MS);
  try {
    return await fetch(request, { signal: AbortSignal.any([request.signal, timeout.signal]) });
  } catch (error) {
    // A cancellation by TanStack Query is not a failure to show to the user.
    if (isNamedError(error, "AbortError")) throw error;
    // Classified here, so only a failed fetch can blame the connection.
    throw new ApiError(timeout.signal.aborted ? "timeout" : "network");
  } finally {
    clearTimeout(timer);
  }
}

// The API shares the page origin; an absolute URL also lets the client build requests outside the browser (tests).
export const api = createClient<paths>({ baseUrl: location.origin, fetch: fetchWithTimeout });
api.use(unauthorizedMiddleware);

interface FetchResult<T> {
  data?: T;
  error?: unknown;
  response: Response;
}

export async function request<T>(call: Promise<FetchResult<T>>): Promise<T> {
  let result: FetchResult<T>;
  try {
    result = await call;
  } catch (error) {
    if (error instanceof ApiError || isNamedError(error, "AbortError")) throw error;
    // E.g. a success response that is not JSON, such as a proxy page.
    throw new ApiError("server");
  }
  if (!result.response.ok) throw ApiError.fromResponse(result.response, result.error);
  // openapi-fetch leaves data undefined only for empty bodies, such as the 204 of the logout.
  return result.data as T;
}

function isNamedError(error: unknown, name: string): boolean {
  return error instanceof Error && error.name === name;
}
