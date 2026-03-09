# Extended Docs: Structured Data

Structured data files for UCS documentation purposes. This is **not** a Sphinx documentation project.

## Contents

- `ucr-deprecated.yaml` -- Registry of deprecated/removed UCR variables with commit hashes, variable names, and optional descriptions. Validated against `ucr-deprecated.schema.json`.
- `ucr-deprecated.schema.json` -- JSON Schema for the deprecated UCR variables file.

## Usage

When removing a UCR variable, add a new entry to `ucr-deprecated.yaml` with the commit hash, variable names, and an optional description.
