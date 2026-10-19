import { CircleAlert, Clock } from "lucide-react";

import { ROLE_LABELS } from "../../shared/labels";
import { Button } from "../../shared/ui/Button";
import { DEMO_PASSWORD, DEMO_USERS } from "./demo-users";

export interface LoginViewProps {
  username: string;
  password: string;
  onChange: (field: "username" | "password", value: string) => void;
  onSubmit: () => void;
  onPickDemo: (username: string) => void;
  pending: boolean;
  errorMessage?: string;
  expired: boolean;
}

const INPUT =
  "min-h-11 w-full rounded-lg border border-line bg-surface px-3 text-ink placeholder:text-muted focus:border-accent focus:outline-none";

export function LoginView({
  username,
  password,
  onChange,
  onSubmit,
  onPickDemo,
  pending,
  errorMessage,
  expired,
}: LoginViewProps) {
  return (
    <main className="flex min-h-dvh items-center justify-center px-4 py-10">
      <div className="w-full max-w-sm">
        <h1 className="text-2xl font-extrabold tracking-tight">Logos</h1>
        <p className="mb-6 text-muted">Central de resposta a incidentes</p>

        {expired && (
          <p className="mb-4 flex items-center gap-2 rounded-lg border border-warning-line bg-warning-soft px-3 py-2 text-sm text-warning-ink">
            <Clock aria-hidden className="size-4 shrink-0" />
            Sua sessão expirou. Entre novamente.
          </p>
        )}

        <form
          className="flex flex-col gap-4 rounded-xl border border-line bg-surface p-5"
          onSubmit={(event) => {
            event.preventDefault();
            onSubmit();
          }}
        >
          <label className="flex flex-col gap-1.5 text-sm font-medium">
            Usuário
            <input
              className={INPUT}
              name="username"
              autoComplete="username"
              required
              value={username}
              onChange={(event) => {
                onChange("username", event.target.value);
              }}
            />
          </label>
          <div className="flex flex-col gap-1.5">
            <label className="flex flex-col gap-1.5 text-sm font-medium">
              Senha
              <input
                className={INPUT}
                name="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(event) => {
                  onChange("password", event.target.value);
                }}
              />
            </label>
            {/* Always rendered with room for one line, so a message never pushes the form down;
                a live region that already exists is also announced more reliably. */}
            <p
              role="alert"
              className="flex min-h-5 items-start gap-2 text-sm leading-5 text-critical-ink"
            >
              {errorMessage !== undefined && (
                <>
                  <CircleAlert aria-hidden className="mt-0.5 size-4 shrink-0" />
                  {errorMessage}
                </>
              )}
            </p>
          </div>

          <Button type="submit" pending={pending} className="min-h-11">
            Entrar
          </Button>
        </form>

        <section className="mt-6 rounded-xl border border-line bg-surface p-4 text-sm">
          <h2 className="font-semibold">Acesso de demonstração</h2>
          <p className="mb-2 text-muted">
            Senha de todos: <span className="font-mono text-ink">{DEMO_PASSWORD}</span>. Clique para
            preencher.
          </p>
          <ul className="flex flex-col">
            {DEMO_USERS.map((user) => (
              <li key={user.username}>
                <button
                  type="button"
                  className="flex min-h-11 w-full items-center justify-between rounded-lg px-2 hover:bg-canvas"
                  onClick={() => {
                    onPickDemo(user.username);
                  }}
                >
                  <span className="font-mono">{user.username}</span>
                  <span className="text-muted">{ROLE_LABELS[user.role]}</span>
                </button>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </main>
  );
}
