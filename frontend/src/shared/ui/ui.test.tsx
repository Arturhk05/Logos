import { describe, expect, it } from "vitest";

import { renderView } from "../../test/render";
import { Button } from "./Button";
import { CriticalityBadge } from "./CriticalityBadge";
import { EmptyState, ErrorState } from "./StateMessage";
import { StatusLabel } from "./StatusLabel";

describe("shared UI", () => {
  it("shows criticality with text, not only color", () => {
    const html = renderView(<CriticalityBadge criticality="HIGH" />);

    expect(html).toContain("Alta");
    expect(html).toContain("<svg");
  });

  it("shows status with text and an icon", () => {
    const html = renderView(<StatusLabel status="INVESTIGATING" />);

    expect(html).toContain("Em Investigação");
    expect(html).toContain("<svg");
  });

  it("disables a pending button", () => {
    expect(renderView(<Button pending>Assumir</Button>)).toMatch(/<button[^>]*disabled=""/);
  });

  it("shows the error message with a retry button", () => {
    const html = renderView(
      <ErrorState
        message="Sem conexão. Verifique sua internet e tente novamente."
        onRetry={() => undefined}
      />,
    );

    expect(html).toContain("Sem conexão. Verifique sua internet e tente novamente.");
    expect(html).toContain("Tentar novamente");
  });

  it("shows the empty message with its action", () => {
    const html = renderView(
      <EmptyState message="Nenhum incidente ativo no momento." action={<a href="/x">Atalho</a>} />,
    );

    expect(html).toContain("Nenhum incidente ativo no momento.");
    expect(html).toContain("Atalho");
  });
});
