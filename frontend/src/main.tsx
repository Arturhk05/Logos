import { QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter } from "react-router";
import { RouterProvider } from "react-router/dom";

import { queryClient } from "./api/query-client";
import "./index.css";

// Placeholder route until the login and the role screens exist.
const router = createBrowserRouter([
  {
    path: "/",
    element: (
      <main className="p-6">
        <h1 className="text-2xl font-semibold">Logos</h1>
      </main>
    ),
  },
]);

const root = document.getElementById("root");
if (root === null) throw new Error("Missing #root element in index.html");

createRoot(root).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </StrictMode>,
);
