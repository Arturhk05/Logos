import { describe, expect, it } from "vitest";

import { renderView } from "../../test/render";
import { LoginView, type LoginViewProps } from "./LoginView";

const props: LoginViewProps = {
  username: "",
  password: "",
  onChange: () => undefined,
  onSubmit: () => undefined,
  onPickDemo: () => undefined,
  pending: false,
  expired: false,
};

describe("LoginView", () => {
  it("lists the demo users of each role with the password", () => {
    const html = renderView(<LoginView {...props} />);

    for (const text of [
      "camila",
      "lucas",
      "roberto",
      "jose",
      "logos123",
      "Analista",
      "Supervisor",
      "Motorista",
    ]) {
      expect(html).toContain(text);
    }
  });

  it("shows the login error", () => {
    const html = renderView(<LoginView {...props} errorMessage="Usuário ou senha inválidos." />);

    expect(html).toContain("Usuário ou senha inválidos.");
  });

  it("shows the login error in red", () => {
    const html = renderView(<LoginView {...props} errorMessage="Usuário ou senha inválidos." />);

    expect(html).toMatch(/role="alert"[^>]*class="[^"]*text-critical/);
  });

  it("keeps the space of the error even without one, so the form does not grow", () => {
    const html = renderView(<LoginView {...props} />);

    expect(html).toMatch(/role="alert"[^>]*class="[^"]*min-h-5/);
  });

  it("shows the expired session notice", () => {
    expect(renderView(<LoginView {...props} expired />)).toContain(
      "Sua sessão expirou. Entre novamente.",
    );
  });

  it("does not show the notice on a normal visit", () => {
    expect(renderView(<LoginView {...props} />)).not.toContain("Sua sessão expirou");
  });

  it("disables the button while logging in", () => {
    expect(renderView(<LoginView {...props} pending />)).toMatch(/<button[^>]*disabled/);
  });
});
