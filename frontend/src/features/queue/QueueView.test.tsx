import { describe, expect, it } from "vitest";

import { renderView } from "../../test/render";
import type { QueueItem } from "./api";
import { QueueView, type QueueViewProps } from "./QueueView";

const now = new Date("2026-10-18T10:00:00Z");

const victims: QueueItem = {
  id: 7,
  category: "ACCIDENT_WITH_VICTIMS",
  criticality: "HIGH",
  status: "OPEN",
  location: "BR-116, km 230",
  created_at: "2026-10-18T09:57:00Z",
  assignee: null,
};

const weather: QueueItem = {
  id: 9,
  category: "ADVERSE_WEATHER",
  criticality: "LOW",
  status: "INVESTIGATING",
  location: "BR-277, km 80",
  created_at: "2026-10-18T08:00:00Z",
  assignee: { id: 2, username: "lucas" },
};

const props: QueueViewProps = {
  state: "ready",
  onRetry: () => undefined,
  items: [victims, weather],
  counts: { HIGH: 12, MEDIUM: 41, LOW: 47 },
  filters: { criticality: [], category: [], assignee: null },
  onFiltersChange: () => undefined,
  hrefFor: (id) => `/fila/${String(id)}`,
  now,
  updatedAt: now,
  refreshFailed: false,
  refreshing: false,
  onRefresh: () => undefined,
};

describe("QueueView", () => {
  it("shows the counters, every incident and who is assigned", () => {
    const html = renderView(<QueueView {...props} />);

    for (const text of [
      "Alta",
      "12",
      "41",
      "47",
      "Acidente com Vítimas",
      "BR-116, km 230",
      "3 min",
      "Condição Climática Atípica na Pista",
      "lucas",
      "—",
    ]) {
      expect(html).toContain(text);
    }
  });

  it("links each incident to its detail", () => {
    expect(renderView(<QueueView {...props} />)).toContain('href="/fila/7"');
  });

  it("highlights only high criticality incidents", () => {
    const html = renderView(<QueueView {...props} />);

    expect(html).toMatch(/class="[^"]*bg-critical-soft[^"]*"[^>]*data-criticality="HIGH"/);
    expect(html).not.toMatch(/class="[^"]*bg-critical-soft[^"]*"[^>]*data-criticality="LOW"/);
  });

  it("marks the criticality filters that are on", () => {
    const html = renderView(
      <QueueView {...props} filters={{ criticality: ["HIGH"], category: [], assignee: null }} />,
    );

    expect(html).toMatch(/aria-pressed="true"[^>]*>[\s\S]*?Alta/);
    expect(html).toContain("Limpar filtros");
  });

  it("fills the counters that are on, red only for high criticality", () => {
    const html = renderView(
      <QueueView
        {...props}
        filters={{ criticality: ["HIGH", "LOW"], category: [], assignee: null }}
      />,
    );

    expect(html).toMatch(/aria-pressed="true"[^>]*class="[^"]*bg-critical[^"]*"[^>]*>[\s\S]*?Alta/);
    expect(html).toMatch(/aria-pressed="true"[^>]*class="[^"]*bg-accent[^"]*"[^>]*>[\s\S]*?Baixa/);
    expect(html).toMatch(
      /aria-pressed="false"[^>]*class="[^"]*bg-surface[^"]*"[^>]*>[\s\S]*?Média/,
    );
  });

  it("keeps the column widths fixed, so filtering does not move the columns", () => {
    const html = renderView(<QueueView {...props} />);

    expect(html).toMatch(/<table[^>]*class="[^"]*table-fixed/);
    expect(html.match(/<col[ />]/g)).toHaveLength(6);
  });

  it("lets the analyst refresh the queue right away", () => {
    // "Atualizado" counts from the real clock, so the last update is now.
    const html = renderView(<QueueView {...props} updatedAt={new Date()} />);

    expect(html).toMatch(/<button[^>]*>(?:(?!<\/button>)[\s\S])*Atualizado agora/);
  });

  it("keeps the refresh button while new data has no date yet, so the header does not jump", () => {
    const html = renderView(<QueueView {...props} updatedAt={undefined} refreshing />);

    expect(html).toMatch(/<button[^>]*>(?:(?!<\/button>)[\s\S])*Atualizando…/);
  });

  it("shows that the queue is refreshing", () => {
    expect(renderView(<QueueView {...props} refreshing />)).toMatch(
      /<button[^>]*aria-busy="true"[^>]*>(?:(?!<\/button>)[\s\S])*Atualizado/,
    );
  });

  it("renders skeleton rows while loading", () => {
    expect(renderView(<QueueView {...props} state="loading" items={[]} />)).toContain(
      'aria-busy="true"',
    );
  });

  it("renders the error with a retry button", () => {
    const html = renderView(
      <QueueView
        {...props}
        state="error"
        items={[]}
        errorMessage="O sistema está temporariamente indisponível. Tente novamente em instantes."
      />,
    );

    expect(html).toContain(
      "O sistema está temporariamente indisponível. Tente novamente em instantes.",
    );
    expect(html).toContain("Tentar novamente");
  });

  it("explains an empty queue", () => {
    const html = renderView(<QueueView {...props} items={[]} />);

    expect(html).toContain("Nenhum incidente ativo no momento.");
    expect(html).not.toContain("Limpar filtros");
  });

  it("offers to clear the filters when they hide everything", () => {
    const html = renderView(
      <QueueView
        {...props}
        items={[]}
        filters={{ criticality: ["LOW"], category: [], assignee: null }}
      />,
    );

    expect(html).toContain("Nenhum incidente com esses filtros.");
    expect(html).toContain("Limpar filtros");
  });

  it.each([
    [null, "Todos"],
    ["none", "Sem responsável"],
    ["me", "Assumidos por mim"],
  ] as const)("marks only the %s assignee option as chosen", (assignee, chosen) => {
    const html = renderView(
      <QueueView {...props} filters={{ criticality: [], category: [], assignee }} />,
    );

    // Within a single button, so the pressed state of another filter cannot match.
    const option = (label: string, pressed: boolean) =>
      new RegExp(`<button[^>]*aria-pressed="${String(pressed)}"[^>]*>(?:(?!</button>).)*${label}`);
    for (const label of ["Todos", "Sem responsável", "Assumidos por mim"]) {
      expect(html).toMatch(option(label, label === chosen));
    }
  });

  it("offers to clear the filters when nothing is assigned to me", () => {
    const html = renderView(
      <QueueView
        {...props}
        items={[]}
        filters={{ criticality: [], category: [], assignee: "me" }}
      />,
    );

    expect(html).toContain("Nenhum incidente com esses filtros.");
    expect(html).toContain("Limpar filtros");
  });

  it("tells when the last refresh failed but keeps the incidents", () => {
    const html = renderView(<QueueView {...props} refreshFailed />);

    expect(html).toContain("Não foi possível atualizar");
    expect(html).toContain("BR-116, km 230");
  });
});
