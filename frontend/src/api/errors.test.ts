import { describe, expect, it } from "vitest";

import { ApiError } from "./errors";

function response(status: number, headers?: Record<string, string>): Response {
  return new Response(null, { status, headers });
}

describe("ApiError.fromResponse", () => {
  it.each([
    [401, "unauthorized"],
    [403, "forbidden"],
    [404, "not_found"],
    [409, "conflict"],
    [422, "invalid"],
    [429, "rate_limited"],
    [500, "server"],
    [502, "unavailable"],
    [503, "unavailable"],
    [504, "unavailable"],
    [400, "server"],
  ])("maps status %i to %s", (status, kind) => {
    const error = ApiError.fromResponse(response(status), {});

    expect(error.kind).toBe(kind);
    expect(error.status).toBe(status);
  });

  it("uses the message sent by the API", () => {
    const error = ApiError.fromResponse(response(403), {
      detail: "Você não pode alterar este incidente.",
    });

    expect(error.message).toBe("Você não pode alterar este incidente.");
  });

  it("ignores the message of a status the API does not use", () => {
    const error = ApiError.fromResponse(response(405), { detail: "Method Not Allowed" });

    expect(error.message).toBe("Ocorreu um erro inesperado. Tente novamente em instantes.");
  });

  it.each([
    ["an HTML page", "<html><body>502 Bad Gateway</body></html>"],
    ["an empty body", undefined],
    ["a body without detail", {}],
    ["a detail that is not text", { detail: [{ loc: ["body"], msg: "Field required" }] }],
    ["a blank detail", { detail: "  " }],
  ])("falls back to a default message for %s", (_, body) => {
    const error = ApiError.fromResponse(response(502), body);

    expect(error.message).toBe(
      "O sistema está temporariamente indisponível. Tente novamente em instantes.",
    );
  });

  it("reads Retry-After in seconds on 429", () => {
    const error = ApiError.fromResponse(response(429, { "Retry-After": "30" }), {});

    expect(error.retryAfterSeconds).toBe(30);
  });

  it.each([
    ["an HTTP date", { "Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT" }],
    ["a missing header", undefined],
  ])("ignores %s in Retry-After", (_, headers) => {
    const error = ApiError.fromResponse(response(429, headers), {});

    expect(error.retryAfterSeconds).toBeUndefined();
  });

  it("keeps the current incident sent with a conflict", () => {
    const current = { id: 7, version: 4, status: "INVESTIGATING" };

    const error = ApiError.fromResponse(response(409), {
      detail: "Alterado por outra pessoa.",
      current,
    });

    expect(error.current).toEqual({ id: 7, version: 4, status: "INVESTIGATING" });
  });

  it("has no current incident when the conflict body lacks it", () => {
    expect(ApiError.fromResponse(response(409), { detail: "x" }).current).toBeUndefined();
  });
});

describe("ApiError", () => {
  it.each([
    ["unauthorized", "Sua sessão expirou. Entre novamente."],
    ["forbidden", "Você não tem permissão para esta ação."],
    ["not_found", "Não encontramos o que você procurava."],
    ["conflict", "Este incidente foi alterado por outra pessoa. Confira como ele está agora."],
    ["invalid", "Dados inválidos. Revise os campos e tente novamente."],
    ["rate_limited", "Muitas tentativas seguidas. Aguarde um pouco e tente novamente."],
    ["unavailable", "O sistema está temporariamente indisponível. Tente novamente em instantes."],
    ["server", "Ocorreu um erro inesperado. Tente novamente em instantes."],
    ["network", "Sem conexão. Verifique sua internet e tente novamente."],
    ["timeout", "O sistema demorou para responder. Tente novamente."],
  ] as const)("has a default message for %s", (kind, message) => {
    const error = new ApiError(kind);

    expect(error).toBeInstanceOf(Error);
    expect(error.message).toBe(message);
    expect(error.status).toBeUndefined();
  });
});
