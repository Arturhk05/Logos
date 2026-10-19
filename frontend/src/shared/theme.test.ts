import { describe, expect, it } from "vitest";

import indexHtml from "../../index.html?raw";

import { nextTheme, readTheme, saveTheme, THEME_STORAGE_KEY } from "./theme";

function memoryStorage(initial: Record<string, string> = {}) {
  const values = new Map(Object.entries(initial));
  return {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => {
      values.set(key, value);
    },
    values,
  };
}

const blockedStorage = {
  getItem: (): string | null => {
    throw new Error("SecurityError");
  },
  setItem: (): void => {
    throw new Error("SecurityError");
  },
};

describe("readTheme", () => {
  it("reads the saved theme", () => {
    expect(readTheme(memoryStorage({ [THEME_STORAGE_KEY]: "dark" }))).toBe("dark");
  });

  it("starts light when nothing valid was saved, whatever the system uses", () => {
    expect(readTheme(memoryStorage())).toBe("light");
    expect(readTheme(memoryStorage({ [THEME_STORAGE_KEY]: "system" }))).toBe("light");
  });

  it("starts light when the browser blocks the storage", () => {
    expect(readTheme(blockedStorage)).toBe("light");
  });
});

describe("saveTheme", () => {
  it("saves the theme", () => {
    const storage = memoryStorage();

    saveTheme(storage, "dark");

    expect(storage.values.get(THEME_STORAGE_KEY)).toBe("dark");
  });

  it("does not break when the browser blocks the storage", () => {
    expect(() => {
      saveTheme(blockedStorage, "dark");
    }).not.toThrow();
  });
});

describe("nextTheme", () => {
  it("switches between light and dark", () => {
    expect(nextTheme("light")).toBe("dark");
    expect(nextTheme("dark")).toBe("light");
  });
});

describe("index.html", () => {
  it("applies the saved theme before the app loads, with the same storage key", () => {
    // The inline script avoids a flash of the light theme; it cannot import this module.
    expect(indexHtml).toContain(`"${THEME_STORAGE_KEY}"`);
    expect(indexHtml).toContain("dataset.theme");
    expect(indexHtml).not.toContain("prefers-color-scheme");
  });
});
