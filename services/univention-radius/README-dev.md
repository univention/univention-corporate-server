# README for Developers (RADIUS)

## Rust development

The packages use the Rust crates provided and packaged by Debian, with the
following exception:

* [`rust-md4`](https://git.knut.univention.de/univention/dev/libraries/rust-md4)
  is maintained by Univention because it is not available in Debian.

For information about packaging Rust crates as Debian packages and how Rust
packages are built in Debian, refer to:

* [Packaging tools](https://rust-team.pages.debian.net/book/packaging-tools.html)
* [Packaging a single crate](https://rust-team.pages.debian.net/book/process-single.html)
* `/usr/share/perl5/Debian/Debhelper/Buildsystem/cargo.pm` - the Cargo build
  system integration provided by `debhelper`
* `/usr/share/cargo/bin/cargo` - Debian's Cargo wrapper

### Static dependencies and rebuilds

Rust dependencies are statically linked into the resulting binaries rather
than dynamically linked at runtime. Consequently, updating a Rust library does
not automatically update binaries that were previously built against it.

Packages therefore need to be rebuilt when one of their statically linked Rust
dependencies receives a relevant update, for example a security fix.

The process for identifying and rebuilding affected packages has not yet been
established. It is being tracked and described in [Track statically linked Rust
dependencies and handle security
updates](https://git.knut.univention.de/univention/dev/internal/securitymonitoring/-/work_items/3).

The concrete Debian packages whose contents were statically incorporated into
a binary are recorded in the binary package's `Static-Built-Using` field. This
field can be used to determine which binary packages need to be rebuilt after
a Rust dependency changes.

## Reminder

The developer should run all the test in the `45_radius` folder after changing
configuration files in radius, as they could affect the results of other tests.

## Radtest

For the test the `radtest` binary is used, sometimes on our test suite
we access directly to the `inner-tunnel` instead of access through the
default service.

This caused a regression on the complete test suite after passing the
username from `inner-tunnel` to the `default` service.

Example: https://git.knut.univention.de/univention/dev/ucs/-/commit/0fa60422362f774ed6afe55a3370f90f8dc7db2d
Regression appeared after modify the inner-tunnel configuration (check the commit message).
