# UPX Portal Frontend

Vue.js client to recreate the UCS5 Portal for the new Univention Phoenix suite.

## Overview

Written in **Vue.js 3** with **Typescript**. Documentation and guidelines are maintained in our xWiki:
- [Brainstorming](https://projects.univention.de/xwiki/wiki/upx/view/UPX%20Portal/Development%20Guidelines/Brainstorming/) (Discussions and ideas that have not yet been decided by the team)
- [Code Style](https://projects.univention.de/xwiki/wiki/upx/view/UPX%20Portal/Development%20Guidelines/Code%20Style/) (Several rules and best practices on how to style and structure our code)
- [Git Rules](https://projects.univention.de/xwiki/wiki/upx/view/UPX%20Portal/Development%20Guidelines/Git%20Rules/) (Commit message style, merge strategy, feature branches and more guidelines)
- [Tech Stack](https://projects.univention.de/xwiki/wiki/upx/view/UPX%20Portal/Development%20Guidelines/Tech%20Stack/) (Technical decisions about the frameworks, libraries and tools we use)
- [Workflow](https://projects.univention.de/xwiki/wiki/upx/view/UPX%20Portal/Development%20Guidelines/Workflow/) (Description and suggestions on how we work together, track issues, review code...)

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

Have a look at `.env.local_example`. Copy it to `.env.local`. Or copy
`.env.production` instead.

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

We use the UCS tooling. The configuration is in `debian/phoenixportal.univention-l10n.` 
You need to download the ucs repo to call the following commands: https://git.knut.univention.de/univention/ucs

```
# creates tempprary files for vue and generates/updates de.po
./process_vue_files.sh && ~/git/ucs/packaging/univention-l10n/univention-l10n-build de

# compiles de.po to de.json
~/git/ucs/packaging/univention-l10n/univention-l10n-install de

# copy that json into out public directory
cp {debian/phoenixportal/,}public/i18n/de.json
```

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
```

## Links and references
- Feather-Sprite Icons: [Overview](https://feathericons.com/)

## CI/CD Setup Building .debs
### create / run the builder docker image
* build image `docker build -t phoenixportalbuilder ./builder`
* build deb `sh ./build-package.sh`
* tag image `docker image tag phoenixportalbuilder:latest docker-registry.knut.univention.de/phoenix/phoenixportalbuilder:latest`
* push image to registry: `docker image push docker-registry.knut.univention.de/phoenix/phoenixportalbuilder`
