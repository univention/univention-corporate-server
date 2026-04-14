ARG UCS_BASE_IMAGE=gitregistry.knut.univention.de/univention/dev/projects/ucs-base-image/ucs-base-python
ARG UCS_BASE_IMAGE_TAG=5.2.5-build.20260326@sha256:163d393824d089e4d33b97378819e319627dea6e183d33200ac54ac1211614f0
############################################################
# Stage 0 - build sssd installer

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

# direct pypi deps for udm-rest
RUN pip3 install --no-cache-dir \
    tornado \
    Genshi \
    pycurl \
    defusedxml \
    jinja2 \
    python-mimeparse \
    setproctitle \
    uritemplate \
    python-ldap \
    requests

COPY base/univention-lib base/univention-lib
RUN pip3 install --no-cache-dir base/univention-lib

COPY management/univention-authorization management/univention-authorization
RUN pip3 install --no-cache-dir management/univention-authorization

# udm
RUN apt-get --yes --no-install-recommends install libcrack2-dev libunivention-debug-dev libunivention-license-dev swig libssl-dev heimdal-dev pkg-config
RUN pip3 install --no-cache-dir \
    lark \
    email-validator \
    dnspython \
    passlib \
    cracklib \
    unidecode \
    python-dateutil \
    pillow \
    python-magic \
    python-debian \
    logfmter \
    trml2pdf \
    M2Crypto \
    bcrypt \
    pkgconfig

COPY base/univention-debug-python base/univention-debug-python
RUN pip3 install --no-cache-dir base/univention-debug-python

COPY base/univention-python base/univention-python
RUN pip3 install --no-cache-dir base/univention-python

COPY base/univention-licence-python base/univention-licence-python
RUN pip3 install --no-cache-dir base/univention-licence-python

COPY base/univention-python-heimdal base/univention-python-heimdal
RUN pip3 install --no-cache-dir base/univention-python-heimdal

COPY services/univention-admin-diary services/univention-admin-diary
RUN pip3 install --no-cache-dir services/univention-admin-diary

COPY management/univention-directory-manager-modules management/univention-directory-manager-modules
RUN pip3 install --no-cache-dir management/univention-directory-manager-modules

COPY base/univention-config-registry base/univention-config-registry
RUN pip3 install --no-cache-dir base/univention-config-registry

COPY packaging/univention-debhelper packaging/univention-debhelper
RUN pip3 install --no-cache-dir packaging/univention-debhelper

COPY management/univention-management-console management/univention-management-console
RUN pip3 install --no-cache-dir management/univention-management-console

COPY management/univention-management-console-module-udm management/univention-management-console-module-udm
RUN pip3 install --no-cache-dir management/univention-management-console-module-udm

COPY management/univention-directory-reports management/univention-directory-reports
RUN pip3 install --no-cache-dir management/univention-directory-reports

COPY management/univention-directory-manager-rest management/univention-directory-manager-rest
RUN pip3 install --no-cache-dir management/univention-directory-manager-rest

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
