#!/bin/sh

CURDIR="$(pwd)"
D=${CURDIR}/debian/horde-webmailer/
HORDESHARE=/usr/share/horde3
HORDE_SRCDIR=debian/horde-src

QUILT_PATCH_OPTS="-p2 -d ${D}/${HORDESHARE}" QUILT_PATCHES=${CURDIR}/debian/patches quilt --leave-rejects --quiltrc /dev/null push -a || test $? = 2


