SPEC_PRESENT = yes
include ../../make-helper/pear.mk

# Get the list of templates if there are any in the template directory
TEMPLATES = $(shell ls templates/$(PACKAGE)-$(VERSION)/*.template 2> /dev/null)

EXTRA = package.patch $(TEMPLATES)
