import Keycloak from "keycloak-js";
import { KEYCLOAK_AUTH_ENDPOINT } from "../queries/endpoints";
import { KEYCLOAK_CLIENT_ID, KEYCLOAK_REALM } from "../config";

// Setup Keycloak instance as needed
// Pass initialization options as required or leave blank to load from 'keycloak.json'

const keycloakConfig = {
    realm: KEYCLOAK_REALM,
    url: KEYCLOAK_AUTH_ENDPOINT,
    clientId: KEYCLOAK_CLIENT_ID,
};

export const keycloak = new Keycloak(keycloakConfig);
