## PEP440 build versions

Derives valid PEP440 version from the projects `debian/changelog`.
Detects if running on the main branch or a MR.

This enables building pip packages in MR pipelines appending git commit hashes
as well as building final versions when merged into the default branch.

## Behavior:

* On the default branch (``CI_COMMIT_BRANCH == CI_DEFAULT_BRANCH``):
  emit the upstream version, e.g. ``12.5.6``.
* Everywhere else (feature branches, MR pipelines, local builds):
  append ``.dev0+g<short-sha>``, e.g. ``12.5.6.dev0+g1a2b3c4``.
  The sha uniquifies each commit so concurrent MRs bumping to the same
  changelog version don't collide in the package registry.

## TODO:
- what to do for old version non default branches?
