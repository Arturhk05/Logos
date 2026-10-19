import { describe, expect, it } from "vitest";

import type { QueueItem } from "../queue/api";
import { renderView } from "../../test/render";
import { MyReportsView, type MyReportsViewProps } from "./MyReportsView";

const now = new Date("2026-10-18T10:00:00Z");

const mechanical: QueueItem = {
  id: 142,
  category: "MECHANICAL_PROBLEM",
  criticality: "MEDIUM",
  status: "INVESTIGATING",
  location: "SP-330, km 12",
  created_at: "2026-10-18T07:40:00Z",
  assignee: { id: 1, username: "camila" },
};

const props: MyReportsViewProps = {
  state: "ready",
  onRetry: () => undefined,
  items: [mechanical],
  now,
};

describe("MyReportsView", () => {
  it("lists each report with its number, place, date and status", () => {
    const html = renderView(<MyReportsView {...props} />);

    for (const text of ["#142", "Problema Mecânico", "SP-330, km 12", "18/10", "Em Investigação"]) {
      expect(html).toContain(text);
    }
  });

  it("tells in plain words where each report in progress stands", () => {
    const waiting: QueueItem = { ...mechanical, id: 150, status: "OPEN", assignee: null };
    const html = renderView(<MyReportsView {...props} items={[waiting, mechanical]} />);

    expect(html).toContain("Em andamento");
    expect(html).toContain("Aguardando a central");
    expect(html).toContain("Seu reporte chegou");
    expect(html).toContain("A central está cuidando");
    expect(html).toContain("WhatsApp");
    expect(html).not.toContain("Encerrados");
  });

  it("keeps closed reports apart, after the ones in progress", () => {
    const closed: QueueItem = { ...mechanical, id: 120, status: "CLOSED" };
    const inconclusive: QueueItem = { ...mechanical, id: 110, status: "INCONCLUSIVE" };
    const html = renderView(
      <MyReportsView {...props} items={[closed, mechanical, inconclusive]} />,
    );

    const order = ["Em andamento", "#142", "Encerrados", "#120", "#110"].map((text) =>
      html.indexOf(text),
    );
    expect(order).toEqual([...order].sort((a, b) => a - b));
    expect(order).not.toContain(-1);
  });

  it("says nothing is in progress when every report is closed", () => {
    const closed: QueueItem = { ...mechanical, status: "CLOSED" };
    const html = renderView(<MyReportsView {...props} items={[closed]} />);

    expect(html).toContain("Nenhum reporte em andamento.");
    expect(html).toContain("Encerrados");
  });

  it("offers to report when there is nothing yet", () => {
    const html = renderView(<MyReportsView {...props} items={[]} />);

    expect(html).toContain("Você ainda não reportou nenhum incidente.");
    expect(html).toContain('href="/reportar"');
  });

  it("renders the error with a retry button", () => {
    const html = renderView(
      <MyReportsView {...props} state="error" items={[]} errorMessage="Sem conexão." />,
    );

    expect(html).toContain("Sem conexão.");
    expect(html).toContain("Tentar novamente");
  });

  it("renders a skeleton while loading", () => {
    expect(renderView(<MyReportsView {...props} state="loading" items={[]} />)).toContain(
      'aria-busy="true"',
    );
  });
});
