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

RUN python3 -m venv venv

ENV PATH="/app/venv/bin:$PATH"

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
RUN apt-get --yes --no-install-recommends install libcrack2-dev libunivention-debug-dev libunivention-license-dev
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
    logfmter

COPY base/univention-debug-python base/univention-debug-python
RUN pip3 install --no-cache-dir base/univention-debug-python

COPY base/univention-python base/univention-python
RUN pip3 install --no-cache-dir base/univention-python

COPY base/univention-licence-python base/univention-licence-python
RUN pip3 install --no-cache-dir base/univention-licence-python

COPY services/univention-admin-diary services/univention-admin-diary
RUN pip3 install --no-cache-dir services/univention-admin-diary

COPY management/univention-directory-manager-modules management/univention-directory-manager-modules
RUN pip3 install --no-cache-dir management/univention-directory-manager-modules

COPY base/univention-config-registry base/univention-config-registry
RUN pip3 install --no-cache-dir base/univention-config-registry

COPY packaging/univention-debhelper packaging/univention-debhelper
RUN pip3 install --no-cache-dir packaging/univention-debhelper

ENTRYPOINT [ "/app/venv/bin/python3" ]
