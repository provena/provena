export const hdlPrefix = "https://hdl.handle.net/";
export const THEME_ID = import.meta.env.VITE_THEME_ID;
export const KEYCLOAK_CLIENT_ID = import.meta.env.VITE_KEYCLOAK_CLIENT_ID;
export const KEYCLOAK_REALM = import.meta.env.VITE_KEYCLOAK_REALM;

/**
===========
Enforcement
===========
*/

const required: Array<[string | undefined, string]> = [
    [THEME_ID, "Theme ID"],
    [KEYCLOAK_CLIENT_ID, "Keycloak Client ID"],
    [KEYCLOAK_REALM, "Keycloak Realm Name"],
];

required.forEach(([url, desc]) => {
    if (!url) {
        throw new Error(
            `Cannot use shared library functionality without ${desc}.`
        );
    }
});
