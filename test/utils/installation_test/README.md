<!--
SPDX-FileCopyrightText: 2024-2026 Univention GmbH
SPDX-License-Identifier: AGPL-3.0-only
-->

# UCS VNC installation tools

This directory contains two tools that drive the graphical UCS
installer/setup over VNC.
Both connect to a VM's VNC console,
use OCR (via `vncautomate`) to locate on-screen text,
and click/type their way through the dialogs:

- **`vnc-install-ucs.py`** — installs UCS from scratch:
  boot menu, Debian installer and the UCS setup wizard.
- **`appliance-vnc-setup.py`** — runs only the UCS setup wizard
  of an already installed appliance image.

Both share the `VNCInstallation` base class
and the common argument parser in `installation.py`,
so the connection options described below — including the Proxmox VNC bridge —
apply to both tools identically.

## Requirements

- Python 3.10+
- `vncdotool` and `vncautomate` (OCR, wraps Tesseract)
- `twisted`
- `websockets` — **only** needed for the Proxmox VNC bridge mode (see below)

## Connection modes (both tools)

Each tool can reach the VM's VNC console
in one of two mutually exclusive ways:

1. **Direct VNC** — connect to an already reachable VNC screen with `--vnc`.
2. **Proxmox VNC bridge** — connect through the Proxmox API.
   Proxmox exposes a VM's console only via an authenticated WebSocket,
   so the tool authenticates with a Proxmox **API token**,
   obtains a short-lived VNC ticket,
   and runs a small local TCP↔WebSocket bridge in a background thread.
   The VNC client then connects to that local port.

Exactly one mode must be selected.
The Proxmox bridge is activated as soon as
`--proxmox-node` **and** `--proxmox-vmid` are given;
`--vnc` must then be omitted (and vice versa).

### Proxmox credentials file

In bridge mode the Proxmox connection details are read from a JSON file
passed via `--proxmox-credentials`
(e.g. the `ucs-ec2-tools.json` used by `ucs-ec2-tools`).
It must contain at least:

```json
{
    "proxmox_host": "proxmox.knut.univention.de",
    "proxmox_api_user": "myusername@LDAP",
    "proxmox_api_token_name": "my_token_name",
    "proxmox_api_token_secret": "12334567-abcd-efab-1234-678901234567"
}
```

The API token identifier is assembled as
`<proxmox_api_user>!<proxmox_api_token_name>`
and sent as an `Authorization: PVEAPIToken=…` header —
no password login and no CSRF token are involved.
The Proxmox API port defaults to `8006` (override with `--proxmox-port`).
TLS certificate verification is disabled,
since Proxmox nodes usually present self-signed certificates.

The API token needs the `VM.Console` privilege on the target VM
(path `/vms/<vmid>`, or `/vms`).
If the token was created with *privilege separation*,
assign that permission to the token explicitly.

### Connection options (shared)

| Option | Description |
| --- | --- |
| `--vnc HOST::PORT` | Connect directly to this VNC screen. Mutually exclusive with the Proxmox options. |
| `--proxmox-node NODE` | Proxmox node the VM runs on. Enables bridge mode (with `--proxmox-vmid`). |
| `--proxmox-vmid VMID` | Proxmox VM ID. Enables bridge mode (with `--proxmox-node`). |
| `--proxmox-credentials FILE` | Path to the credentials JSON. Required in bridge mode. |
| `--proxmox-port PORT` | Proxmox API port (default: `8006`). |

### Common options (shared)

Provided by `installation.py` and available in both tools:

