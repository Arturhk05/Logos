import { describe, expect, it } from "vitest";

import { renderView } from "../test/render";
import { AppError } from "./AppError";

describe("AppError", () => {
  it("apologizes in Portuguese and offers a way back, without technical details", () => {
    const html = renderView(<AppError />);

    expect(html).toContain("Ocorreu um erro inesperado.");
    expect(html).toContain('href="/"');
    expect(html).not.toMatch(/Unexpected|Error|stack/i);
  });
});
