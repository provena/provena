import Keycloak from "keycloak-js";
export interface UserProfile extends Keycloak.KeycloakTokenParsed {
    scope: string;
    sid: string;
    email_verified: boolean;
    name: string;
    preferred_username: string;
    given_name: string;
    family_name: string;
    email: string;
}