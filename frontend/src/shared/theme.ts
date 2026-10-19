export type Theme = "light" | "dark";

// Also read by the inline script in index.html, which applies the theme before the app loads.
export const THEME_STORAGE_KEY = "logos-theme";

type Storage = Pick<globalThis.Storage, "getItem" | "setItem">;

/** The saved theme, or light; the browser may block storage (private mode, policies). */
export function readTheme(storage: Storage | undefined): Theme {
  try {
    return storage?.getItem(THEME_STORAGE_KEY) === "dark" ? "dark" : "light";
  } catch {
    return "light";
  }
}

export function saveTheme(storage: Storage | undefined, theme: Theme): void {
  try {
    storage?.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    // Not saving only means the choice lasts until the page is reloaded.
  }
}

export function nextTheme(theme: Theme): Theme {
  return theme === "light" ? "dark" : "light";
}
