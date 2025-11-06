# Development Reverse Proxy

Testing the portal with all involved components and a real UCS instance is
possible with the support of this reverse proxy.


## Overview

The basic idea is that this reverse proxy support various development setups:

- running processes locally on your machine
- running containers locally on your machine
- a mix of the two above
- running the processes in production as well as in development mode

The reverse proxy only glues the components together, so that they can be used
end-to-end including the UCS VM which could run locally or remote. It does not
add anything beyond this.


## Requirements regarding the UCS VM

The UCS system will have to be tweaked, so that it does allow certain requests
from the outside. Those requests would usually only be allowed to originate from
the local system.

IMPORTANT: Be aware, these tweaks open up the system in a way in which it is not
supposed to be opened up. This shall only be used until there are better
solutions available and only for the purpose of development.

The following aspects are needed:

- UMC HTTP API has to be exposed.
- Files like `portal.json` and `groups.json` have to be exposed.
- The portal server has to use the HTTP based caching backend.


## Usage example

Assumptions:

- The portal server is reachable on http://localhost:8095
- The portal frontend is reachable on http://localhost:8080

Note: Using other ports and even URLs is possible if the env-files and
configuration files are adapted.

Run the proxy with the following example command:

```
docker compose up reverse-proxy
```

Now open http://localhost:8000/univention/portal/ in your web browser.
