#!/bin/sh


CURDIR=$(pwd)
WEBMAILER_DIR=${CURDIR}/horde-webmailer

## directories for the upstream packages:
HORDE_SRCDIR=${CURDIR}/horde-upstream
KOLAB_SRCDIR=${CURDIR}/kolab-upstream
KOALB_WEBCLIENT=server/kolab-webclient

## substitutions for kolab template variables
horde_confdir=etc/horde/horde3
imp_confdir=etc/horde/imp4
dimp_confdir=etc/horde/dimp1
mimp_confdir=etc/horde/mimp1
ingo_confdir=etc/horde/ingo1
kronolith_confdir=etc/horde/kronolith2
mnemo_confdir=etc/horde/mnemo2
nag_confdir=etc/horde/nag2
turba_confdir=etc/horde/turba2
passwd_confdir=etc/horde/passwd	## svn/dev/branches/ucs-2.3/external/horde/sork-passwd
gollem_confdir=etc/horde/gollem	## svn/dev/branches/ucs-2.3/external/horde/gollem
#warning=
#horde_cookie_path=
#postfix_mydomain=
#base_dn=
#php_pw=
#fqdnhostname=
#local_addr=

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

  ## 3. apply kolab patches for it
  tar xf "${HORDE_SRCDIR}/${file}"

  cd ${pkgfullname} && {
  #patch -p1 -P 0
  QUILT_PATCHES=${KOLAB_SRCDIR}/${KOALB_WEBCLIENT}/${pkg}/patches/${pkg}-${version} quilt --quiltrc /dev/null push -a || test $? = 2
  cd ..
  mv ${pkgfullname} ${WEBMAILER_DIR}/${pkg}
  ## cleanup quilt patch dirs
  find ${WEBMAILER_DIR} -type d -name .pc -exec rm -rf {} \;

  ## 4. copy static Kolab config files and sub-files into target dirs
  for f in kolab-upstream/server/kolab-webclient/$pkg/configuration/*/*.php ; do
    filename="$(basename $f)"
    if [[ "$filename" =~ ^([[:digit:]]+-kolab)_([^_]+)_(.*.php) ]]; then
      cfgmultifile="${BASH_REMATCH[2]}"
	  subfile="${BASH_REMATCH[1]}_${BASH_REMATCH[3]}"
      targetdir="${WEBMAILER_DIR}/${pkg}/config/${cfgmultifile}.d/"
      mkdir -p "${targetdir}"
	  cp "$f" "${targetdir}/${subfile}"
    else
	  targetdir="${WEBMAILER_DIR}/${pkg}/config/"
	  mkdir -p "${targetdir}"
      cp "$f" "${targetdir}"
    fi
  done

  ## 5. fix special case for horde framework package
  if [ "${pkg}" == horde ]; then
	mv ${WEBMAILER_DIR}/horde/* ${WEBMAILER_DIR}
    rm -Rf ${WEBMAILER_DIR}/horde
  fi
  }

  ## 6. generate Config sub-files from Kolab Templates for manual inspection
  #for t in kolab-upstream/server/kolab-webclient/$pkg/templates/*/*.template ; do
  #  target="$(cat $t | sed -n '/KOLAB_META_START/,/KOLAB_META_END/ s/TARGET=\(.*\)/\1/p')"
  #  eval target=$(echo $target | sed -e 's/@@@\(.*\)@@@/$\1/')
  #  mkdir -p $(dirname kolab-templates/$target)
  #  cat $t | sed -n '/KOLAB_META_END/,$ p' | grep -v KOLAB_META_END > kolab-config/$target
  #done

done

