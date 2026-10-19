import { describe, expect, it } from "vitest";

import { ApiError } from "./errors";
import { queryClient, retryDelay, shouldRetry } from "./query-client";

describe("shouldRetry", () => {
  it.each(["network", "timeout", "unavailable", "server", "rate_limited"] as const)(
    "retries a temporary failure (%s)",
    (kind) => {
      expect(shouldRetry(0, new ApiError(kind))).toBe(true);
    },
  );

  it.each(["unauthorized", "forbidden", "not_found", "conflict", "invalid"] as const)(
    "does not retry a failure that would repeat (%s)",
    (kind) => {
      expect(shouldRetry(0, new ApiError(kind))).toBe(false);
    },
  );

  it("retries at most three times", () => {
    expect(shouldRetry(2, new ApiError("network"))).toBe(true);
    expect(shouldRetry(3, new ApiError("network"))).toBe(false);
  });

  it("does not retry errors that did not come from the API", () => {
    expect(shouldRetry(0, new TypeError("x is undefined"))).toBe(false);
  });
});

describe("retryDelay", () => {
  it.each([
    [0, 1000],
    [1, 2000],
    [2, 4000],
  ])("waits longer after each failure (failure %i: %i ms)", (failureCount, expected) => {
    expect(retryDelay(failureCount, new ApiError("network"))).toBe(expected);
  });

  it("waits as long as the API asks on a rate limit", () => {
    expect(retryDelay(0, new ApiError("rate_limited", { retryAfterSeconds: 30 }))).toBe(30_000);
  });

  it("never waits more than a minute, whatever the API asks", () => {
    expect(retryDelay(0, new ApiError("rate_limited", { retryAfterSeconds: 1e20 }))).toBe(60_000);
  });

  it("backs off normally when the rate limit gives no wait time", () => {
    expect(retryDelay(1, new ApiError("rate_limited"))).toBe(2000);
  });
});

describe("queryClient", () => {
  it("uses the retry policy for reads", () => {
    const queries = queryClient.getDefaultOptions().queries;

    expect(queries?.retry).toBe(shouldRetry);
    expect(queries?.retryDelay).toBe(retryDelay);
  });

  it("never retries writes", () => {
    expect(queryClient.getDefaultOptions().mutations?.retry).toBe(false);
  });
});
