# Errata Advisories

Errata advisory data for UCS releases. Contains YAML templates for errata entries and a JSON schema for validation. This is **not** a Sphinx documentation project.

## Contents

- `erratum.schema.json` -- JSON Schema for errata advisory files.
- `staging/` -- Templates (`0template.yaml`, `0security-template.yaml`) for new errata entries.

## Workflow

New errata advisories are created from the templates in `staging/`. Each entry specifies product, release, version scope, source package, fix, description, and bug references.
