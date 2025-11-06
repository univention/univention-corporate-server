# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2023-2024 Univention GmbH

ARG DOCKER_PROXY
FROM ${DOCKER_PROXY}library/nginx:1.23.3

COPY nginx.conf /etc/nginx/nginx.conf
COPY default.conf.template /etc/nginx/templates/

COPY ssl /etc/nginx/ssl/

# create self-signed certificate if no certificates are present
WORKDIR /etc/nginx
# hadolint ignore=SC2288
RUN \[ ! -f ssl/private.key -o ! -f ssl/cert.pem \] && \
    openssl genrsa -des3 -passout pass:x -out ssl/server.pass.key && \
    openssl rsa -passin pass:x -in ssl/server.pass.key -out ssl/private.key && \
    rm ssl/server.pass.key && \
    openssl req -new -key ssl/private.key -out ssl/server.csr \
        -subj "/C=DE/O=Univention/CN=localhost" && \
    openssl x509 -req -days 365 -in ssl/server.csr -signkey ssl/private.key -out ssl/cert.pem && \
    rm ssl/server.csr
