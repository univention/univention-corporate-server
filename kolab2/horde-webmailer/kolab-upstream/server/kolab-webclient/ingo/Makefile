STAGING = ../../stage

include ../../make-helper/kolab.mk

SOURCE_URL=http://ftp.horde.org/pub/$(PACKAGE)
SOURCE_0 ?= $(PACKAGE)-h3-$(VERSION).$(SOURCE_FORMAT)

include ../../make-helper/package.mk
include ../../make-helper/patch-series.mk

# Get the list of templates if there are any in the template directory
TEMPLATES = $(shell ls templates/$(PACKAGE)-$(VERSION)/*.template 2> /dev/null)

# Get the list of configuration files if there are any in the configuration directory
CONFIGURATION = $(shell ls configuration/$(PACKAGE)-$(VERSION)/*.php 2> /dev/null)

EXTRA = package.patch $(TEMPLATES) $(CONFIGURATION)

include ../../make-helper/package-new.mk
include ../../make-helper/fetch.mk
