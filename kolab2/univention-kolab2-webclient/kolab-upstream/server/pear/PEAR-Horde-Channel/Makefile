STAGING = ../../stage

include ../../make-helper/kolab.mk

PACKAGE = PEAR-Horde-Channel
VERSION = $(shell grep "^Version:" *.spec | sed -e "s/^Version:\s*\([0-9.]*\).*/\1/")
RELEASE = $(shell grep "^Release:" *.spec | sed -e "s/^Release:\s*\([0-9]*\).*/\1/")

SOURCE_URL=
SOURCE_0=
EXTRA=pear.horde.org.xml

BUILD_OPTIONS=

include ../../make-helper/package.mk
include ../../make-helper/package-new.mk
include ../../make-helper/fetch.mk
