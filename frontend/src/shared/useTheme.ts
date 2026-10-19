import { useEffect, useState } from "react";

import { readTheme, saveTheme, type Theme } from "./theme";

function storage(): Storage | undefined {
  try {
    return window.localStorage;
  } catch {
    return undefined;
  }
}

/** The theme, saved in the browser and applied to <html>. */
export function useTheme(): [Theme, (theme: Theme) => void] {
  const [theme, setTheme] = useState(() => readTheme(storage()));

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  return [
    theme,
    (next) => {
      saveTheme(storage(), next);
      setTheme(next);
    },
  ];
}
