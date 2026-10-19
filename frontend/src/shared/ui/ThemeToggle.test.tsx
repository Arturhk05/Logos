import { describe, expect, it } from "vitest";

import { renderView } from "../../test/render";
import { ThemeToggle } from "./ThemeToggle";

describe("ThemeToggle", () => {
  it.each([
    ["light", "Tema claro. Mudar para o escuro"],
    ["dark", "Tema escuro. Mudar para o claro"],
  ] as const)("says the current theme %s and the other one", (theme, label) => {
    const html = renderView(<ThemeToggle theme={theme} onChange={() => undefined} />);

    expect(html).toContain(`aria-label="${label}"`);
    expect(html).toContain("<svg");
  });

  it("is big enough to tap on a phone", () => {
    const html = renderView(<ThemeToggle theme="light" onChange={() => undefined} />);

    expect(html).toMatch(/<button[^>]*class="[^"]*size-11/);
  });
});
