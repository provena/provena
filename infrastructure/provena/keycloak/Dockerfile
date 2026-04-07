FROM quay.io/keycloak/keycloak:16.0.0

# Keycloak's docker-entrypoint.sh builds BIND_OPTS from `hostname --all-ip-addresses`,
# repeating -Djboss.bind.address and -Djboss.bind.address.private for each IP (last wins).
# On some Fargate/CNI setups that makes WildFly's inet-address for "private" ambiguous
# or inconsistent (WFLYSRV0082). Loopback by NIC name is always a single match.
RUN sed -i 's|<inet-address value="${jboss.bind.address.private:127.0.0.1}"/>|<nic name="lo"/>|' \
    /opt/jboss/keycloak/standalone/configuration/standalone-ha.xml

ARG KC_THEME_NAME

# Include the modules in the plugin folder
COPY ./modules/* /opt/jboss/keycloak/providers/

# Include our custom theme - this is configurable by the deployer
COPY ./themes/${KC_THEME_NAME} /opt/jboss/keycloak/themes/${KC_THEME_NAME}