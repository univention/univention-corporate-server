# Tests that concern the portal as a whole

The univention portal is housed in a monorepo and consists of subprojects like
portal server, notifications api, frontend etc.

This folder houses tests whose scope is bigger than any single subprojects.
This includes two types of tests:

1. End-to-end tests: These live in the `e2e` folder.
2. Integration tests where the components under test span multiple subprojects:
Currently, we have no such integration tests. When we do, we will store them in the
`integration` folder.

