# univention-docker

Debian source package: UCS settings for Docker. Contains configuration adjustments for running Docker in UCS.

## Key contents
- `conffiles/docker-daemon-restart.py` - Script for restarting the Docker daemon
- `conffiles/etc/` - Configuration file templates
- `lib/univention-docker_lib.sh` - Shared shell library for Docker operations
- `systemd/20-univention-firewall.conf` - Systemd drop-in for firewall integration
- `debian/` - Debian packaging including UCR variable definitions, service registration, and postinst script
