import { useEffect } from "react";
import { ReactKeycloakProvider } from "@react-keycloak/web";
import { keycloak } from "react-libs";
import RoutesAndLayout from "./layout/RoutesAndLayout";
import { observer } from "mobx-react-lite";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

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
