import { createBrowserRouter } from "react-router";

import { LoginPage } from "../features/auth/LoginPage";
import { QueuePage } from "../features/queue/QueuePage";
import { CentralLayout } from "./CentralLayout";
import { DriverLayout } from "./DriverLayout";
import { Placeholder } from "./Placeholder";
import { HomeRedirect, RequireRole } from "./RequireRole";
import { SessionGate } from "./SessionGate";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    element: <SessionGate />,
    children: [
      {
        element: <RequireRole area="central" />,
        children: [
          {
            element: <CentralLayout />,
            children: [
              { path: "/fila/:incidentId?", element: <QueuePage /> },
              { path: "/historico/:incidentId?", element: <Placeholder title="Histórico" /> },
            ],
          },
        ],
      },
      {
        element: <RequireRole area="driver" />,
        children: [
          {
            element: <DriverLayout />,
            children: [
              { path: "/reportar", element: <Placeholder title="Reportar incidente" /> },
              { path: "/meus-reportes", element: <Placeholder title="Meus reportes" /> },
            ],
          },
        ],
      },
      // "/" and unknown paths go to the user's home.
      { path: "*", element: <HomeRedirect /> },
    ],
  },
]);
