import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router";

import { homePathFor, login, meQueryOptions } from "../../app/session";
import { DEMO_PASSWORD } from "./demo-users";
import { LoginView } from "./LoginView";

export function LoginPage() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const location = useLocation();
  const expired = (location.state as { expired?: boolean } | null)?.expired === true;
  const [credentials, setCredentials] = useState({ username: "", password: "" });

  // The previous session's screens are gone by now, so its data can go too, before anyone logs in.
  useEffect(() => {
    queryClient.clear();
  }, [queryClient]);

  const mutation = useMutation({
    mutationFn: login,
    onSuccess: (user) => {
      queryClient.setQueryData(meQueryOptions.queryKey, user);
      void navigate(homePathFor(user.role), { replace: true });
    },
  });

  return (
    <LoginView
      username={credentials.username}
      password={credentials.password}
      onChange={(field, value) => {
        setCredentials((current) => ({ ...current, [field]: value }));
      }}
      onSubmit={() => {
        mutation.mutate(credentials);
      }}
      onPickDemo={(username) => {
        setCredentials({ username, password: DEMO_PASSWORD });
      }}
      pending={mutation.isPending}
      errorMessage={mutation.error?.message}
      // Once the user tries again, the old notice no longer helps.
      expired={expired && mutation.isIdle}
    />
  );
}
