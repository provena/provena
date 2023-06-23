FROM quay.io/keycloak/keycloak:16.0.0

ARG KC_THEME_NAME

# Include the modules in the plugin folder
COPY ./modules/* /opt/jboss/keycloak/providers/

# Include our custom theme - this is configurable by the deployer
COPY ./themes/${KC_THEME_NAME} /opt/jboss/keycloak/themes/${KC_THEME_NAME}