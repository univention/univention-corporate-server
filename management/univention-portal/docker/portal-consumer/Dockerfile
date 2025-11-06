# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2023-2024 Univention GmbH

ARG UCS_BASE_IMAGE_TAG=0.16.1-build-2025-02-20
ARG UCS_BASE_IMAGE=gitregistry.knut.univention.de/univention/components/ucs-base-image/ucs-base-520

# in the pipeline, this will be set to whatever the current image tag for portal-server in that pipeline is (e.g. vX.Y.Z)
ARG PORTAL_BASE_IMAGE_TAG=latest
ARG PORTAL_BASE_IMAGE=gitregistry.knut.univention.de/univention/components/univention-portal/portal-server:${PORTAL_BASE_IMAGE_TAG}

# hadolint ignore=DL3006
FROM ${PORTAL_BASE_IMAGE} as portal-server-image

FROM ${UCS_BASE_IMAGE}:${UCS_BASE_IMAGE_TAG} as final

# TODO: Duplicated from the portal-server
RUN apt-get --assume-yes --verbose-versions --no-install-recommends install \
    jq \
    python3 \
    python3-pip \
    python3-boto3 \
    gcc \
    libsasl2-dev \
    python3-dev \
    libldap2-dev \
    univention-config-registry \
    python3-univention-directory-manager-rest-client \
    univention-group-membership-cache

COPY ./docker/portal-consumer/requirements.txt /
RUN pip3 install --break-system-packages --no-cache-dir -r requirements.txt

# TODO: Duplicated from the portal-server
RUN mkdir -p /var/log/univention/ \
    && touch /var/log/univention/portal.log \
    && mkdir -p /usr/share/univention-portal \
    && mkdir -p /usr/share/univention-portal/icons/entries \
    && mkdir -p /usr/lib/univention-portal/config \
    && mkdir -p /var/cache/univention-portal \
    && touch /var/cache/univention-portal/groups.json \
    && touch /var/cache/univention-portal/portal.json \
    && touch /var/cache/univention-portal/selfservice.json

COPY --from=portal-server-image /usr/local/lib/python3.11/dist-packages/univention /usr/local/lib/python3.11/dist-packages/univention
COPY --from=portal-server-image /app/univention-portal /usr/sbin/univention-portal
COPY --from=portal-server-image /entrypoint.d/50-entrypoint.sh /entrypoint.d/25-docker-entrypoint.sh

COPY ./docker/portal-consumer/stub_portals.json /usr/share/univention-portal/portals.json
COPY ./docker/portal-consumer/ldap-setup.envsh /50-ldap-setup.envsh
COPY ./portal_consumer/ /portal_consumer/

# Create listener user for group membership cache
RUN useradd -m -d /app app \
    && useradd -m listener

CMD ["/usr/bin/python3", "-m", "portal_consumer.consumer"]
