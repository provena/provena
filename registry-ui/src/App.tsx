import { ReactKeycloakProvider } from "@react-keycloak/web";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { observer } from "mobx-react-lite";
import { keycloak } from "react-libs";
import RoutesAndLayout from "./layout/RoutesAndLayout";

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: false,
    },
  },
});

function App() {
  return (
    <div>
      <QueryClientProvider client={queryClient}>
        <ReactKeycloakProvider authClient={keycloak}>
          <RoutesAndLayout />
        </ReactKeycloakProvider>
      </QueryClientProvider>
    </div>
  );
}

export default observer(App);
