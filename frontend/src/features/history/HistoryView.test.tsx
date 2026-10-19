import { describe, expect, it } from "vitest";

import { renderView } from "../../test/render";
import type { HistoryItem } from "./api";
import { HistoryView, type HistoryViewProps } from "./HistoryView";

const now = new Date("2026-10-18T10:00:00Z");

const closed: HistoryItem = {
  id: 31,
  category: "ROAD_BLOCKAGE",
  criticality: "HIGH",
  status: "CLOSED",
  location: "BR-101, km 45",
  created_at: "2026-10-17T08:00:00Z",
  closed_at: "2026-10-17T11:30:00Z",
  closed_by: { id: 3, username: "roberto" },
  assignee: { id: 2, username: "lucas" },
};

const props: HistoryViewProps = {
  state: "ready",
  onRetry: () => undefined,
  items: [closed],
  total: 45,
  filters: { status: [], criticality: [], category: [], page: 2 },
  onFiltersChange: () => undefined,
  hrefFor: (id) => `/historico/${String(id)}`,
  now,
};

describe("HistoryView", () => {
  it("lists closed incidents with who closed them and when", () => {
    const html = renderView(<HistoryView {...props} />);

    for (const text of ["Bloqueio de Pista", "BR-101, km 45", "Fechado", "roberto", "17/10"]) {
      expect(html).toContain(text);
    }
    expect(html).toContain('href="/historico/31"');
  });

  it("shows the page out of the total", () => {
    const html = renderView(<HistoryView {...props} />);

    expect(html).toContain("Página 2 de 3");
    expect(html).toContain("45 incidentes encerrados");
  });

  it("disables previous on the first page and next on the last", () => {
    const first = renderView(<HistoryView {...props} filters={{ ...props.filters, page: 1 }} />);
    const last = renderView(<HistoryView {...props} filters={{ ...props.filters, page: 3 }} />);

    expect(first).toMatch(/<button[^>]*disabled=""[^>]*>(?:(?!<\/button>)[\s\S])*Anterior/);
    expect(last).toMatch(/<button[^>]*disabled=""[^>]*>(?:(?!<\/button>)[\s\S])*Próxima/);
  });

  it("marks the status filters that are on", () => {
    const html = renderView(
      <HistoryView {...props} filters={{ ...props.filters, status: ["INCONCLUSIVE"] }} />,
    );

    expect(html).toMatch(/aria-pressed="true"[^>]*>(?:(?!<\/button>)[\s\S])*Inconclusivo/);
    expect(html).toContain("Limpar filtros");
  });

  it("explains when no closed incident matches the filters", () => {
    const html = renderView(
      <HistoryView
        {...props}
        items={[]}
        total={0}
        filters={{ ...props.filters, criticality: ["LOW"], page: 1 }}
      />,
    );

    expect(html).toContain("Nenhum incidente encerrado com esses filtros.");
    expect(html).toContain("Limpar filtros");
    expect(html).not.toContain("Página");
  });

  it("explains an empty history", () => {
    const html = renderView(
      <HistoryView {...props} items={[]} total={0} filters={{ ...props.filters, page: 1 }} />,
    );

    expect(html).toContain("Nenhum incidente encerrado até agora.");
  });

  it("renders the error with a retry button", () => {
    const html = renderView(
      <HistoryView {...props} state="error" items={[]} errorMessage="Sem conexão." />,
    );

    expect(html).toContain("Sem conexão.");
    expect(html).toContain("Tentar novamente");
  });

  it("renders skeleton rows while loading", () => {
    expect(renderView(<HistoryView {...props} state="loading" items={[]} />)).toContain(
      'aria-busy="true"',
    );
  });
});
