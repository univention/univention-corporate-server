# univention-docker

Integration package containing configuration adjustments for running Docker on a UCS host. Manages Docker daemon settings, firewall rules, HTTP proxy configuration, and a helper shell library.

## Binary Packages

- `univention-docker`

## Directory Structure

- `conffiles/` -- UCR templates for Docker daemon config (`daemon.json`, `http-proxy.conf`, `/etc/default/docker`, seccomp profile, restart script).
- `lib/` -- `univention-docker_lib.sh` shell helper library.
- `systemd/` -- systemd drop-in for Docker/firewall integration.
- `debian/` -- Debian packaging, UCR variable/service definitions, postinst script.