| Option | Default | Description |
| --- | --- | --- |
| `--fqdn FQDN` | `master.ucs.test` | Fully qualified host name to set. |
| `--password PW` | `univention` | Password for `root` and/or `Administrator`. |
| `--organisation NAME` | `ucs` | Organisation name (used for the `master` role). |
| `--dns IP` | | DNS server of the UCS domain to join (required for join roles). |
| `--join-user USER` | | User name authorised to join the domain (required for join roles). |
| `--join-password PW` | | Password for the join user (required for join roles). |
| `--screenshot-dir DIR` | `./screenshots` | Directory for screenshots taken during setup. |
| `--logging`, `-l LEVEL` | `info` | Log level: `critical`, `error`, `warning`, `info`, `debug`. |
| `--debug-boxes FILE` | | Dump detected OCR text boxes. |
| `--debug-screen FILE` | | Dump the captured screen. |
| `--debug-gradients-x FILE` | | Dump horizontal gradients. |
| `--debug-gradients-y FILE` | | Dump vertical gradients. |
| `--debug-dir DIR` | | Directory for OCR debug artifacts. |

## `appliance-vnc-setup.py`

Runs the UCS setup wizard of a booted appliance:
language and localization, network, domain role,
organisation and password, host name, and the final configuration run.

Tool-specific options:

| Option | Default | Description |
| --- | --- | --- |
| `--role {master,admember,fast,slave}` | `master` | UCS system role to configure. |
| `--ucs` | off | Treat the image as a UCS appliance (creates a new UCS domain). |

Examples:

```bash
# Direct VNC connection (unchanged behaviour)
appliance-vnc-setup.py --vnc 10.0.0.5::5901 --role master

# Through the Proxmox VNC bridge, creating a new UCS domain
appliance-vnc-setup.py \
  --proxmox-node uni-pve-02 \
  --proxmox-vmid 5402 \
  --proxmox-credentials ./ucs-ec2-tools.json \
  --role master
```

## `vnc-install-ucs.py`

Installs UCS from scratch:
picks the boot-menu entry, walks through the Debian installer
and then the UCS setup wizard.

Tool-specific options:

| Option | Default | Description |
| --- | --- | --- |
| `--role {master,backup,slave,member,admember,applianceEC2,applianceLVM}` | `master` | UCS system role to install. |
| `--language {deu,eng,fra}` | `deu` | Text language of the installer. |
| `--school-dep {central,edu,adm}` | | Select the UCS@school role. |
| `--ip IP` | | IPv4 address if DHCP is unavailable. |
| `--netmask MASK` | | Network netmask. |
| `--gateway IP` | | Default router address. |
| `--second-interface IFACE` | | Configure a second interface. |

Examples:

```bash
# Direct VNC screen
vnc-install-ucs.py --vnc 10.0.0.5::5901 --role master

# Through the Proxmox VNC bridge
vnc-install-ucs.py \
  --proxmox-node uni-pve-02 \
  --proxmox-vmid 5402 \
  --proxmox-credentials ./ucs-ec2-tools.json \
  --role master
```

Joining an existing domain as a Replica Directory Node (role `slave`)
requires the join options:

```bash
vnc-install-ucs.py \
  --proxmox-node uni-pve-02 --proxmox-vmid 5402 \
  --proxmox-credentials ./ucs-ec2-tools.json \
  --role slave \
  --dns 10.200.0.1 \
  --join-user Administrator \
  --join-password univention
```

## How the Proxmox bridge works

1. The credentials file is loaded and validated.
2. A single `POST /nodes/<node>/qemu/<vmid>/vncproxy` call
   (authenticated with the API token)
   returns the WebSocket `port` and a VNC `ticket`.
3. A TCP server is started on `127.0.0.1` (an ephemeral port)
   in a background daemon thread.
   Each accepted connection is bridged to the Proxmox `vncwebsocket` endpoint.
4. The VNC client connects to the local port.
   The Proxmox VNC ticket is used as the RFB password.

The VNC ticket is short-lived
and serves both as the WebSocket authorisation and as the RFB password,
so it is fetched once and used immediately —
this mode is intended for a single automation session,
not for reconnecting clients.

The bridge runs as a daemon thread
and is torn down automatically when the process exits.
