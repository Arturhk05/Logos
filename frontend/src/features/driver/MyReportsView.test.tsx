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
