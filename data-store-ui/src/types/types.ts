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
export interface LinkType {
    link: string;
    label: string;
}

export interface DatedCredentials {
    aws_access_key_id: string;
    aws_secret_access_key: string;
    aws_session_token: string;
    expiry: Date;
}
