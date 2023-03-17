_[TOC]_

# univention-keycloak

TODO

## TODO

## Keeping track of keycloak upgrades

The idea is that init sets up the config, but can only be executed once per
domain. For updates we add a code block to `upgrade-config` for a specific
version. `upgrade-config` keeps track of the domain wide config status and
executes upgrade steps for all version between the domain config status and
the version we are currently upgrading to.

### Upgrade status for versions

The information of the "domain wide config status" (basically the version
keycloak was installed or the version of the last update) is stored in the
`setting/data` object `cn=keycloak,cn=data,cn=univention,,...` as `json`
(the object itself is created in `app/configure_host`):
```json
{
	...
	"domain_config_version": "19.0.2-ucs1",
	"domain_config_init": "18.0.0",
	...
}
```

`domain_config_version=19.0.2-ucs1` means, the app was installed with version
19.0.2-ucs1 or the last update (including upgrade steps) was the update to
this version.

`domain_config_init=19.0.2-ucs1` -> keycloak was installed with this version.

### Managing the upgrade status

`univention-keycloak` is responsible for managing the upgrade status for the
keycloak app.

* it does not create the settings/data object, this is done in
  `app/configure_host` -> Traceback if not existing
* if `init` is executed it stores the current version of the keycloak app in
  `domain_config_version` and `domain_config_init` (and init should do
  everything to bring the keycloak configuration to this level)
* in `upgrade-config`
  * we get the `domain_config_version` and the current keycloak version
  * execute all upgrade steps from `domain_config_version` to the current
    version (excluding "domain_config_version" version)
  * save the current version in `domain_config_version`

Note: All of this is only executed if `univention-keycloak` is runs on a UCS
system.

### Manually managing domain config version

```sh
# get the complete settings/data object
-> univention-keycloak  domain-config --json --get

# get current status
-> univention-keycloak  upgrade-config --dry-run

# which updates are missing
-> univention-keycloak upgrade-config --get-upgrade-steps --json
```

Only for tests or in case of in case of emergency (normally only
univention-keycloak should manage the upgrade status)!
```sh
# set domain config version
univention-keycloak  domain-config --set-domain-config-version 17.0.0

# set domain init version
univention-keycloak  domain-config --set-domain-config-init 17.0.0
```

### Example: New app version with new config setting

* add the new setting to `init` (so that new installations work)
  ```python
  def init_keycloak_ucs(...
      ...
      add_new_feature_config()

  ```
* add a block to `upgrade_config` and extend the upgrade version list (never
  change the order of this list)
  ```python
  def upgrade_config(...
     ...
      upgrades = ["19.0.2", "20.20.1-ucs99"]
      upgrade_steps = upgrades[upgrades.index(domain_config_version) + 1:]
      for step in upgrade_steps:
          print(f"Running update steps for version: {version}")
          if step = "19.0.2":
              if not opt.dry_run:
              add_bla_bla()
          if version == "20.20.1-ucs99":
              print(f"Running update steps for version: {version}")
              if not opt.dry_run:
                 add_new_feature_config()
  ```
* raise join script version

### Example: Join script

```sh
VERSION="5"

joinscript_init

# if init is necessary, this also sets domain_config_version
# and domain_config_init to the current keycloak version
univention-keycloak init || die

...


# on updates, upgrade-config runs all upgrade
# steps between "domain_config_version" and
# the current keycloak version and save the
# current version in "domain_config_version"
if ! ucr_is_false keycloak/auto-migration
	univention-keycloak upgrade-config || die
fi

joinscript_save_current_version
```
