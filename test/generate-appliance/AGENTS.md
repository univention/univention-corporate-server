# test/generate-appliance/

Debian source package. Creates virtual appliance images for various virtualization systems from a single disk image.

## Binary packages

- **generate-appliance** -- Converts disk images into appliance formats (VMware, VirtualBox, KVM, etc.) using `qemu-utils` and `libguestfs`.

## Structure

- `generate_appliance/` -- Python package with the conversion logic.
- `setup.py`, `setup.cfg` -- Python packaging configuration.
- `debian/` -- Debian packaging files.
