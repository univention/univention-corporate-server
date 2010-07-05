#!/bin/sh

CURDIR=$(pwd)
WEBMAILER_DIR=${CURDIR}/horde-webmailer

## directories for the upstream packages:
HORDE_SRCDIR=${CURDIR}/horde-upstream
KOLAB_SRCDIR=${CURDIR}/kolab-upstream
KOALB_WEBCLIENT=server/kolab-webclient

## 1. checkout current kolab-webclient with patches for upstream horde packages

if [ -d "${KOLAB_SRCDIR}/${KOALB_WEBCLIENT}" ]; then
	cd "${KOLAB_SRCDIR}/${KOALB_WEBCLIENT}"
	cvs update -dP
	cd -
else
    export CVSROOT=':pserver:anonymous@intevation.de:/home/kroupware/jail/kolabrepository'
	cvs login
	cd "${KOLAB_SRCDIR}"
	cvs checkout -r HEAD ${KOALB_WEBCLIENT}
	cd -
fi

mkdir -p ${HORDE_SRCDIR}

package=( horde dimp imp ingo kronolith mimp mnemo nag turba ) # passwd is part of sork-passwd deb

for ((i=0; i<${#package[@]}; i++)); do
  ## 2. download upstream horde package
  pkg=${package[$i]}
  tmp=(`grep "%define         V_version" ${KOLAB_SRCDIR}/${KOALB_WEBCLIENT}/${pkg}/${pkg}.spec`)
  version=${tmp[2]}

  if [ "${pkg}" == horde ]; then
    pkgfullname=${pkg}-${version}
  else
    pkgfullname=${pkg}-h3-${version}
  fi
  file=${pkgfullname}.tar.gz

  [ -f "${HORDE_SRCDIR}/${file}" ] || wget -P ${HORDE_SRCDIR} http://ftp.horde.org/pub/${pkg}/${file}

done

# next run debian/prepare_horde-webmailer.sh , done in debian/rules
