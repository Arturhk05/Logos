import { describe, expect, it } from "vitest";

import type { IncidentDetail } from "../../api/client";
import { renderView } from "../../test/render";
import { IncidentDrawerView, type IncidentDrawerViewProps } from "./IncidentDrawerView";

const now = new Date("2026-10-18T10:00:00Z");

const active: IncidentDetail = {
  id: 7,
  version: 3,
  category: "ACCIDENT_WITH_VICTIMS",
  criticality: "HIGH",
  status: "OPEN",
  location: "BR-116, km 230",
  description: "Colisão traseira com duas pessoas feridas.",
  reporter: { id: 9, username: "jose" },
  assignee: null,
  closed_by: null,
  closed_at: null,
  closure_reason: null,
  created_at: "2026-10-18T07:02:00Z",
  updated_at: "2026-10-18T07:05:00Z",
  events: [],
};

const closed: IncidentDetail = {
  ...active,
  status: "CLOSED",
  assignee: { id: 2, username: "lucas" },
  closed_by: { id: 3, username: "roberto" },
  closed_at: "2026-10-18T09:30:00Z",
  closure_reason: "Pista liberada",
};

const props: IncidentDrawerViewProps = {
  state: "ready",
  incident: active,
  actions: ["assume"],
  onAction: () => undefined,
  onRetrySave: () => undefined,
  now,
};

describe("IncidentDrawerView", () => {
  it("shows every detail of an active incident", () => {
    const html = renderView(<IncidentDrawerView {...props} />);

    for (const text of [
      "Acidente com Vítimas",
      "Alta",
      "Aberto",
      "BR-116, km 230",
      "Colisão traseira com duas pessoas feridas.",
      "jose",
      "Responsável",
      "Atualizado em",
    ]) {
      expect(html).toContain(text);
    }
  });

  it("shows who closed, when and why", () => {
    const html = renderView(<IncidentDrawerView {...props} incident={closed} actions={[]} />);

    expect(html).toContain("Encerrado por");
    expect(html).toContain("roberto");
    expect(html).toContain("Pista liberada");
  });

  it("offers only the available actions", () => {
    const html = renderView(<IncidentDrawerView {...props} />);

    expect(html).toContain("Assumir incidente");
    expect(html).not.toContain("Devolver à fila");
  });

  it("offers closing, inconclusive and back to the queue to whoever may change it", () => {
    const html = renderView(
      <IncidentDrawerView {...props} actions={["close", "inconclusive", "reopen"]} />,
    );

    expect(html).toContain("Fechar");
    expect(html).toContain("Inconclusivo");
    expect(html).toContain("Devolver à fila");
    expect(html).not.toContain("Assumir incidente");
  });

  it("shows no action buttons when none is available", () => {
    const html = renderView(<IncidentDrawerView {...props} actions={[]} />);

    expect(html).not.toContain("Assumir incidente");
    expect(html).not.toContain("Fechar");
  });

  it("disables the actions while one is being saved", () => {
    const html = renderView(<IncidentDrawerView {...props} pendingAction="assume" />);

    expect(html).toMatch(/<button[^>]*disabled=""[^>]*>(?:(?!<\/button>)[\s\S])*Assumir incidente/);
  });

  it("shows the conflict above the current state", () => {
    const html = renderView(
      <IncidentDrawerView {...props} conflict="lucas assumiu este incidente antes de você." />,
    );

    expect(html).toContain("lucas assumiu este incidente antes de você.");
    expect(html).toContain("Veja abaixo como ele está agora.");
    expect(html).not.toContain("versão");
  });

  it("offers a retry when saving failed", () => {
    const html = renderView(<IncidentDrawerView {...props} saveError="Não foi possível salvar." />);

    expect(html).toContain("Não foi possível salvar.");
    expect(html).toContain("Tentar novamente");
  });

  it("renders the error state with the API message", () => {
    const html = renderView(
      <IncidentDrawerView
        {...props}
        state="error"
        incident={undefined}
        errorMessage="Incidente não encontrado."
      />,
    );

    expect(html).toContain("Incidente não encontrado.");
  });

  it("shows a skeleton while loading", () => {
    expect(
      renderView(<IncidentDrawerView {...props} state="loading" incident={undefined} />),
    ).toContain('aria-busy="true"');
  });

  it("shows the timeline, oldest first, with who, when and why", () => {
    const incident: IncidentDetail = {
      ...active,
      events: [
        {
          actor: { id: 9, username: "jose" },
          from_status: null,
          to_status: "OPEN",
          reason: null,
          created_at: "2026-10-18T07:02:00Z",
        },
        {
          actor: { id: 1, username: "camila" },
          from_status: "OPEN",
          to_status: "INVESTIGATING",
          reason: null,
          created_at: "2026-10-18T07:10:00Z",
        },
        {
          actor: { id: 3, username: "roberto" },
          from_status: "INVESTIGATING",
          to_status: "OPEN",
          reason: "Analista saiu do turno",
          created_at: "2026-10-18T08:00:00Z",
        },
        {
          actor: { id: 2, username: "lucas" },
          from_status: "OPEN",
          to_status: "INVESTIGATING",
          reason: null,
          created_at: "2026-10-18T08:05:00Z",
        },
      ],
    };

    const text = renderView(<IncidentDrawerView {...props} incident={incident} />).replace(
      /<[^>]+>/g,
      " ",
    );

    expect(text).toContain("Linha do tempo");
    const order = [
      "Reportado",
      "jose",
      "Assumido",
      "camila",
      "Devolvido à fila",
      "roberto",
      "Analista saiu do turno",
      "Assumido",
      "lucas",
    ];
    let from = 0;
    for (const piece of order) {
      const at = text.indexOf(piece, from);
      expect(at, piece).toBeGreaterThanOrEqual(0);
      from = at + piece.length;
    }
  });

  it("shows no reason line for a change without one", () => {
    const incident: IncidentDetail = {
      ...active,
      events: [
        {
          actor: { id: 9, username: "jose" },
          from_status: null,
          to_status: "OPEN",
          reason: null,
          created_at: "2026-10-18T07:02:00Z",
        },
      ],
    };

    const html = renderView(<IncidentDrawerView {...props} incident={incident} />);

    expect(html).toContain("Reportado");
    expect(html).not.toContain("&quot;");
    expect(html).not.toContain("“");
  });
});
