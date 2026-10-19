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
  unavailable: false,
};

describe("ActionDialog when closing", () => {
  it("asks for the closing reason", () => {
    const html = renderView(<ActionDialog {...props} />);

    expect(html).toContain("Motivo");
    expect(html).not.toContain("opcional");
    expect(html).toMatch(/<textarea[^>]*required/);
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
    expect(html).toMatch(
      /<button[^>]*type="submit"(?![^>]*disabled="")[^>]*>(?:(?!<\/button>)[\s\S])*Devolver à fila/,
    );
  });

  it("offers an optional reason that does not block confirming", () => {
    const html = renderView(<ActionDialog {...props} action="reopen" canConfirm />);

    expect(html).toContain("Motivo (opcional)");
    expect(html).toMatch(/<textarea(?![^>]*required)[^>]*>/);
    expect(html).toContain('maxLength="500"');
  });

  it("talks to the user when they are the assignee", () => {
    const html = renderView(
      <ActionDialog {...props} action="reopen" assignee="camila" assigneeIsUser canConfirm />,
    );

    expect(textOf(html)).toContain("você deixa de ser o responsável");
  });
});

describe("ActionDialog when the incident changed meanwhile", () => {
  it("says why the action is no longer possible", () => {
    const html = renderView(
      <ActionDialog {...props} reason="Pista liberada" unavailable canConfirm={false} />,
    );

    expect(html).toContain("Este incidente mudou e esta ação não está mais disponível.");
    expect(html).toContain("Pista liberada");
  });

  it("does not leave an empty name when the incident has no assignee anymore", () => {
    const html = renderView(
      <ActionDialog {...props} action="reopen" assignee={undefined} unavailable />,
    );

    expect(html).not.toContain("<strong></strong>");
  });

  it("announces the conflict to screen readers", () => {
    const html = renderView(
      <ActionDialog {...props} conflict="Este incidente foi encerrado por roberto." />,
    );

    expect(html).toMatch(
      /role="alert"[^>]*>(?:(?!<\/p>)[\s\S])*Este incidente foi encerrado por roberto\./,
    );
  });
});
