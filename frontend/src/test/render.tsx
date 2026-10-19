import type { ReactElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router";

/** Render a view to HTML, with a router so links work. Tests run without a DOM (see vite.config.ts). */
export function renderView(element: ReactElement): string {
  return renderToStaticMarkup(<MemoryRouter>{element}</MemoryRouter>);
}
