# Template for README.md files in packages / apps

When working on a package in this repository, please consider adding a `README.md` file to the top of the package directory, for example `management/univention-directory-listener/README.md`.

The README files' content addresses fellow software developers. It must not be published in the binary distribution.

## Scope

When writing the README file, please consider the intended scope of the content.

* The file contains information _for developers_.
* The file is a starting point for internal documentation about the code, architecture and design of the package.
* When this internal documentation grows beyond a single `README` file or needs more structure to ensure readability, consider creating a proper manual for developers with Sphinx in the package source tree. Other options may be to add the content to the UCS architecture documentation or developer reference, see [UCS Developer documentation overview](https://docs.software-univention.de/developers_5.0.html.en).

## Content

Start the README with a short introduction about what the package does and doesn't do. Link to other existing documentation for that package. This introduction may be read by _non-developers_ at GitHub.

The rest of the file addresses developers.
It contains in-depth information about the inner workings of the software in that package.

Write it from an architectural perspective.

When referring to (software in) another package, please create a separate `README` file in its directory and link to it. Avoid duplicate information, as it will be difficult to keep all versions up to date.

Recommendation: Write explanations about code pieces as docstrings or comments next to the code itself, _not_ into the `README`.

See the template for such a README file below for questions that guide your content writing.

## Template

```markdown
# univention-transmogrifier (package name)

## Introduction

The `univention-transmogrifier` package contains a daemon and a command line frontend that can transform one thing into another.

Administrators can use the package through a UMC module (see package `management/univention-management-console-module-transmogrifier`).
Developers can use the functionality through a REST API interface (see package `management/univention-transmogrifier-rest-api`).

You find user documentation in the [UCS Manual - Transmogrifier](https://docs.software-univention.de/manual-5.0.html#magic:transmogrifier).

## Development

* Architectural decisions:
  * Why was something designed in a certain way?
  * What other alternatives were considered, but discarded?
* Design decisions, for example *Why was something implemented in a certain way?*
* Which classes or components interact with each other?
* What is the purpose of a class or component and what are its boundaries?

## Non-functional requirements

* What requirements and risks for the customers should a developer be aware of? For example:
  * performance requirements
  * security requirements
  * UX / UI design / accessibility
  * Limitations

## Testing

* What environments or scenarios must be tested? For example:
  * _execute software on a Replication node_
  * _modify with a group with 500 members_
  * _login with SAML_
* Do unit tests exist? When are they executed (package built, ucs-test)?
* Do integration tests exist? In what `ucs-test-*` package are they located?
* Do product tests exist? Where are they documented (for example [UCS product tests - Mail](https://git.knut.univention.de/univention/product-tests/ucs/-/blob/main/Mail.md))?

## Building & CI/CD

* How is the package built?
* Which automatisms or pipelines will be triggered by changes to the package?
```
