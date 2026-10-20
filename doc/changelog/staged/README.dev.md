# UCS release changelog fragments

For UCS minor releases, administrator-visible changes are documented in individual
reStructuredText (reST) fragments. The fragments are merged into the release
changelog later, which avoids conflicts in `doc/changelog/index.rst`.

## How to add an entry

1. Choose the most specific section from the table below.
2. Create `doc/changelog/staged/${section}.${bugids}.rst`, where `${bugids}` is one or more comma-separated bug numbers.
3. Write a short, administrator-facing description of the change in reStructuredText.
4. Commit the fragment together with the corresponding code changes.

Example: `doc/changelog/staged/changelog-umc-server.12345,12346.rst`

```rst
The authentication configuration has been adjusted to support larger environments.
```

**Formatting rules:**

- Do not include bug references in the text; they are derived from the filename.
- Do not prefix the entry with a list marker (`*`).
- End sentences with a period.
- Use reST syntax, for example double backticks for code: ``univention-updater``.
- Use one fragment for each change (with multiple bug IDs if applicable).

The optional Debian changelog fragment is `${srcpkg}/debian/changelog.${bugids}` (without a leading `*` or explicit bug reference).
If omitted, the Debian changelog is generated from Git history using `gbp dch`. This workflow applies to **releases**, not errata updates or apps.

## Available sections

Select the section according to the affected component.
The package names below are examples from the mapping, not an exhaustive list.
Parent sections are valid where no more specific subsection fits.

