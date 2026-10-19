import { describe, expect, it } from "vitest";

import { renderView } from "../../test/render";
import { ActionDialog, type ActionDialogProps } from "./ActionDialog";

// What the user reads, without the markup around names in bold.
function textOf(html: string): string {
  return html.replace(/<[^>]+>/g, "");
}

const props: ActionDialogProps = {
  open: true,
  action: "close",
  assignee: "lucas",
  assigneeIsUser: false,
  reason: "",
  onReasonChange: () => undefined,
  onConfirm: () => undefined,
  onCancel: () => undefined,
  pending: false,
  canConfirm: false,
};

describe("ActionDialog when closing", () => {
  it("asks for the closing reason", () => {
    const html = renderView(<ActionDialog {...props} />);

    expect(html).toContain("Motivo");
    expect(html).toContain('maxLength="500"');
  });

  it("does not confirm without a reason", () => {
    expect(renderView(<ActionDialog {...props} />)).toMatch(
      /<button[^>]*disabled=""[^>]*>(?:(?!<\/button>)[\s\S])*Fechar incidente/,
    );
  });

  it("keeps the typed reason and shows the conflict", () => {
    const html = renderView(
      <ActionDialog
        {...props}
        reason="Pista liberada"
        conflict="Este incidente foi encerrado por roberto."
      />,
    );

    expect(html).toContain("Pista liberada");
    expect(html).toContain("Este incidente foi encerrado por roberto.");
  });

  it("shows why saving failed", () => {
    const html = renderView(<ActionDialog {...props} error="Não foi possível salvar." />);

    expect(html).toContain("Não foi possível salvar.");
  });
});

describe("ActionDialog when sending back to the queue", () => {
  it("asks to confirm and says the assignee stops being responsible", () => {
    const html = renderView(<ActionDialog {...props} action="reopen" canConfirm />);

    expect(html).toContain("Devolver à fila?");
    expect(textOf(html)).toContain("lucas deixa de ser o responsável");
    expect(html).toContain("Aberto");
    expect(html).not.toContain("Motivo");
    expect(html).toMatch(
      /<button[^>]*type="submit"(?![^>]*disabled="")[^>]*>(?:(?!<\/button>)[\s\S])*Devolver à fila/,
    );
  });

  it("talks to the user when they are the assignee", () => {
    const html = renderView(
      <ActionDialog {...props} action="reopen" assignee="camila" assigneeIsUser canConfirm />,
    );

    expect(textOf(html)).toContain("você deixa de ser o responsável");
  });
});
