ARG UCS_BASE_IMAGE=gitregistry.knut.univention.de/univention/dev/projects/ucs-base-image/ucs-base-python
ARG UCS_BASE_IMAGE_TAG=5.2.5-build.20260326@sha256:163d393824d089e4d33b97378819e319627dea6e183d33200ac54ac1211614f0

FROM ${UCS_BASE_IMAGE}:${UCS_BASE_IMAGE_TAG}

RUN apt-get --yes --no-install-recommends install python3-venv

RUN apt-get --yes --no-install-recommends install \
    build-essential python3-dev \
    libldap2-dev libsasl2-dev slapd ldap-utils tox \
    lcov valgrind

WORKDIR /app

RUN python3 -m venv --system-site-packages venv

ENV PATH="/app/venv/bin:$PATH"

# python3-apt is Debian-specific and not easily pip-installable
RUN apt-get --yes --no-install-recommends install python3-apt

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

COPY base base
COPY management management
COPY services/univention-admin-diary services/univention-admin-diary
COPY packaging packaging

# Single install — pip resolves the whole graph from pyproject.toml.
RUN pip3 install --no-cache-dir ./management/univention-directory-manager-rest

# Minimal UCR config so modules that read UCR at import time don't crash.
RUN mkdir -p /etc/univention
COPY management/univention-directory-manager-rest/docker/base.conf /etc/univention/base.conf

# Generate locales (the server calls locale.setlocale with whatever UCR says)
RUN apt-get --yes --no-install-recommends install locales && \
    printf 'en_US.UTF-8 UTF-8\nde_DE.UTF-8 UTF-8\n' >> /etc/locale.gen && \
    localedef -i de_DE -c -f UTF-8 -A /usr/share/locale/locale.alias de_DE.UTF-8 && \
    localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8

# Runtime directories expected by univention.lib / UMC code paths and the
# entrypoint scripts that wire up LDAP.
RUN mkdir -p \
        /etc/univention/ssl/ucsCA \
        /etc/univention/directory/reports \
        /var/cache/univention-config \
        /var/log/univention \
        /var/lib/univention-appcenter/attributes && \
    echo '{}' > /var/lib/univention-appcenter/attributes/mapping.json

# Pre-rendered reports config (univention-directory-reports.Config() expects
# /etc/univention/directory/reports/config.ini with a [reports] section).
COPY management/univention-directory-manager-rest/docker/reports-config.ini /etc/univention/directory/reports/config.ini

# Entrypoint: runs /entrypoint.d/* (LDAP wiring) before exec'ing CMD.
COPY management/univention-directory-manager-rest/docker/entrypoint.sh /entrypoint.sh
COPY management/univention-directory-manager-rest/docker/entrypoint.d /entrypoint.d/
RUN chmod +x /entrypoint.sh /entrypoint.d/*

ENTRYPOINT ["/entrypoint.sh"]

CMD [ \
  "venv/bin/python3", \
  "-m", "univention.admin.rest.server", \
  "--debug", "2", \
  "--port", "9979", \
  "--interface", "0.0.0.0", \
  "--processes", "1" \
  ]
