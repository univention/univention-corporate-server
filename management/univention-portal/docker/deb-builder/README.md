# Debian package builder

The container image in this folder does provide the needed environment, so that
the Debian packaging based processes around the Univention Portal can be used.

The container image is intended to be used for the following two purposes:

1. Locally so that a Developer can easily perform the various tasks from within
   a well defined environment.

2. Automation, especially within our CI Pipelines.


## Building the Debian package itself

The Debian specific utilities are needed in order to be able to build the Debian
package variant of the portal. The provided node version is consistent with the
one in use in the frontend container build, see
[`/frontend/Dockerfile`](../../frontend/Dockerfile).


## Translation handling

The translation handling is based on the Univention specific tooling from the
package `univention-l10n`. This package is provided within the container, so
that it can be used as an environment to perform the various translation related
tasks.

Details are described in [`/docs/translation.md`](../../docs/translation.md).
