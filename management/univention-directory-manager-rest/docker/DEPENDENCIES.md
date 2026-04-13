# UDM REST API — Dependency Analysis for Source-Based Container Build

## Goal

Move from building the container from `.deb` packages to building from source.
Dependencies are categorised into three tiers:

- **Tier 1** — Available on PyPI, just `pip install`
- **Tier 2** — Internal to this repo, but have `setup.py`/`setup.cfg` (can be pip-installed from path)
- **Tier 3** — Internal to this repo, no setuptools config (must be copied manually)

Long-term: eliminate tier 3 (and eventually remove the UMC dependency entirely).

---

## Tier 1 — PyPI packages

Direct dependencies of the REST API server itself (from `debian/control`):

| PyPI package     | Debian package          | Notes                        |
|------------------|-------------------------|------------------------------|
| tornado          | python3-tornado         | Web framework                |
| genshi           | python3-genshi          | Templating                   |
| pycurl           | python3-pycurl          | HTTP client (C extension)    |
| defusedxml       | python3-defusedxml      | Safe XML parsing             |
| jinja2           | python3-jinja2          | Templating                   |
| python-mimeparse | python3-mimeparse       | Content negotiation          |
| setproctitle     | python3-setproctitle    | Process title                |
| uritemplate      | python3-uritemplate     | URI templates for HAL links  |
| python-ldap      | python3-ldap            | LDAP client (C extension)    |
| requests         | python3-requests        | HTTP client (for client lib) |

Transitive PyPI dependencies pulled in by tier 2/3 packages:

| PyPI package     | Needed by                              | Notes                              |
|------------------|----------------------------------------|------------------------------------|
| lazy-object-proxy| univention-config-registry             |                                    |
| logfmter         | univention-debug-python                | Structured logging                 |
| lark             | univention-directory-manager-modules   | LDAP filter parsing                |
| email-validator  | univention-directory-manager-modules   |                                    |
| dnspython        | univention-directory-manager-modules   |                                    |
| passlib          | univention-directory-manager-modules   |                                    |
| cracklib         | univention-directory-manager-modules   | Password strength (C extension)    |
| unidecode        | univention-directory-manager-modules   |                                    |
| dateutil         | univention-directory-manager-modules   |                                    |
| Pillow           | univention-directory-manager-modules   | Image handling (C extension)       |
| python-magic     | univention-directory-manager-modules   |                                    |
| pam              | univention-management-console          |                                    |
| PyYAML           | univention-management-console          |                                    |
| sdnotify         | univention-management-console          |                                    |
| trml2pdf         | univention-directory-reports           | PDF report generation              |
| polib            | univention-lib                         | Gettext .po file handling          |

System libraries needed at runtime (apt-get):

| Package                    | Needed by                          |
|----------------------------|------------------------------------|
| libunivention-debug1       | univention-debug-python            |
| libsasl2-modules-oauthbearer | LDAP OAUTHBEARER auth            |
| python3-samba              | univention-directory-manager-modules (not on PyPI) |
| python3-ldb                | univention-directory-manager-modules (not on PyPI) |
| libunivention-license0     | univention-directory-manager-modules (C ext) |

---

## Tier 2 — Internal packages with setup.py/setup.cfg

These live in this monorepo and can be `pip install -e <path>` or built as wheels.

### univention-config-registry
- **Path:** `base/univention-config-registry`
- **Build config:** setup.py + setup.cfg
- **Internal deps:** **univention-debhelper** (runtime — `handler.py` imports `univention.debhelper.parseRfc822`)
- **PyPI deps:** lazy-object-proxy
- **Notes:** Not a true leaf — needs univention-debhelper installed too.

### univention-debhelper
- **Path:** `packaging/univention-debhelper`
- **Build config:** setup.py
- **Internal deps:** none
- **PyPI deps:** none (pure stdlib)
- **Notes:** Tiny package, single file `univention/debhelper.py`. Pip-installable.

### univention-debug-python
- **Path:** `base/univention-debug-python`
- **Build config:** setup.py
- **Internal deps:** none
- **PyPI deps:** logfmter
- **Notes:** C extension wrapping `libunivention-debug`. Needs the `.deb` `libunivention-debug-dev` at build time and `libunivention-debug1` at runtime. Provides `univention.debug` and `univention.logging`.

### univention-python
- **Path:** `base/univention-python`
- **Build config:** setup.py
- **Internal deps:** univention-config-registry, univention-debug-python
- **PyPI deps:** python-ldap
- **Notes:** Provides `univention.password`, `univention.uldap`, `univention.dn`, etc.

### univention-directory-manager-modules
- **Path:** `management/univention-directory-manager-modules`
- **Build config:** setup.cfg
- **Internal deps:** univention-config-registry, univention-debug-python, univention-python, univention-lib (tier 3), univention-authorization (tier 3)
- **PyPI deps:** lark, email-validator, dnspython, passlib, cracklib, unidecode, dateutil, Pillow, python-magic, python-ldap
- **System deps:** python3-samba, python3-ldb, libunivention-license0
- **Notes:** The big one. `univention.admin.*` namespace. Has tier 3 deps so installing it cleanly requires those to be available first.

