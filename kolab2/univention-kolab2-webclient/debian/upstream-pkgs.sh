#!/bin/sh

PACKAGE_NAME=univention-kolab2-webclient
CURDIR="$(pwd)"
TARGET_DIR=${CURDIR}/kolab-php-lib

## directories for the upstream packages:
KOLAB_SRCDIR=kolab-upstream
KOLABPEAR=server/pear
# KOLABPHP=server/php-kolab

## 1. checkout current kolab pear and php-kolab packages

for d in ${KOLABPEAR} ${KOLABPHP}; do
	if [ -d "${KOLAB_SRCDIR}/${d}" ]; then
		cd "${KOLAB_SRCDIR}/${d}"
		cvs update -dP
		cd -
	else
		export CVSROOT=':pserver:anonymous@intevation.de:/home/kroupware/jail/kolabrepository'
		cd "${KOLAB_SRCDIR}"
		cvs login
		cvs checkout -r HEAD "${d}"
		cd -
	fi
done


mkdir -p ${TARGET_DIR}

# The Makefiles of the PEAR-Packages under server/pear use
# server/make-helper/pear.mk to generate a spec file from
# server/pear/pear.spec.template. Mainly two steps are described
# in the spec-template: 1. patching of the pear and php-kolab
# tarballs if patches are found and 2. installation via pear.
#
# The patch part is done below, resulting in a .with-kolab-patch.tgz
# tarball and the pear-Installation is done as part of the package
# build process in debian/rules

# unfortunately http://kolab.org/cgi-bin/viewcvs-kolab.cgi/server/pear/PEAR-Net_IMAP/ is currently empty
# but it is absolutely require_once'd in /usr/share/horde3/lib/Horde/Kolab/IMAP/pear.php
# Note that /usr/share/php/PEAR/Net/IMAP.php shipped by univention-kolab2-framework is not in the include_path
# Since currently univention-kolab2-webclient does not depend on univention-kolab2-framework, we have to
# ship it here
wget -P ${TARGET_DIR} http://download.pear.php.net/package/Net_IMAP-1.1.0.tgz
wget -P ${TARGET_DIR} http://download.pear.php.net/package/MDB2-2.4.1.tgz
wget -P ${TARGET_DIR} http://download.pear.php.net/package/MDB2_Driver_pgsql-1.4.1.tgz
wget -P ${TARGET_DIR} http://download.pear.php.net/package/MDB2_Schema-0.8.5.tgz
wget -P ${TARGET_DIR} http://download.pear.php.net/package/Net_DNS-1.0.1.tgz

# extract the kolab package name, upstream package name, version and URL from the PEAR info file
for pkginfo in ${KOLAB_SRCDIR}/${KOLABPEAR}/*/package.info; do
	## 2. look for kolab patches for the upstream package
	pkgdir=`dirname ${pkginfo}`

	# package.info parsing from from server/make-helper/pear.mk
	PEAR_PACKAGE=$(grep "^pear_package=" "${pkginfo}" | sed -e "s/pear_package='\([A-Za-z0-9\_-]*\)'\s*/\1/")
	PACKAGE=$(grep "^package=" "${pkginfo}" | sed -e "s/package='\([A-Za-z0-9\_-]*\)'\s*/\1/")
	VERSION=$(grep "^version=" "${pkginfo}" | sed -e "s/version='\([0-9.a-zA-Z]*\)'\s*/\1/")
	SOURCEURL=$(grep "^sourceurl=" "${pkginfo}" | sed -e "s/sourceurl='\(.*\)'$/\1/")

	pkgfullname=${PEAR_PACKAGE}-${VERSION}
	file=${pkgfullname}.tgz

	pkgpatchdir="${pkgdir}/patches/${PACKAGE}-${VERSION}/"
	patchlist="$(ls ${pkgpatchdir}/*.diff ${pkgpatchdir}/*.patch 2>/dev/null)"

	# skip the Horde_* and Kolab_* packages, they are included in horde-webmailer and/or kolab-framework
	if [[ "${PEAR_PACKAGE}" == Horde_* ]]; then
		if [ -n "${patchlist}" ]; then
			echo "WARNING: Please test the following patches which might be integrated into the horde-webmailer package: "
			echo "${patchlist}"
		fi
		continue
	fi
	if [[ "${PEAR_PACKAGE}" == Kolab_* ]]; then
		if [ -n "${patchlist}" ]; then
			echo "WARNING: Please test the following patches which might be integrated into the horde-webmailer package: "
			echo "${patchlist}"
		fi
		continue
	fi
	if [[ "${PEAR_PACKAGE}" == File ]]; then
		if [ -n "${patchlist}" ]; then
			echo "WARNING: Please test the following patches which might be integrated into the horde-webmailer package: "
			echo "${patchlist}"
		fi
		continue
	fi

	## 3. download upstream tarball and apply kolab patches if present
	if [ -z "${patchlist}" ]; then
		if ! [ -f "${TARGET_DIR}/${file}" ]; then
			wget -P ${TARGET_DIR} ${SOURCEURL}/${file}
		fi
	else
		outputfile=${pkgfullname}.with-kolab-patch.tgz
		rm "${TARGET_DIR}/${outputfile}"
		wget ${SOURCEURL}/${file}
		tar xf "${file}"
		if [ "${PEAR_PACKAGE}" == Date_Holidays -o "${PEAR_PACKAGE}" == Kolab_Storage ]; then
			# Workaround for broken patch prefix
			sed -i -e 's/md5sum="[^"]*"//' package.xml
			mv package.xml "${pkgfullname}"
		fi
		for patchfile in ${patchlist}; do
			patch -d "${pkgfullname}" -p3 < "${patchfile}" || exit 1
		done
		if [ "${PEAR_PACKAGE}" == Date_Holidays -o "${PEAR_PACKAGE}" == Kolab_Storage ]; then
			# Workaround for broken patch prefix
			mv "${pkgfullname}/package.xml" .
		fi
		tar czf "${TARGET_DIR}/${outputfile}" --remove-files "${pkgfullname}" package.xml
		rm "${file}"
	fi

done

## add the PEAR channels, moved to debian/rules
#D=${CURDIR}/debian/${PACKAGE_NAME}/
#php_dir=${D}/usr/share/horde3/lib
#for channelxml in PEAR-Horde-Channel/pear.horde.org.xml PEAR-PHPUnit-Channel/pear.phpunit.de.xml;
#do
#	pear_xml=${KOLABPEAR_SRCDIR}/${channelxml}
#	PHP_PEAR_PHP_BIN="php -d safe_mode=off"   \
#	pear -d php_dir=${php_dir} channel-add    ${pear_xml} || \
#	  echo "Channel already exists!" && sleep 1
#	pear -d php_dir=${php_dir} channel-update ${pear_xml} || \
#	  echo "Could not update channel pear.horde.org!" && sleep 1
#done
