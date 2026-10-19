import { useTheme } from "../useTheme";
import { ThemeToggle } from "./ThemeToggle";

/** The theme toggle wired to the saved choice. */
export function ThemeSwitch() {
  const [theme, setTheme] = useTheme();
  return <ThemeToggle theme={theme} onChange={setTheme} />;
}
