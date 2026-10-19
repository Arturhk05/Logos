import { delay, http, HttpResponse } from "msw";
import { afterEach, describe, expect, expectTypeOf, it, vi } from "vitest";

import { server } from "../test/server";
import { api, request, REQUEST_TIMEOUT_MS, setUnauthorizedHandler } from "./client";
import { ApiError } from "./errors";
import type { components } from "./schema";

const API = "http://localhost/api";

const camila = { id: 1, username: "camila", role: "ANALYST" };

afterEach(() => {
  setUnauthorizedHandler(undefined);
  vi.useRealTimers();
});

async function failure(call: Promise<unknown>): Promise<ApiError> {
  const error: unknown = await call.catch((reason: unknown) => reason);
  expect(error).toBeInstanceOf(ApiError);
  return error as ApiError;
}

describe("request", () => {
  it("returns the response data", async () => {
    server.use(http.get(`${API}/me`, () => HttpResponse.json(camila)));

    const user = await request(api.GET("/api/me"));

    expectTypeOf(user).toEqualTypeOf<components["schemas"]["UserResponse"]>();
    expect(user).toEqual(camila);
  });

  it("returns undefined for an empty success response", async () => {
    server.use(http.post(`${API}/auth/logout`, () => new HttpResponse(null, { status: 204 })));

    await expect(request(api.POST("/api/auth/logout"))).resolves.toBeUndefined();
  });

  it("throws the API message on an error response", async () => {
    server.use(
      http.get(`${API}/incidents`, () =>
        HttpResponse.json({ detail: "Você não tem permissão para esta ação." }, { status: 403 }),
      ),
    );

    const error = await failure(request(api.GET("/api/incidents")));

    expect(error.kind).toBe("forbidden");
    expect(error.message).toBe("Você não tem permissão para esta ação.");
  });

  it("keeps the current incident on a conflict", async () => {
    const current = { id: 7, version: 4, status: "INVESTIGATING" };
    server.use(
      http.patch(`${API}/incidents/7/status`, () =>
        HttpResponse.json({ detail: "Alterado por outra pessoa.", current }, { status: 409 }),
      ),
    );

    const error = await failure(
      request(
        api.PATCH("/api/incidents/{incident_id}/status", {
          params: { path: { incident_id: 7 } },
          body: { status: "CLOSED", version: 3, reason: "Pneu trocado" },
        }),
      ),
    );

    expect(error.kind).toBe("conflict");
    expect(error.current).toEqual(current);
  });

  it("shows a friendly message when the server answers with an HTML page", async () => {
    server.use(
      http.get(`${API}/incidents`, () =>
        HttpResponse.html("<html>502 Bad Gateway</html>", { status: 502 }),
      ),
    );

    const error = await failure(request(api.GET("/api/incidents")));

    expect(error.kind).toBe("unavailable");
    expect(error.message).toBe(
      "O sistema está temporariamente indisponível. Tente novamente em instantes.",
    );
  });

  it("reads how long to wait on a rate limit", async () => {
    server.use(
      http.get(`${API}/incidents`, () =>
        HttpResponse.json(
          { detail: "Muitas requisições." },
          { status: 429, headers: { "Retry-After": "30" } },
        ),
      ),
    );

    const error = await failure(request(api.GET("/api/incidents")));

    expect(error.kind).toBe("rate_limited");
    expect(error.retryAfterSeconds).toBe(30);
  });

  it("does not blame the connection when a success response is not readable", async () => {
    server.use(http.get(`${API}/me`, () => HttpResponse.html("<html>Logos</html>")));

    const error = await failure(request(api.GET("/api/me")));

    expect(error.kind).toBe("server");
  });

  it("reports a network failure", async () => {
    server.use(http.get(`${API}/me`, () => HttpResponse.error()));

    const error = await failure(request(api.GET("/api/me")));

    expect(error.kind).toBe("network");
    expect(error.message).toBe("Sem conexão. Verifique sua internet e tente novamente.");
  });

  it("gives up after the request timeout", async () => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
    server.use(
      http.get(`${API}/me`, async () => {
        await delay("infinite");
        return HttpResponse.json(camila);
      }),
    );

    const pending = failure(request(api.GET("/api/me")));
    await vi.advanceTimersByTimeAsync(REQUEST_TIMEOUT_MS);

    expect((await pending).kind).toBe("timeout");
  });

  it("does not turn a cancellation into an error for the user", async () => {
    server.use(
      http.get(`${API}/me`, async () => {
        await delay("infinite");
        return HttpResponse.json(camila);
      }),
    );
    const controller = new AbortController();

    const pending = request(api.GET("/api/me", { signal: controller.signal })).catch(
      (reason: unknown) => reason,
    );
    controller.abort();
    const error = await pending;

    expect(error).not.toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ name: "AbortError" });
  });
});

describe("unauthorized handler", () => {
  it("is called when the session is no longer valid", async () => {
    const onUnauthorized = vi.fn();
    setUnauthorizedHandler(onUnauthorized);
    server.use(
      http.get(`${API}/me`, () =>
        HttpResponse.json({ detail: "Sessão expirada." }, { status: 401 }),
      ),
    );

    const error = await failure(request(api.GET("/api/me")));

    expect(error.kind).toBe("unauthorized");
    expect(onUnauthorized).toHaveBeenCalledOnce();
  });

  it("is not called for wrong credentials on the login", async () => {
    const onUnauthorized = vi.fn();
    setUnauthorizedHandler(onUnauthorized);
    server.use(
      http.post(`${API}/auth/login`, () =>
        HttpResponse.json({ detail: "Usuário ou senha incorretos." }, { status: 401 }),
      ),
    );

    const error = await failure(
      request(api.POST("/api/auth/login", { body: { username: "camila", password: "errada" } })),
    );

    expect(error.message).toBe("Usuário ou senha incorretos.");
    expect(onUnauthorized).not.toHaveBeenCalled();
  });
});
