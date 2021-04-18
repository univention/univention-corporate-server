# UPX Portal Frontend

Vue.js client to recreate the UCS5 Portal for the new Univention Phoenix suite.

## Overview

Written in **Vue.js 3** with **Typescript**. Documentation and guidelines are maintained in our xWiki:
- [Brainstorming](https://projects.univention.de/xwiki/wiki/upx/view/UPX%20Portal/Development%20Guidelines/Brainstorming/) (Discussions and ideas that have not yet been decided by the team)
- [Code Style](https://projects.univention.de/xwiki/wiki/upx/view/UPX%20Portal/Development%20Guidelines/Code%20Style/) (Several rules and best practices on how to style and structure our code)
- [Git Rules](https://projects.univention.de/xwiki/wiki/upx/view/UPX%20Portal/Development%20Guidelines/Git%20Rules/) (Commit message style, merge strategy, feature branches and more guidelines)
- [Tech Stack](https://projects.univention.de/xwiki/wiki/upx/view/UPX%20Portal/Development%20Guidelines/Tech%20Stack/) (Technical decisions about the frameworks, libraries and tools we use)
- [Workflow](https://projects.univention.de/xwiki/wiki/upx/view/UPX%20Portal/Development%20Guidelines/Workflow/) (Description and suggestions on how we work together, track issues, review code...)

## Have a live look

A version that *should* work can be found here: http://10.200.4.60

`ssh lagan.knut.univention.de virsh start dwiesent_ucs5-vue-portal`

You may as well install our latest packages. Add this to `/etc/apt/sources.list`:

```
deb http://omar.knut.univention.de/build2/ ucs_5.0-0-vue-frontend/all/
deb http://omar.knut.univention.de/build2/ ucs_5.0-0-vue-frontend/$(ARCH)/
```

and install the packages `phoenix-portal univention-portal`

This installs the frontend to /univention/phoenix/.

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

## Translation

We use the UCS tooling. The configuration is in debian/phoenixportal.univention-l10n. Here are some commands how to make the translation files locally (and so that they can be checked in):

```
# updates de.po
~/git/ucs/packaging/univention-l10n/univention-l10n-build de

# compiles de.po to de.json
~/git/ucs/packaging/univention-l10n/univention-l10n-install de
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
