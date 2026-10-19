import { describe, expect, it } from "vitest";

import { renderView } from "../../test/render";
import { Button } from "./Button";
import { CriticalityBadge } from "./CriticalityBadge";
import { Dialog } from "./Dialog";
import { EmptyState, ErrorState } from "./StateMessage";
import { StatusLabel } from "./StatusLabel";

describe("shared UI", () => {
  it("shows criticality with text, not only color", () => {
    const html = renderView(<CriticalityBadge criticality="HIGH" />);

    expect(html).toContain("Alta");
    expect(html).toContain("<svg");
  });

  it("gives every criticality badge the same width and an outline", () => {
    const classes = (["HIGH", "MEDIUM", "LOW"] as const).map((criticality) => {
      const html = renderView(<CriticalityBadge criticality={criticality} />);
      return /<span class="([^"]*)"/.exec(html)?.[1]?.split(" ") ?? [];
    });

    for (const list of classes) {
      expect(list).toContain("w-20");
      expect(list).toContain("border");
    }
  });

  it("keeps the icon on the left and centers the label in the space left", () => {
    const html = renderView(<CriticalityBadge criticality="MEDIUM" />);

    expect(html).toMatch(
      /<span class="[^"]*"><svg[\s\S]*?<\/svg><span class="[^"]*flex-1[^"]*text-center[^"]*">Média<\/span>/,
    );
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

  it("makes the retry button big enough to tap on a phone", () => {
    const html = renderView(<ErrorState message="Sem conexão." onRetry={() => undefined} />);

    expect(html).toMatch(
      /<button[^>]*class="[^"]*min-h-11[^"]*"[^>]*>(?:(?!<\/button>)[\s\S])*Tentar novamente/,
    );
  });

  it("tells the stylesheet which way the dialog enters", () => {
    const drawer = renderView(
      <Dialog open onClose={() => undefined} title="Incidente #7" variant="drawer">
        x
      </Dialog>,
    );
    const modal = renderView(
      <Dialog open onClose={() => undefined} title="Fechar incidente">
        x
      </Dialog>,
    );

    expect(drawer).toMatch(/<dialog[^>]*data-variant="drawer"/);
    expect(modal).toMatch(/<dialog[^>]*data-variant="modal"/);
  });

  it("shows the empty message with its action", () => {
    const html = renderView(
      <EmptyState message="Nenhum incidente ativo no momento." action={<a href="/x">Atalho</a>} />,
    );

    expect(html).toContain("Nenhum incidente ativo no momento.");
    expect(html).toContain("Atalho");
  });
});
