# README for Developers (RADIUS)

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
Regression appeared after modify the inner-tunnel configuration. (Check the commit message)
