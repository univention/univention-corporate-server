# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2023-2024 Univention GmbH

ARG UCS_BASE_IMAGE_TAG="0.10.0"
ARG UCS_BASE_IMAGE="gitregistry.knut.univention.de/univention/components/ucs-base-image/ucs-base-506"

###############################################################################
# Creates a yarn builder

FROM ${UCS_BASE_IMAGE}:${UCS_BASE_IMAGE_TAG} AS local-dev-env

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ARG NODE_VERSION="14.21.3"
ARG YARN_VERSION="1.22.1"
ARG NODE_SHA256="bef2685d9469058c1229cc7789e171861044fe3f70316ec744e9bf3609cd45ed"

# The following dependencies are only needed when on an aarch64 platform,
# because then the package "deasync" does not include ready made binaries
# for the platform and falls back to compiling them.
#
# This is relevant for developers who work on machines with Apple's M1
# processors.
RUN \
  apt-get --quiet --quiet update \
  && apt-get install  --assume-yes --verbose-versions --no-install-recommends \
  "ca-certificates=20200601*" \
  "wget=1.20.*" \
  && if [[ "$(uname -m)" == "aarch64" ]]; then \
    apt-get --assume-yes --verbose-versions --no-install-recommends install \
    "gcc=4:8.*" \
    "g++=4:8.*" \
    "make=4.*" \
    "python3=3.7.*" \
  ; fi \
  && rm -fr "/var/lib/apt/lists/*" "/var/cache/apt/archives/*" \
  && wget --progress="dot:giga" --output-document="node.tar.gz" \
  "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.gz" \
  && echo "${NODE_SHA256}  node.tar.gz" > SHA256 \
  && sha256sum --check "SHA256" \
  && tar xz -C "/usr/local" --strip-components=1 -f "node.tar.gz" \
  && rm -f "node.tar.gz" "SHA256" \
  && NODE_RESULT=$(node --version) \
  && echo "node version: ${NODE_RESULT}" \
  && if [[ "${NODE_RESULT}" != "v${NODE_VERSION}" ]]; then echo "Bad node version"; exit 1; fi \
  && npm install -g yarn@"${YARN_VERSION}" \
  && yarn set version "${YARN_VERSION}" \
  && YARN_RESULT=$(yarn --version) \
  && echo "yarn version: ${YARN_RESULT}" \
  && if [[ "${YARN_RESULT}" != "${YARN_VERSION}" ]]; then echo "Bad yarn version"; exit 1; fi \
  && apt-get --assume-yes --verbose-versions purge ca-certificates wget

WORKDIR /app
CMD ["/bin/bash"]


FROM local-dev-env as base
COPY ./package.json .
COPY ./yarn.lock .

RUN \
  npx browserslist@latest --update-db \
  && yarn install --frozen-lockfile \
  && yarn cache clean

# Copy should come after yarn install to prevent long rebuilding time
COPY . .


# The dev-server stage is running a development server. This is intended to be
# used with the Tilt based development environment.
FROM base AS dev-server

# Define the command for the local-dev-env run in Tilt.
#
# Currently it is not possible to inject this from the Tilt configuration.
# See https://github.com/tilt-dev/tilt-extensions/issues/391#issuecomment-1687045699
CMD ["yarn", "serve", "--port", "80"]


###############################################################################

FROM base as build

RUN yarn build


###############################################################################
# Starts production nginx server

FROM gitregistry.knut.univention.de/univention/customers/dataport/upx/container-nginx/nginx:0.1.1 AS final

COPY --from=build /app/dist /var/www/html

###############################################################################
