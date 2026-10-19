import { QueryClient } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";

import { server } from "../test/server";
import { canAccess, handleUnauthorized, homePathFor, login, logout } from "./session";

const API = "http://localhost/api";
const camila = { id: 1, username: "camila", role: "ANALYST" };

describe("homePathFor", () => {
  it.each([
    ["ANALYST", "/fila"],
    ["SUPERVISOR", "/fila"],
    ["DRIVER", "/reportar"],
  ] as const)("sends %s to %s", (role, path) => {
    expect(homePathFor(role)).toBe(path);
  });
});

describe("canAccess", () => {
  it.each([
    ["ANALYST", "central", true],
    ["SUPERVISOR", "central", true],
    ["DRIVER", "central", false],
    ["ANALYST", "driver", false],
    ["SUPERVISOR", "driver", false],
    ["DRIVER", "driver", true],
  ] as const)("%s in the %s area is %s", (role, area, expected) => {
    expect(canAccess(role, area)).toBe(expected);
  });
});

describe("login", () => {
  it("logs in and returns the user", async () => {
    let body: unknown;
    server.use(
      http.post(`${API}/auth/login`, async ({ request }) => {
        body = await request.json();
        return HttpResponse.json(camila);
      }),
    );

    await expect(login({ username: "camila", password: "logos123" })).resolves.toEqual(camila);
    expect(body).toEqual({ username: "camila", password: "logos123" });
  });

  it("rejects wrong credentials with the API message", async () => {
    server.use(
      http.post(`${API}/auth/login`, () =>
        HttpResponse.json({ detail: "Usuário ou senha inválidos." }, { status: 401 }),
      ),
    );

    await expect(login({ username: "camila", password: "errada" })).rejects.toMatchObject({
      kind: "unauthorized",
      message: "Usuário ou senha inválidos.",
    });
  });
});

describe("logout", () => {
  it("ends the session", async () => {
    let called = false;
    server.use(
      http.post(`${API}/auth/logout`, () => {
        called = true;
        return new HttpResponse(null, { status: 204 });
      }),
    );

    await logout();

    expect(called).toBe(true);
  });
});

describe("handleUnauthorized", () => {
  it("warns about an expired session when there was one", () => {
    const client = new QueryClient();
    client.setQueryData(["me"], camila);
    const navigate = vi.fn();

    handleUnauthorized(client, navigate, "/fila/7");

    expect(navigate).toHaveBeenCalledWith("/login", { state: { expired: true } });
  });

  it("keeps the cached user, so the screens still on the way out do not break", () => {
    const client = new QueryClient();
    client.setQueryData(["me"], camila);

    handleUnauthorized(client, vi.fn(), "/fila/7");

    expect(client.getQueryData(["me"])).toEqual(camila);
  });

  it("keeps warning when several requests fail together", () => {
    const client = new QueryClient();
    client.setQueryData(["me"], camila);
    const navigate = vi.fn();

    handleUnauthorized(client, navigate, "/fila/7");
    handleUnauthorized(client, navigate, "/fila/7");

    expect(navigate).toHaveBeenLastCalledWith("/login", { state: { expired: true } });
  });

  it("does not warn on a first visit without a session", () => {
    const navigate = vi.fn();

    handleUnauthorized(new QueryClient(), navigate, "/fila");

    expect(navigate).toHaveBeenCalledWith("/login", { state: { expired: false } });
  });

  it("stays put when already on the login screen", () => {
    const navigate = vi.fn();

    handleUnauthorized(new QueryClient(), navigate, "/login");

    expect(navigate).not.toHaveBeenCalled();
  });
});
