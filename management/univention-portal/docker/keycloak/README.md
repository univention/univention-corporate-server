# Keycloak runner

This image extends the upstream keycloak image so that it easily runs locally in
the docker compose based development setup.

On the first start of the container,
default settings for the realm are loaded.
LDAP connection details are grabbed from environment variables.
If the container is stopped and restarted,
the realm is *not* imported again
and custom modifications are preserved.

In order to reset the configuration
remove and recreate the container.

Be aware that it depends on the root CA certificate from your UCS machine to be
extracted first.
