# Portal Extension

This is the extension bundle of the Portal for Nubus.


## Status - Stable

The extension is based on the
[Extension image structure](https://git.knut.univention.de/univention/internal/nubus-infocenter/-/blob/main/topics/extensions/extension-image-structure.md?ref_type=heads).


## Required configuration in the template context

- `svcPortalServerUserPassword`: The password for the service account user has
  to be provided in this parameter.

  Updating this value to rotate the secret is not yet supported.
