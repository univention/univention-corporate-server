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
mkdir -p ${WEBMAILER_DIR}

package=( horde dimp imp ingo kronolith mimp mnemo nag passwd turba )

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

  ## 3. apply kolab patches for it
  tar xf "${HORDE_SRCDIR}/${file}"

  cd ${pkgfullname} && {
  #patch -p1 -P 0
  QUILT_PATCHES=${KOLAB_SRCDIR}/${KOALB_WEBCLIENT}/${pkg}/patches/${pkg}-${version} quilt --quiltrc /dev/null push -a || test $? = 2
  cd ..
  mv ${pkgfullname} ${WEBMAILER_DIR}/${pkg}
  if [ "${pkg}" == horde ]; then
	mv ${WEBMAILER_DIR}/horde/* ${WEBMAILER_DIR}
    rm -Rf ${WEBMAILER_DIR}/horde
  fi
  }

  ## 4. generate Demo Config files from Kolab Templates with hooks for UCS Templates
  # run kolabconf to commit templates http://packages.debian.org/de/sid/libkolab-perl

done


