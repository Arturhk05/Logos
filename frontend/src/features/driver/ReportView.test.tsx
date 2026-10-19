import { describe, expect, it } from "vitest";

import { renderView } from "../../test/render";
import { EMPTY_DRAFT, type CategoryOption } from "./report";
import { ReportView, type ReportViewProps } from "./ReportView";

const options: CategoryOption[] = [
  {
    category: "ACCIDENT_WITH_VICTIMS",
    label: "Acidente com Vítimas",
    suggested_criticality: "HIGH",
    criticality_locked: true,
  },
  {
    category: "ROAD_BLOCKAGE",
    label: "Bloqueio de Pista",
    suggested_criticality: "MEDIUM",
    criticality_locked: false,
  },
];

const props: ReportViewProps = {
  categoriesState: "ready",
  onRetryCategories: () => undefined,
  options,
  draft: EMPTY_DRAFT,
  errors: {},
  onCategory: () => undefined,
  onCriticality: () => undefined,
  onField: () => undefined,
  onSubmit: () => undefined,
  pending: false,
  onReportAnother: () => undefined,
};

function buttonWith(text: string): RegExp {
  return new RegExp(`<button[^>]*>(?:(?!</button>)[\\s\\S])*${text}`);
}

describe("ReportView", () => {
  it("offers every category with big touch targets", () => {
    const html = renderView(<ReportView {...props} />);

    expect(html).toContain("Acidente com Vítimas");
    expect(html).toContain("Bloqueio de Pista");
    expect(html).toMatch(/<button[^>]*class="[^"]*min-h-11/);
  });

  it("gives every category button the same height, in one column on very narrow phones", () => {
    const html = renderView(<ReportView {...props} />);
    const grid =
      /<div class="([^"]*grid[^"]*)"><button[^>]*aria-pressed/.exec(html)?.[1]?.split(" ") ?? [];

    expect(grid).toContain("auto-rows-fr");
    expect(grid).toContain("grid-cols-1");
    expect(grid).toContain("min-[360px]:grid-cols-2");
  });

  it("marks the chosen category and criticality", () => {
    const html = renderView(
      <ReportView
        {...props}
        draft={{ ...EMPTY_DRAFT, category: "ROAD_BLOCKAGE", criticality: "MEDIUM" }}
      />,
    );

    expect(html).toMatch(/aria-pressed="true"[^>]*>(?:(?!<\/button>)[\s\S])*Bloqueio de Pista/);
    expect(html).toMatch(/aria-pressed="true"[^>]*>(?:(?!<\/button>)[\s\S])*Média/);
  });

  it("locks the criticality for accidents with victims", () => {
    const html = renderView(
      <ReportView
        {...props}
        draft={{ ...EMPTY_DRAFT, category: "ACCIDENT_WITH_VICTIMS", criticality: "HIGH" }}
      />,
    );

    expect(html).toContain("Sempre Alta para acidente com vítimas");
    expect(html).toMatch(/<button[^>]*disabled=""[^>]*>(?:(?!<\/button>)[\s\S])*Média/);
    expect(html).toMatch(/<button[^>]*disabled=""[^>]*>(?:(?!<\/button>)[\s\S])*Baixa/);
  });

  it("shows each field error in red without losing the typed text", () => {
    const html = renderView(
      <ReportView
        {...props}
        draft={{ ...EMPTY_DRAFT, description: "Carreta tombada" }}
        errors={{ location: "Informe o local." }}
      />,
    );

    expect(html).toMatch(
      /class="[^"]*text-critical[^"]*"[^>]*>(?:(?!<\/p>)[\s\S])*Informe o local\./,
    );
    expect(html).toContain("Carreta tombada");
  });

  it("reserves the space of the field errors, so the form does not grow", () => {
    const html = renderView(<ReportView {...props} />);

    expect(html.match(/class="[^"]*min-h-5[^"]*text-critical/g)?.length).toBeGreaterThanOrEqual(3);
  });

  it("keeps the data and offers a retry when sending failed", () => {
    const html = renderView(
      <ReportView
        {...props}
        draft={{ ...EMPTY_DRAFT, location: "BR-101, km 45" }}
        submitError="Sem conexão. Verifique sua internet e tente novamente."
      />,
    );

    expect(html).toContain("Sem conexão. Verifique sua internet e tente novamente.");
    expect(html).toMatch(buttonWith("Tentar novamente"));
    expect(html).toContain("BR-101, km 45");
  });

  it("disables sending while pending", () => {
    expect(renderView(<ReportView {...props} pending />)).toMatch(
      /<button[^>]*type="submit"[^>]*disabled=""/,
    );
  });

  it("confirms the created incident number", () => {
    const html = renderView(
      <ReportView {...props} created={{ id: 142, phone: "5500900000001" }} />,
    );

    expect(html).toContain("Incidente #142 enviado.");
    expect(html).toContain(
      "A central já foi avisada e vai entrar em contato pelo WhatsApp no número terminado em 0001.",
    );
    expect(html).toContain("Ver meus reportes");
    expect(html).toMatch(buttonWith("Reportar outro"));
  });

  it("explains when the categories could not load", () => {
    const html = renderView(
      <ReportView {...props} categoriesState="error" options={[]} categoriesError="Sem conexão." />,
    );

    expect(html).toContain("Sem conexão.");
    expect(html).toMatch(buttonWith("Tentar novamente"));
  });
});
