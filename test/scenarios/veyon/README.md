_[TOC]_

# Veyon test environment

We have jobs (KVM, EC2) to create a veyon test environment. These jobs setup a
multiserver school environment with a primary, a school replica and a number
of windows clients. The windows clients are joined into the replica domain and
veyon is installed. After the setup you can open the replica's UMC and the
computerroom module where all the windows clients should be available.

## Jenkins Jobs

* create test environment in KVM `UCSschool-5.0 -> VeyonEnv -> Create Veyon Environment in KVM`
  * creates a personal instances (username_windows-veyon-5.0-1)
  * Instances have to be removed manually!!
* create test environment in EC2 `UCSschool-5.0 -> VeyonEnv -> Create Veyon Environment in EC2`
* get running EC2 test instances `UCSschool-5.0 -> VeyonEnv -> Get EC2 Veyon Environment`
* delete running EC2 test instances `UCSschool-5.0 -> VeyonEnv -> Destroy EC2 Veyon Environment`

## Files
* **veyon.cfg** - the ucs-ec2/kvm-create config file (used in KVM/EC2 jenkins jobs)
* **veyon.json** - the veyon config file (copied to the replica and windows clients, applied after the veyon installation on windows)
* **start-kvm.sh** - used in the KVM jenkins job to start a KVM env, can be used on cli as well (default number of windows clients 3, configurable via `UCS_ENV_VEYON_WINDOWS_HOST`)
* **start-ec2.sh** - used in the EC2 jenkins job to start a EC2 env, can be used on cli as well, fails if ec2 veyon instances (tag usecase:veyon-test-environment) exist
* **get-ec2.sh** - get running EC2 veyon instances
* **destroy-ec2.sh** - delete running EC2 veyon instances
* **utils-veyon.sh** - helper for veyon/aws setup
* **create_veyon_cfg.py** - used in start-kvm.sh and start-ec2.sh to copy the windows section
* **create_computer_rooms.py** - used during the setup to create computer rooms

## Examples

Create test env in KVM with 2 windows hosts:
```
UCS_ENV_VEYON_WINDOWS_HOST=2 ./scenarios/veyon/start-kvm.sh
...
```
Get ec2 test instances:
```
./scenarios/veyon/get-ec2.sh
---------------------------------------------------------------------------------
|                               DescribeInstances                               |
+----------------------+-------------+-------------------------+----------------+
|          id          |     ip      |          name           |   public_ip    |
+----------------------+-------------+-------------------------+----------------+
|  i-00f7dc02db1d5560d |  10.0.0.44  |  Test-jenkins-replica   |  None          |
|  i-06afd51b7596bbc83 |  10.0.0.35  |  Test-jenkins-windows   |  None          |
|  i-0e3878d7352037b52 |  10.0.0.51  |  Test-jenkins-primary   |  34.249.17.195 |
|  i-0c1ba56dc230c6cfc |  10.0.0.244 |  Test-jenkins-windows2  |  None          |
+----------------------+-------------+-------------------------+----------------+

```

## KVM

The `win10-pro-winrm_de-winrm-credssp_amd64.tar.gz` ucs-kt-get template is
used for the windows clients.

## EC2

The `Windows_Server-2016-German-Full-Base-*` AMI is used for the windows
clients. All instances are created in the private subnet
`subnet-0c8e0b6088ba000b2` (vpc: `vpc-09941d80c8a62cae9`). Only the primary
server gets an public IP (eip: `eipalloc-07d5af32fb6f5a4ac`). This host is
used as proxy by ucs-ec2-create to connect to the other instances.

For internet access a egress internet gateway (`eigw-0b68f6acf5258500a`) is
used. This eigw supports only IPv6. Therefor the subnet assigns IPv6 addresses
automatically to all instances.

## Passwords

### KVM

Windows/root/Administrator - the standard password.

### EC2

Windows/root/Administrator - the password from stdout of the job (`[windows] Get password: done (thepassword)`)

## Access to EC2 instances

Access to the instances is possible via the public ip
(`eipalloc-07d5af32fb6f5a4ac` -> 34.249.17.195) as proxy.

Add a .ssh/config config like this:
```
Host veyon-proxy
  Hostname 34.249.17.195
  User root
  IdentityFile ~/ec2/keys/tech.pem
  StrictHostKeyChecking=no
  UserKnownHostsFile=/dev/null
```

SSH to the replica:
```
ssh -i ~/ec2/keys/tech.pem root@REPLICA_PRIVATE_IP -J veyon-proxy"
```

SSH tunnel for UMC on https://localhost:2000:
```
ssh veyon-proxy -L 2000:PRIVATE_IP:443 -N
```

SSH tunnel for RDP on localhost:2000:
```
ssh veyon-proxy -L 2000:WINDOWS_PRIVATE_IP:3389 -N
```

## Known issues

### EC2

* Error during login with roaming profiles (because in ec2 the windows
  instances get another dns domain), can be ignored for now, best to
  deactivate roam profiles.
* RDP session: By default the veyon software on the windows clients does not
  support RDP. There are two ways to tackle this problem.
  1. Non-interactive logon on windows, but as we can never access this session
     (ec2 does not support VNC to the local session) this may not be to helpful.
     ```
     ucs-winrm logon-as --username student --userpwd password --client ...

     ```
  2. Activte remote sessions in veyon software on the windows client. The problem with
     that is, that the we have to change the default port for the veyon service on windows
     in order for our veyon client to find the RDP session. Normally the default port is for
     the local session. We can change this to the (first) RDP session, then our client finds
     the session. But as the veyon service only starts if a RDP session exists, the port is
     not reachable if nobody is logged in (via RDP) and the for the client it looks like
     the computer is down.
     To activate RDP sessions in the veyon software, use the following config on windows:
     ```
     {
       "AccessControl": {
         "DomainGroupsEnabled": true
       },
       "Authentication": {
         "Method": 1
       },
       "Network": {
         "FirewallExceptionEnabled": "1",
         "VeyonServerPort": 11099
       },
       "Service": {
         "MultiSession": "true"
       }
     }
     ```
* RDP sessions can't handle users with `pwdChangeNextLogin` (user has to change password on next logi)
