import { QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router/dom";
import "@fontsource-variable/inter";

import { setUnauthorizedHandler } from "./api/client";
import { queryClient } from "./api/query-client";
import { router } from "./app/router";
import { handleUnauthorized } from "./app/session";
import "./index.css";

setUnauthorizedHandler(() => {
  handleUnauthorized(
    queryClient,
    (to, options) => {
      void router.navigate(to, options);
    },
    router.state.location.pathname,
  );
});

const root = document.getElementById("root");
if (root === null) throw new Error("Missing #root element in index.html");

createRoot(root).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </StrictMode>,
);
