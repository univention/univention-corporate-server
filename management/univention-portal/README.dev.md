# Univention Portal - Developer Information

## Overview

The following components form the Univention portal:

- [Frontend in `frontend/`](./frontend/) -- The client side implementation of
  the portal.

- [Server in `./`](./) -- The portal server is currently located in the root
  folder. The source code is in [`python/`](./python/) and the tests are inside
  of [`unittests/`](./unittests/).

  We aim to group the portal server inside a sub folder
  [`portal-server`](./portal-server).

- [Notifications API in `notifications-api/`](./notifications-api/) -- The
  backend api needed for server side notification handling.

- [Portal Consumer](./portal_consumer) -- The consumer is responsible for
  listening to changes in the LDAP and updating the portal accordingly.

  We aim to group the consumer related code inside of a sub folder
  [`portal-consumer`](./portal-consumer).

## Utilities

The following utilities are in use for development, ci integration and
packaging:

- [Ansible in `ansible/`](./ansible/) -- Ansible scripts which capture useful
  and needed tweaks to adjust the state of a given UCS machine.
- [Debian Package in `debian/`](./debian/) -- (deprecated) Configuration and
  scripts to build a Debian package out of the codebase. This has in the past
  also been used to develop the portal on a UCS machine. We keep it in a working
  state until the migration towards containers has been fully achieved and
  proven to be solid also for all use cases from a developer's perspective.
- [Docker in `docker/`](./docker) -- Docker based tooling is kept inside of the
  subdirectory `./docker/`. An exception are the Dockerfiles related to a
  component, those are typically in the root folder of the respective component.
  The packaging of new components is only based on docker containers, old
  components are being migrated into a container based packaging.
- [Docker Compose in `docker/`](./docker) -- Docker compose is in use as a
  convenience utility to ease the process of starting the application locally.
- [Helm in `helm/`](./helm) -- Helm is used as a package manager to ease the
  installation in Kubernetes.
- [Gitlab CI in `.gitlab-ci.yml`](./.gitlab-ci.yml) -- The pipeline
  configuration shows which checks are automatically run and how they are run.

## Working with container images locally

### Preparation of a UCS machine for development

Have a UCS machine ready for development. The machine has to be patched so that
it can be integrated into a development environment, see the folder
[`ansible/`](./ansible/) regarding details.

1. Define your inventory file if it's not yet there.
2. Apply the playbooks as shown in the below example.

```shell
ansible-playbook -i ansible/hosts.yaml \
    ansible/ucs-umc-open-for-portal-server.yaml \
    ansible/ucs-expose-portal-json-files.yaml \
    ansible/fetch-secrets-from-ucs-machine.yaml
```

### Preparation of Keycloak for development

In `docker/docker-compose.yaml` you can find a service called `keycloak` which
you will need to test the SAML login and work on the notifications OIDC.

1. Create the file `docker-compose.override.yaml` from the example:
    ```bash
    cp docker/docker-compose.override.yaml.example docker/docker-compose.override.yaml
    ```
2. Go to your UCS machine, run the following commands. You will need the output in the next step.
    a.
        ```bash
        echo `cat /etc/idp-ldap-user.secret`
        ```
    b.
        ```bash
        ucr get ldap/base
        ```
3. Open the file `docker/docker-compose.override.yaml` and fill the following values under `keycloak.environment`:
  a. `LDAP_BASE`: the value from `ucr get ldap/base`.
  b. `LDAP_SECRET`: the contents of `/etc/idp-ldap-user.secret`.
  c. `LDAP_SERVER`: the LDAP server on your UCS machine, e.g. `ldap://10.200.XX.YY:7389`.

4. Enable the SAML login on the UCS machine with the playbook:
  ```shell
  ansible-playbook -i ansible/hosts.yaml ansible/ucs-login-with-local-keycloak.yaml
  ```
5. Step 4 copied the SSL certificates from the UCS host to the local
   reverse-proxy and keycloak. Follow the next section to rebuild the images
   (including the SSL certificates) and restart the stack.

> Once you have the full stack running (see below), you can reach the Keycloak
> UI at http://localhost:8097/admin with the username and password set in `docker-compose.yaml`.
>
> Feel free to play around with `portal-notifications` client and mappings.
> The default configuration provided might not be valid for your setup for some cases.

### Build and run containers locally

An adjusted docker compose file has been created to make it easier to build the
current state into container images and to run those images. This file can be
found at `docker/docker-compose.yaml`. It will run the production containers in
a local setup.

Preparation:

- Ensure that you have a local copy of the file `/docker/.env.example`, otherwise
  `docker compose` will refuse to run your containers.

  ```sh
  cp docker/.env.example docker/.env
  ```

- You have to set at least the correct value for `UCS_BASE_URL`, so that your
  UCS machine will be reached.

- The other values should work out of the box and only need modification in
  adjusted setups or non-Linux systems.

Example:

```sh
# Be inside the folder docker
cd docker

# Build images
docker compose build

# Run the containers locally
docker compose up
```

Check if http://localhost:8000/ does give you a "roughly" working portal.

### Interaction from the command line

A simple interaction example with the running containers:

```sh
$ curl http://localhost:8080/
<!DOCTYPE html><htm [...]

$ curl http://localhost:8095/univention/portal/portal.json
{"cache_id": "1667994988.804391", "user_links": [], "menu_links": [...]
```

### Local development

#### Run a development server

You can run a development server of the frontend and then start the other
services based on the docker compose file:

```sh
# Bring up proxy and portal server
cd docker
docker compose up --build portal-server reverse-proxy notifications-api

# Run the frontend dev server locally
cd frontend
yarn serve
```

The idea of the `reverse-proxy` is that any combination of production and
development containers and processes is possible, as long as they bind to the
correct ports on the local machine.

See [`docker/reverse-proxy/`](./docker/reverse-proxy/) regarding further
details.

#### Utilities provided via docker compose

Further examples regarding provided containers:

```sh
# Make sure you are in the folder "docker"
cd docker

# Build images
docker compose build portal-server

# Run the containers locally
docker compose up portal-server

# Run the portal server tests locally
docker compose run test

# Run the linter container
docker compose run pre-commit

# Generate the Helm chart readmes
docker compose run helm-docs
```
