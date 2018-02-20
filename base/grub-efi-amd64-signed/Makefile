#!/usr/bin/make -f

ALL := gcdx64.efi.signed grubx64.efi.signed
ARCH := x86_64-efi

# For sbsign:
#KEY := shim.rsa
#CERT := shim.pem

# For pesign:
#TOKEN := Univention GmbH
#CERT := # Univention 2014

GRUBDIR := /usr/lib/grub/$(ARCH)
MODULE_FILES := $(wildcard $(GRUBDIR)/*.mod)
MODULE_NAMES := $(basename $(notdir $(MODULE_FILES)))
MODULES_SKIP := linux cb%
MODULES_gcdx64 := $(filter-out $(MODULES_SKIP),$(MODULE_NAMES))
MODULES_grubx64 := $(shell cat grubx64.lst)

.PHONY: all
all: $(ALL)

%.efi.signed: %.efi
ifneq ($(TOKEN),)
	pesign --sign --in "$<" --force --out "$@" --nss-token "$(TOKEN)" --certficate "$(CERT)" --verbose
else ifneq ($(KEY),)
	sbsign --key "$(KEY)" --cert "$(CERT)" --output "$@" "$<"
endif

%.efi: %.cfg
	grub-mkimage -d "$(GRUBDIR)" -o "$@" -O "$(ARCH)" -c "$<" -p /efi/boot $(MODULES_$*)

.PHONY: clean
clean::
	$(RM) $(ALL:.signed=)

.PHONY: maintainerclean
maintainerclean:: clean
	$(RM) $(ALL)
