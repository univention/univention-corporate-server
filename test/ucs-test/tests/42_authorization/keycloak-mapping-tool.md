# Keycloak IDP mapping tool

A CLI tool for creating IDP mappers in Keycloak.

The tool needs at least an internal and external group name as argument.
If the internal group doesn't exists, it will be created.
If the argument --internal-group-nubus-roles is filled, then an attribute with
the name 'nubus_roles' will be added to the internal group, with the given role as value.

## Configuration

The Keycloak configuration can be setted via a Yaml configuration file. The default file name is `keycloak_mapping_tool_config.yaml`. This can be overwritten via the `--config` argument:

e.g.:
```bash
./keycloak-mapping-tool.py --config my_config.yaml list group
```

An exaample config file can be found [here](keycloak_mapping_tool_config.yaml)

## Usage

### List objects

List all groups in the realm:
```bash
./keycloak-mapping-tool.py list group
```

List all IDP mappers in the configured IDP client:
```bash
./keycloak-mapping-tool.py list mapper
```

### Show objects

Show the details of a group:
```bash
./keycloak-mapping-tool.py show group <GROUP_ID>
```

Show the details of a mapper:
```bash
./keycloak-mapping-tool.py show group <GROUP_ID>
```

### Create IDP mapper

#### By command line args
```bash
./keycloak-mapping-tool.py create mapper \
    --external-group-name <GROUP_NAME> \
    --internal-group-name <GROUP_NAME \
    --internal-group-nubus-role <NUBUS_ROLE>
```

#### By configuration file
```bash
./keycloak-mapping-tool.py create mapper \
    --mapping-config <PATH_TO_JSON_FILE>
```

```json
[
    {
        "external-group-name": "external_group_1",
        "internal-group-name": "internal_group_1",
        "internal-group-roles": "nubus_helpdesk_ou1"
    },
    {
        "external-group-name": "external_group_2",
        "internal-group-name": "internal_group_2",
        "internal-group-roles": "nubus_helpdesk_ou1"
    },
    {
        "external-group-name": "external_group_3",
        "internal-group-name": "internal_group_3",
        "internal-group-nubus-roles": ["nubus_helpdesk_ou1", "nubus_helpdesk_ou2"]
    }
]
```