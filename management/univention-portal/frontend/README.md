# UPX Portal Frontend

Vue.js client to recreate the UCS5 Portal for the new Univention Phoenix suite.

## Overview

Written in **Vue.js 3** with **Typescript**. Documentation and guidelines are maintained in our xWiki:
- [Brainstorming](https://projects.univention.de/xwiki/wiki/upx/view/UPX%20Portal/Development%20Guidelines/Brainstorming/) (Discussions and ideas that have not yet been decided by the team)
- [Code Style](https://projects.univention.de/xwiki/wiki/upx/view/UPX%20Portal/Development%20Guidelines/Code%20Style/) (Several rules and best practices on how to style and structure our code)
- [Git Rules](https://projects.univention.de/xwiki/wiki/upx/view/UPX%20Portal/Development%20Guidelines/Git%20Rules/) (Commit message style, merge strategy, feature branches and more guidelines)
- [Tech Stack](https://projects.univention.de/xwiki/wiki/upx/view/UPX%20Portal/Development%20Guidelines/Tech%20Stack/) (Technical decisions about the frameworks, libraries and tools we use)
- [Workflow](https://projects.univention.de/xwiki/wiki/upx/view/UPX%20Portal/Development%20Guidelines/Workflow/) (Description and suggestions on how we work together, track issues, review code...)


## Node version

We have seen various issues, esp. issues related to openssl with more recent
versions of NodeJS.

Currently it is recommended to use `nvm` to provide an older LTS version of NodeJS, e.g. 16.x.

See https://github.com/nvm-sh/nvm

Example commands:

```
# See what's there and available
nvm ls

# Install a LTS version, compare details from the command above.
nvm install lts/gallium

# Use a specific version
nvm use v16.19.0

# Verify the version
node --version
```


## Project setup: Initial steps

The following steps are typically a one-off operation which have to be done once
after having a fresh clone of the repository.

### Prepare the environment file

Have a look at `.env.local_example`. Copy it to `.env.local`. Or copy
`.env.production` instead.


### Be aware of potential feature toggles

Some features may be disabled by default if they are still in ongoing
development. Take a close look into `.env.local_example`.

When we use build time feature toggles, then we prefix those variables with
`VUE_APP_FEATURE` and explain them in `.env.local_example`.


## Container based project setup -- recommended

The container based project setup is in active development. It's main focus is
on providing a test runner environment so that linting and testing can be
executed within the CI pipeline.

All files except the Gitlab CI configuration are within this folder.

The containers can be used locally to run commands in the same environment as
the CI pipeline. Those environments can be used to run the development server
and to run the unit tests with a watcher, see the examples below.


### Using the dev environment container

The stage `local-dev-env` in the `Dockerfile` does define a very basic layer which
just provides a well defined Linux environment. This can be used to run the
frontend inside of this environment instead of directly on your operating
system, so that better isolation is achieved. It is integrated via docker
compose, so that volumes and ports are hooked up automatically.

The following example shows how it can be used:

```sh
# build it
docker compose build dev

# enter a shell
docker compose run -it --rm --service-ports dev

# inside the container the regular yarn commands work:
yarn install
yarn lint
yarn test:unit
yarn test:unit:watch
yarn serve
yarn storybook -p 8080
```


### Using the test runner container

The container defined in `Dockerfile` as stage `test` does provide the needed
environment plus the codebase in order to run the linter and the tests. In
comparison to the `local-dev-env` stage above which only provides an environment, this
stage does include everything needed already.

Tests (both unit and ui tests) can be run using docker compose:

```sh
# Build the image
docker compose build test

# Run unit tests
docker compose run test

# Run UI tests
docker compose run test yarn test:e2e:headless --browser chrome
```



## Notifications API client

The API client is generated from the OpenAPI spec of the `notifications-api`
service. You can re-generate the client in the following way:

```sh
# Ensure that "notifications-api" is up and running
curl http://localhost:8096/openapi.json

# Generate the API client
yarn generate-apis
```



## Project setup

Regardless if you want to run it locally on your Linux machine or on a UCS
server, you need a recent version of NPM (Node Package Manager). So do that as
root:

```
apt install npm  # "old" version
npm install --force -g npm@latest  # newer version
/usr/local/bin/npm install -g yarn  # at the end, we use yarn, not npm

/usr/local/bin/yarn install  # installs all runtime and build dependencies (see yarn.lock)
```

### Sync frontend files into the ucs repository
The frontend of the Portal is still released via the
[UCS](https://git.knut.univention.de/univention/ucs) repository
while the development of the frontend is done in this repository.

To copy the needed files to the ucs repository execute
```
./sync /path/to/git/ucs/management/univention-portal/frontend/
```
The [sync](sync) script should be used because it copies only some selected files instead of the whole repository.

### Sync the files to a UCS

In order to build the project on a UCS, you can sync all dev files from your local git:

```
UCS_MACHINE=10.200.4.80
~/git/frontend/sync $UCS_MACHINE:frontend/
```

### Compiles and hot-reloads for development
```
yarn serve
```

#### In-browser debugging and inspection

For inspecting the state of Vue.js and the Vuex store,
the [Vue.js devtools extension](https://devtools.vuejs.org/guide/installation.html) can be used
(e.g. directly from [Mozillas Addon Store](https://addons.mozilla.org/en-US/firefox/addon/vue-js-devtools/)).


### Compiles and minifies for production
```
yarn build
```

This creates a static HTML file that may be served by UCS' apache. Everything in `dist/*` should be put somewhere in `/var/www/univention/`.

### Lints and fixes files
```
yarn lint
```

### Using a real backend server
Currently, the dev server just serves a static portal.json (from `public/data`). A full portal server that accepts backend calls like tile reordering and so on can be configured by setting up a reverse proxy *on your laptop*.

You need:

- A UCS 5.0 machine with a running portal. See our KVM environment. It runs at, say, 10.200.4.80.
- An alias for localhost, say portal-dev.intranet, added in your local /etc/hosts
- A reverse proxy on your laptop. We are using nginx
  - A config for said proxy (you could just append it to `/etc/nginx/sites-enabled/default`):

```
server {
        listen 80;
        listen [::]:80;
        server_name portal-dev.intranet;

        location /univention/portal/data/portal.json {
                proxy_pass http://10.200.4.80/univention/portal/portal.json;
        }

        location /univention/portal/data/meta.json {
                proxy_pass http://10.200.4.80/univention/meta.json;
        }

        location /univention/portal/data/languages.json {
                proxy_pass http://10.200.4.80/univention/languages.json;
        }

        location /univention/portal/icons/ {
                proxy_pass http://10.200.4.80/univention/portal/icons/;
        }

        location /univention/portal/ {
                proxy_pass http://localhost:8080/;
        }

        location /univention/ {
                proxy_pass http://10.200.4.80/univention/;
        }
}
```

Now you can access the development portal like this: `http://portal-dev.intranet/univention/portal`.

(The /univention/ part is important for cookies set by the backend)

To enable hot reloading, you need to do

`yarn serve --host portal-dev.intranet`


## Translation

We use the UCS tooling and rely on the configuration in the base debian package
at `/debian/univention-portal.univention-l10n`.

Working with the translations can be done trough the `Makefile`. Using `docker
compose` does automatically provide a well defined execution environment:

```
cd /docker

# Update PO files
docker compose run -it --rm deb-builder make l10n-extract

# Compile into MO files and JSON files
docker compose run -it --rm deb-builder make l10n-build
```

The Results of the translation build process can be found in the following
places:

- The Portable Object (PO) files are in [`./src/assets/`](./src/assets/).
- The generated JSON Message Objects will be located in `./public/i18n/`.


## Unit tests
Runs unit tests with Jest
```
yarn test:unit
```

### Update tests interactively
All unit tests run on every change for immediate feedback und regeneration with a keystroke.
(Preferred way to update snapshots)
```
yarn test:unit:watch
```

### Snapshot testing
This is done for simple components, just to ensure that they keep their design while we're changing other stuff.
Most IDEs support this in some degree (e.g. IntelliJ just puts a link to regenerate every failed snapshot test).

### Update all snapshots
Use this command with care
```
yarn test:unit:updatesnapshots
```

## End-to-end tests
Runs e2e tests with Cypress.

```
yarn test:e2e
yarn test:e2e:run
yarn test:e2e:headless
```

## Links and references
- Feather-Sprite Icons: [Overview](https://feathericons.com/)