### univention-management-console
- **Path:** `management/univention-management-console`
- **Build config:** setup.py (custom build commands)
- **Internal deps:** univention-config-registry, univention-debug-python, univention-python, univention-lib (tier 3), univention-directory-manager-modules
- **PyPI deps:** pam, PyYAML, sdnotify, tornado
- **Notes:** Slated for removal as a dependency. Complex setup.py with custom build steps.

---

## Tier 3 — Internal packages without setuptools (copy only)

These need their Python files manually copied into the image.

### univention-lib  (**candidate for promotion to tier 2**)
- **Path:** `base/univention-lib`
- **Build config:** none (Makefile) — adding setup.py/pyproject.toml is straightforward
- **Internal deps:** univention-config-registry, univention-debug-python, univention-python
- **PyPI deps:** polib (and others for modules the REST API doesn't use)
- **Python files:** `python/univention/lib/*.py` -> `univention.lib` (16 modules)
- **Notes:** The REST API only uses `univention.lib.i18n`, which is **pure stdlib** (gettext, locale, re) — zero internal deps. The heavier deps (python-ldap, samba, ldb, Pillow) are only in other modules. Adding a setup.py is easy; the heavy deps could be optional extras.

### univention-authorization  (**candidate for promotion to tier 2**)
- **Path:** `management/univention-authorization`
- **Build config:** none — adding setup.py/pyproject.toml is trivial (4 files)
- **Internal deps:** univention-python, univention-config-registry (both tier 2)
- **PyPI deps:** lark, requests, PyYAML
- **Python files:** `modules/univention/authorization/*.py` -> `univention.authorization` (4 files)
- **Notes:** Small package. All deps are tier 1 or tier 2. Easy promotion.

### univention-directory-reports
- **Path:** `management/univention-directory-reports`
- **Build config:** none (Makefile)
- **Internal deps:** univention-directory-manager-modules, univention-config-registry, univention-debug-python, univention-lib
- **PyPI deps:** trml2pdf
- **Python files:** `modules/univention/directory/reports/*.py` -> `univention.directory.reports`
- **Notes:** PDF/CSV report generation for directory entries.

### univention-management-console-module-udm  (going away)
- **Path:** `management/univention-management-console-module-udm`
- **Build config:** none
- **Internal deps:** univention-management-console, univention-directory-manager-modules, univention-directory-reports, univention-lib
- **Python files:** `umc/python/udm/*.py` -> `univention.management.console.modules.udm`
- **Notes:** Slated for removal as a dependency. The REST API imports `udm_ldap` and `tools` from this.

---

## Internal dependency graph

```
univention-config-registry          (tier 2, leaf)
univention-debug-python             (tier 2, leaf, needs libunivention-debug)
  |
  v
univention-python                   (tier 2, depends on above two)
  |
  +---> univention-authorization    (tier 2 after adding setup.py)
  +---> univention-lib              (tier 2 after adding setup.py)
  |       |
  v       v
univention-directory-manager-modules (tier 2, all deps now tier 2!)
  |
  +---> univention-directory-reports           (tier 3, could be promoted)
  +---> univention-management-console          (tier 2, going away)
  |       |
  v       v
  univention-management-console-module-udm     (tier 3, going away)
```

**After promoting univention-lib and univention-authorization to tier 2**, the remaining
tier 3 packages are only the ones slated for removal (UMC + UMC-module-udm) plus
univention-directory-reports.

---

## Proposed build strategy

1. `apt-get install` system libs: libunivention-debug1, libsasl2-modules-oauthbearer, python3-samba, python3-ldb
2. `pip install` tier 1 PyPI packages (via pyproject.toml)
3. `pip install` tier 2 packages from source paths (in dependency order, or let pip resolve)
4. COPY tier 3 package Python files into dist-packages
5. COPY the REST API `src/` into dist-packages

---

## Near-term actions

- [ ] Add setup.py/pyproject.toml to `univention-lib` (promote to tier 2). Heavy deps (samba, ldb, Pillow) can be optional extras since the REST API only uses `i18n`.
- [ ] Add setup.py/pyproject.toml to `univention-authorization` (promote to tier 2). Trivial — 4 files, all deps already tier 1/2.
- [ ] After those two, univention-directory-manager-modules becomes cleanly pip-installable (all its deps are tier 2).

## Open questions

- [ ] Can univention-debug-python's setup.py build against libunivention-debug from apt, or does it need special paths?
- [ ] How much of univention-management-console is actually needed at runtime vs. just a few modules?
- [ ] Are python3-samba / python3-ldb actually needed by the REST API, or only by UDM modules that aren't used in this context?
- [ ] univention-admin-diary, univention-heimdal, univention-license — are these needed at runtime?
- [ ] univention-directory-reports — promote to tier 2 or will it go away with the UMC removal?
