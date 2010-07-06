#!/bin/sh

CURDIR=$(pwd)
WEBMAILER_DIR=${CURDIR}/horde-webmail

## directories for the upstream packages:
HORDE_SRCDIR=${CURDIR}/horde-upstream
KOLAB_SRCDIR=${CURDIR}/kolab-upstream
KOALB_WEBCLIENT=server/kolab-webclient

## substitutions for kolab template variables
#horde_confdir=etc/horde/horde3
#imp_confdir=etc/horde/imp4
#dimp_confdir=etc/horde/dimp1
#mimp_confdir=etc/horde/mimp1
#ingo_confdir=etc/horde/ingo1
#kronolith_confdir=etc/horde/kronolith2
#mnemo_confdir=etc/horde/mnemo2
#nag_confdir=etc/horde/nag2
#turba_confdir=etc/horde/turba2
#passwd_confdir=etc/horde/passwd	## svn/dev/branches/ucs-2.3/external/horde/sork-passwd
#gollem_confdir=etc/horde/gollem	## svn/dev/branches/ucs-2.3/external/horde/gollem
#warning=
#horde_cookie_path=
#postfix_mydomain=
#base_dn=
#php_pw=
#fqdnhostname=
#local_addr=

## Step 1. and 2. (copying the kolab and horde upstream packages) can be done manually by
## calling debian/upstream-pkgs.sh

mkdir -p ${WEBMAILER_DIR}

package=( horde dimp imp ingo kronolith mimp mnemo nag turba ) # passwd is part of sork-passwd deb

for ((i=0; i<${#package[@]}; i++)); do
  pkg=${package[$i]}
  tmp=(`grep "%define         V_version" ${KOLAB_SRCDIR}/${KOALB_WEBCLIENT}/${pkg}/${pkg}.spec`)
  version=${tmp[2]}

  if [ "${pkg}" == horde ]; then
    pkgfullname=${pkg}-${version}
  else
    pkgfullname=${pkg}-h3-${version}
  fi
  file=${pkgfullname}.tar.gz
 
  ## 3. apply kolab patches for it
  tar xf "${HORDE_SRCDIR}/${file}"
  
  cd ${pkgfullname} && {
  #patch -p1 -P 0
  QUILT_PATCHES=${KOLAB_SRCDIR}/${KOALB_WEBCLIENT}/${pkg}/patches/${pkg}-${version} quilt --quiltrc /dev/null push -a || test $? = 2
  cd ..
  mv ${pkgfullname} ${WEBMAILER_DIR}/${pkg}
  ## cleanup quilt patch dirs
  find ${WEBMAILER_DIR} -type d -name .pc | xargs -r rm -rf
  
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
  
  # copy php.dist files where necessary
  for f in "${WEBMAILER_DIR}/${pkg}"/config/*.php.dist; do
    targetfilename="$(basename $f .dist)"
    target="${WEBMAILER_DIR}/${pkg}/config/$targetfilename"
    if ! [ -f "$target" ]; then
	  cp $f $target
	  if [ "$targetfilename" == "prefs.php" ]; then
	    # patch the relative into an absolute path, necessary for the /etc/horde setup
        sed -i "s|^require_once dirname(__FILE__) . '/../lib/\(.*\)';|require_once '/usr/share/horde3/${pkg}/lib/\1';|" "$target"
	  fi
	fi
  done

  # Hook templates not considered yet : hooks/horde-3.3.6/hook-delete_webmail_user.php
  
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