| Section | Changelog heading | Example packages |
| --- | --- | --- |
| `changelog-general` | General | - |
| `security` | ↳ Security updates | - |
| `debian` | ↳ Debian updates | - |
| `maintained` | ↳ Maintained packages | - |
| `changelog-installer` | Univention Installer | `univention-dvd` |
| `changelog-basic` | Basic system services | - |
| `changelog-basic-kernel` | ↳ Linux kernel and firmware packages | `amd64-microcode`, `intel-microcode`, `linux` |
| `changelog-basis-ucr` | ↳ Univention Configuration Registry | `univention-config-registry` |
| `changelog-basis-ucr-template` | ↳ ↳ Changes to templates and modules | `univention-base-files` |
| `changelog-basis-boot` | ↳ Boot Loader | `insserv`, `shim`, `univention-bootsplash` |
| `changelog-basis-other` | ↳ Other system services | `univention-doc`, `univention-errata-level`, `univention-licence` |
| `changelog-domain` | Domain services | `univention-admin-diary`, `univention-server` |
| `changelog-domain-openldap` | ↳ OpenLDAP | `lmdb`, `openldap`, `univention-directory-logger` |
| `changelog-domain-openldap-acl` | ↳ ↳ LDAP ACL changes | - |
| `changelog-domain-openldap-schema` | ↳ ↳ LDAP schema changes | - |
| `changelog-domain-openldap-replication` | ↳ ↳ Listener/Notifier domain replication | `univention-directory-listener`, `univention-directory-notifier`, `univention-directory-replication` |
| `changelog-domain-dnsserver` | ↳ DNS server | `univention-bind` |
| `changelog-udm` | ↳ LDAP Directory Manager | `univention-directory-manager-modules`, `univention-directory-manager-rest` |
| `changelog-umc` | Univention Management Console | - |
| `changelog-umc-web` | ↳ Univention Management Console web interface | `univention-dojo`, `univention-web` |
| `changelog-umc-portal` | ↳ Univention Portal | `univention-portal`, `univention-server-overview` |
| `changelog-umc-server` | ↳ Univention Management Console server | `univention-management-console`, `univention-management-console-module-lib` |
| `changelog-umc-appcenter` | ↳ Univention App Center | `univention-appcenter`, `univention-app-appliance` |
| `changelog-umc-setup` | ↳ Modules for system settings / setup wizard | `univention-management-console-module-ipchange`, `univention-system-setup` |
| `changelog-umc-update` | ↳ Software update module | `univention-maintenance-mode` |
| `changelog-umc-join` | ↳ Domain join module | `univention-join`, `univention-ldb-modules`, `univention-management-console-module-join` |
| `changelog-umc-user` | ↳ User management | `univention-admingrp-user-passwordreset`, `univention-management-console-module-passwordchange`, `univention-self-service` |
| `changelog-umc-reports` | ↳ Univention Directory Reports | `univention-directory-reports` |
| `changelog-umc-license` | ↳ License module | `univention-system-activation` |
| `changelog-umc-diagnostic` | ↳ System diagnostic module | `univention-management-console-module-diagnostic`, `univention-management-console-module-mrtg`, `univention-support-info` |
| `changelog-umc-top` | ↳ Process overview module | `univention-management-console-module-top` |
| `changelog-umc-policy` | ↳ Policies | `univention-policy` |
| `changelog-umc-quota` | ↳ File system quota module | `univention-quota` |
| `changelog-umc-ucr` | ↳ Univention Configuration Registry module | `univention-management-console-module-ucr` |
| `changelog-umc-ldap` | ↳ LDAP directory browser | `univention-management-console-module-udm` |
| `changelog-umc-other` | ↳ Other modules | `python-notifier`, `univention-management-console-module-reboot`, `univention-management-console-module-services` |
| `changelog-lib` | Univention base libraries | `univention-debug`, `univention-debug-python`, `univention-ldap` |
| `changelog-deployment` | Software deployment | `apt-mirror`, `univention-archive-key`, `univention-debmirror` |
| `changelog-deployment-pkgdb` | ↳ Software monitor | `univention-pkgdb` |
| `changelog-service` | System services | - |
| `changelog-service-postgresql` | ↳ PostgreSQL | `postgresql-common`, `univention-postgresql` |
| `changelog-service-mysql` | ↳ MySQL and MariaDB | `univention-mariadb`, `univention-mysql` |
| `changelog-service-docker` | ↳ Docker | `docker.io`, `univention-appliance-docker-container`, `univention-docker` |
| `changelog-service-saml` | ↳ SAML | `crudesaml`, `php-krb5`, `python-keycloak` |
| `changelog-service-mail` | ↳ Mail services | `univention-fetchmail` |
| `changelog-service-imap` | ↳ ↳ IMAP services | `univention-mail-cyrus`, `univention-mail-cyrus-murder`, `univention-mail-dovecot` |
| `changelog-service-postfix` | ↳ ↳ Postfix | `univention-mail-canonical-maps`, `univention-mail-postfix`, `univention-postgrey` |
| `changelog-service-virus` | ↳ ↳ Spam/virus detection and countermeasures | `univention-antivir-mail`, `univention-dansguardian`, `univention-spamassassin` |
| `changelog-service-print` | ↳ Printing services | `univention-check-printers`, `univention-foomatic-ppds`, `univention-printquota` |
| `changelog-service-nagios` | ↳ Nagios | `univention-monitoring-client`, `univention-nagios`, `univention-nagios-raid` |
| `changelog-service-apache` | ↳ Web services | `univention-apache` |
| `changelog-service-radius` | ↳ RADIUS | `univention-radius` |
| `changelog-service-proxy` | ↳ Proxy services | `squid3`, `univention-squid`, `univention-squid-kerberos` |
| `changelog-service-kerberos` | ↳ Kerberos | `univention-heimdal`, `univention-python-heimdal`, `libpam-krb5` |
| `changelog-service-ssl` | ↳ SSL/TLS | `ca-certificates`, `univention-ssl` |
| `changelog-service-celery` | ↳ Celery services | `univention-celery` |
| `changelog-service-dhcp` | ↳ DHCP services | `univention-dhcp`, `univention-net-installer`, `univention-tftp` |
| `changelog-service-pam` | ↳ PAM / Local group cache | `pam`, `pam-runasroot`, `pam-univentionmailcyrus` |
| `changelog-service-nfs` | ↳ NFS | `univention-nfs`, `univention-home-mounter` |
| `changelog-service-backup` | ↳ Bacula and Backup | `univention-bacula`, `univention-remote-backup` |
| `changelog-service-network` | ↳ Networking services | `univention-firewall`, `univention-ftp`, `univention-network-manager` |
| `changelog-service-other` | ↳ Other services | - |
| `changelog-desktop` | Desktop | `univention-kdm` |
| `changelog-virt` | Virtualization | - |
| `changelog-virt-uvmm` | ↳ UCS Virtual Machine Manager (UVMM) | `openbios`, `seabios`, `univention-kvm-virtio` |
| `changelog-virt-operation` | ↳ Operate UCS as virtual machine | `univention-cloud-init` |
| `changelog-win` | Services for Windows | - |
| `changelog-win-samba` | ↳ Samba | `ldb`, `samba`, `tdb` |
| `changelog-win-takeover` | ↳ Univention AD Takeover | `univention-management-console-module-adtakeover` |
| `changelog-win-s4c` | ↳ Univention S4 Connector | `univention-nagios-s4-connector`, `univention-s4-connector` |
| `changelog-win-adc` | ↳ Univention Active Directory Connection | `univention-ad-connector`, `univention-nagios-ad-connector` |
| `changelog-development` | Development packages | `ucslint`, `univention-debhelper`, `univention-directory-manager-module-example` |
| `changelog-other` | Other changes | `configparser`, `univention-l10n-fr` |

The complete package-to-section mapping and hierarchy are maintained in
[the changelog mapping source](https://git.knut.univention.de/univention/doc-common/-/blob/master/changelog-generate.py)
and
[univention_sphinx_changelog](https://git.knut.univention.de/univention/documentation/univention_sphinx_changelog/-/blob/main/src/univention_sphinx_changelog/ucs.py).

## Merging fragments

During release preparation, the changelog tooling merges staged `.rst`
fragments into `doc/changelog/index.rst` under their respective sections, sorts
entries by bug ID, and removes the staged fragments. Do not manually edit the
generated release changelog for an ordinary change.

For the full workflow and rationale, see
[ADR: Workflow for Debian and Release changelog](https://git.knut.univention.de/univention/dev/internal/decision-records/-/blob/main/ucs/0000-changelog-workflow.md).
