# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2023-2024 Univention GmbH

ARG UCS_BASE_IMAGE=gitregistry.knut.univention.de/univention/components/ucs-base-image/ucs-base-520
ARG UCS_BASE_IMAGE_TAG=0.16.1-build-2025-02-20

FROM ${UCS_BASE_IMAGE}:${UCS_BASE_IMAGE_TAG} AS build-base

RUN apt-get --assume-yes --verbose-versions --no-install-recommends install \
    gcc \
    libsasl2-dev \
    python3 \
    python3-pip \
    python3-setuptools \
    python3-dev \
    libldap2-dev \
    python3-univention-directory-manager-rest-client \
  && rm /usr/lib/python*/EXTERNALLY-MANAGED

WORKDIR /app/
COPY ./requirements.txt .
RUN pip3 install --ignore-installed --no-cache-dir -r requirements.txt

# TODO: The debian packaging files are included by setup.py and copied due to
# this reason. This will have to be adapted once the former debian packaging will
# be removed.
COPY ./debian/changelog ./debian/changelog
COPY ./debian/control ./debian/control
COPY ./python ./python
COPY ./portal_consumer ./portal_consumer
COPY ./setup.py .
COPY ./univention-portal-server .
COPY ./univention-portal .


FROM build-base AS build

RUN pip3 install --no-cache-dir .


FROM build-base AS local-dev-env
WORKDIR /app/

# hadolint ignore=DL3008
RUN apt-get --assume-yes --verbose-versions --no-install-recommends install \
    jq \
    python3-univention-directory-manager \
    univention-group-membership-cache \
    python3-boto3

COPY ./requirements-test.txt .
RUN pip3 install --no-cache-dir --upgrade pip==24.* \
    && pip3 install --no-cache-dir -r requirements-test.txt \
    && mkdir -p /var/log/univention/ \
    && touch /var/log/univention/portal.log \
    && mkdir -p /usr/share/univention-portal \
    && mkdir -p /usr/lib/univention-portal/config

RUN pip3 install --no-cache-dir --editable .

COPY ./docker/portal-server/stub_portals.json /usr/share/univention-portal/portals.json
COPY ./docker/portal-server/docker-entrypoint.sh /entrypoint.d/50-entrypoint.sh

# The GroupsContentFetcher is using "univention.ldap_cache" which depends
# on a user "listener" to be present.
#
# See: https://git.knut.univention.de/univention/ucs/-/blob/aac7cba2ef9e0dc93a46d388673aebff78818b6c/base/univention-group-membership-cache/src/univention/ldap_cache/cache/backend/gdbm_cache.py#L65
RUN useradd -m "listener"

CMD ["bash"]


# Define the command for the local-dev-env run in Tilt.
#
# Currently it is not possible to inject this from the Tilt configuration.
# See https://github.com/tilt-dev/tilt-extensions/issues/391#issuecomment-1687045699
FROM local-dev-env as dev-server

ENV PORTAL_SERVER_DEVELOPMENT_MODE="true"
ENV LOG_LEVEL="DEBUG"
CMD ["./univention-portal-server"]


# Define the command for the local-dev-env run in Tilt.
#
# Currently it is not possible to inject this from the Tilt configuration.
# See https://github.com/tilt-dev/tilt-extensions/issues/391#issuecomment-1687045699
FROM local-dev-env as test

CMD ["pytest", "unittests"]


FROM build-base AS final

RUN apt-get --assume-yes --verbose-versions --no-install-recommends install \
      jq \
      python3 \
      # libldap2-dev is required to make python-ldap work.
      # Currently this is used in the portal server to parse the DNs via "str2dn".
      libldap2-dev \
      python3-univention-directory-manager-rest-client \
      python3-boto3 \
    && useradd -m -d /app app
WORKDIR /app/

RUN mkdir -p /var/log/univention/ \
    && touch /var/log/univention/portal.log \
    && mkdir -p /usr/share/univention-portal \
    && mkdir -p /usr/lib/univention-portal/config

COPY ./univention-portal-server /usr/sbin/univention-portal-server
COPY ./univention-portal .
COPY --from=build /app/requirements.txt .
COPY --from=build /usr/local/lib/python3.11 /usr/local/lib/python3.11

# Considered to be part of the application.
#
# Users MAY provide a different file from the outside if the portal server
# components shall be configured in a different way. This is not an intended
# usage of the container though.
COPY ./docker/portal-server/stub_portals.json /usr/share/univention-portal/portals.json

COPY ./docker/portal-server/docker-entrypoint.sh /entrypoint.d/50-entrypoint.sh

EXPOSE 80

CMD ["/usr/bin/python3", "/usr/sbin/univention-portal-server"]

# [EOF]
