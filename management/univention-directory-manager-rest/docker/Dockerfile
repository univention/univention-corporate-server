ARG UCS_BASE_IMAGE=gitregistry.knut.univention.de/univention/dev/projects/ucs-base-image/ucs-base-python
ARG UCS_BASE_IMAGE_TAG=5.2.5-build.20260326@sha256:163d393824d089e4d33b97378819e319627dea6e183d33200ac54ac1211614f0

FROM ${UCS_BASE_IMAGE}:${UCS_BASE_IMAGE_TAG} AS build

RUN apt-get --yes --no-install-recommends install \
    build-essential python3-dev \
    libldap2-dev libsasl2-dev

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /usr/local/bin/uv

# C build deps for native extensions in internal packages
# (libcrack2-dev: cracklib; libunivention-debug-dev: univention-debug-python;
#  libunivention-license-dev: univention-licence-python; heimdal-dev:
#  univention-python-heimdal; swig + libssl-dev: M2Crypto)
RUN apt-get --yes --no-install-recommends install \
    libcrack2-dev \
    libunivention-debug-dev \
    libunivention-license-dev \
    swig \
    libssl-dev \
    heimdal-dev \
    pkg-config

COPY . .

RUN uv sync --project /app/docker \
    --package univention-directory-manager-rest \
    --frozen \
    --no-dev \
    --no-editable

FROM ${UCS_BASE_IMAGE}:${UCS_BASE_IMAGE_TAG}

COPY --from=build /app/docker/.venv /app/docker/.venv
COPY management/univention-directory-manager-rest/docker/base.conf /etc/univention/base.conf

RUN mkdir -p /etc/univention && \
    apt-get --yes --no-install-recommends install \
        libhdb9-heimdal \
        libsasl2-2 \
        libsasl2-modules-oauthbearer \
        libcrack2 \
        libmagic1 \
        libunivention-config0 \
        libunivention-debug1 \
        libunivention-license0 \
        libunivention-policy0 && \
    apt-get --yes --no-install-recommends install locales && \
    printf 'en_US.UTF-8 UTF-8\nde_DE.UTF-8 UTF-8\n' >> /etc/locale.gen && \
    localedef -i de_DE -c -f UTF-8 -A /usr/share/locale/locale.alias de_DE.UTF-8 && \
    localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8 && \
    mkdir -p \
        /etc/univention/ssl/ucsCA \
        /etc/univention/directory/reports \
        /var/cache/univention-config \
        /var/log/univention \
        /var/lib/univention-appcenter/attributes && \
    echo '{}' > /var/lib/univention-appcenter/attributes/mapping.json

# Pre-rendered reports config (univention-directory-reports.Config() expects
# /etc/univention/directory/reports/config.ini with a [reports] section).
COPY management/univention-directory-manager-rest/docker/reports-config.ini /etc/univention/directory/reports/config.ini

COPY management/univention-directory-manager-rest/docker/entrypoint.d /entrypoint.d/

CMD [ \
    "/app/docker/.venv/bin/python3", \
    "-m", "univention.admin.rest.server", \
    "--debug", "2", \
    "--port", "9979", \
    "--interface", "0.0.0.0", \
    "--processes", "1" \
    ]
