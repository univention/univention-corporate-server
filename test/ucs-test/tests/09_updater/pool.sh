# vim:set ft=sh:
#
# Common library function for updater test
# 1. All modifications done though "ucr" are automatically undone on exit
# 2. Extra files for apache should be symlinked from ${BASEDIR}, which are removed on exit
#
eval "$(univention-config-registry shell | sed -e 's/^/declare -r _/')"
declare -i major="${_version_version%.*}"
declare -i minor="${_version_version#*.}"
pkgname="test-$$-${RANDOM}"
repoprefix="univention-repository"
ARCH=$(dpkg-architecture -qDEB_HOST_ARCH 2>/dev/null)

# if UT_VERBOSE is set, output messages to STDERR, otherwise /dev/null
case "${UT_VERBOSE-}" in
	/?*|./?*)
		exec 3>&2 4>"${UT_VERBOSE}.$$"
		PS4='+${BASH_SOURCE}:${LINENO}:${FUNCNAME[0]}: '
		BASH_XTRACEFD=4
		set -x
		;;
	"") exec 3>/dev/null ;;
	?*) exec 3>&2 ;;
esac

unset TMPDIR # Unset user-defines base-directroy for mktemp
BASEDIR="$(mktemp -d)"
echo "BASEDIR=\"${BASEDIR}\"" >&3
# Need to be accessible by apache2, otherwise 403 FORBIDDEN
chmod 755 "${BASEDIR}"
# Make a backup
cp /etc/univention/base*.conf "${BASEDIR}/"
cp /etc/apt/trusted.gpg "${BASEDIR}/trusted.gpg"

# Wrap univention-config-registry to later undo any changes
declare -a _reset=(version/version version/patchlevel version/erratalevel)
ucr () { # (get|set|unset) name[=value]...
	local mode="${1}"
	case "${mode}" in
		set|unset)
			shift
			local name_value
			for name_value in "$@"
			do
				_reset+=("${name_value%%=*}")
			done
			univention-config-registry "${mode}" "$@" >&3 2>&3
			;;
		*)
			univention-config-registry "$@"
			;;
	esac
}

cleanup () { # Undo all changes
	set +e +x
	trap - EXIT

	[ -f "${BASEDIR}/reenable_mirror" ] && a2ensite univention-repository >&3 2>&3
	find -P /etc/apache2 -lname "${BASEDIR}/*" -exec rm -f {} +
	apache2ctl graceful >&3 2>&3

	declare -a reset remove
	local name sname
	for name in "${_reset[@]}"
	do
		local sname="_${name//\//_}"
		if [ -n "${!sname}" ]
		then
			reset+=("${name}"="${!sname}")
		else
			remove+=("${name}")
		fi
	done
	[ -n "${remove}" ] && univention-config-registry unset "${remove[@]}" >&3 2>&3
	[ -n "${reset}" ] && univention-config-registry set "${reset[@]}" >&3 2>&3
	cp "${BASEDIR}"/base*.conf /etc/univention/
	cp "${BASEDIR}/trusted.gpg" /etc/apt/trusted.gpg

	[ -x /etc/init.d/cron ] && [ -f "${BASEDIR}/reenable_cron" ] && invoke-rc.d cron start >&3 2>&3 3>&-

	rm -rf "${BASEDIR}"
	echo "=== RESULT: ${RETVAL} ==="
}
trap cleanup EXIT
failure () { # Report failed command
	set +e +x
	trap - ERR
	[ ${BASH_SUBSHELL} -eq 0 ] && return 0 # do not exit the controlling shell

	echo "**************** Test failed above this line ****************" >&2
	echo "ERROR ${0}:${BASH_LINENO[@]}" >&2
	echo "ERROR ${BASH_COMMAND}" >&2
	sleep ${UT_DELAY:-0}
	exit ${RETVAL:-140} # internal error
}
trap 'failure ${LINENO}' ERR
set -E # functions inherit ERR

setup_apache () { # Setup apache for repository [--port ${port}] [${prefix}]
	local hostname=localhost
	if [ "${1}" = "--port" ]
	then
		local port="${2}"
		local listen="Listen ${port}"
		shift 2
	fi
	REPOPREFIX="${1}"
	REPODIR="${BASEDIR}${REPOPREFIX:+/${REPOPREFIX#/}}"
	[ -n "${REPOPREFIX}" ] && local alias="Alias /${REPOPREFIX} ${REPODIR}"
	cat <<-EOF >"${BASEDIR}/apache2.conf"
	${listen}
	<VirtualHost ${hostname}${port:+:${port}}>
	DocumentRoot ${BASEDIR}
	${alias}
	<Directory ${REPODIR}>
			   AllowOverride All
			   Options +Indexes
			   order allow,deny
			   allow from all
	</Directory>
	</VirtualHost>
	EOF
	ln -s "${BASEDIR}/apache2.conf" /etc/apache2/sites-enabled/univention-repository.$$
	mkdir -p "${REPODIR}"
	if test -f /etc/apache2/sites-enabled/univention-repository
	then
		touch "${BASEDIR}/reenable_mirror"
		a2dissite univention-repository >&3 2>&3
	fi
	apache2ctl graceful >&3 2>&3
}

config_repo () { # Configure use of repository from local apache
	local server=localhost
	local port=80
	local prefix="${REPOPREFIX}"
	declare -a extra
	while [ $# -ge 1 ]
	do
		case "${1}" in
			/*) prefix="${1#/}" ;;
			:[1-9]*) port="${1#:}" ;;
			?*=*) extra+=("${1}") ;;
			*:[1-9]*) server="${1%:*}" ; port="${1##*:}" ;;
			*) server="${1}" ;;
		esac
		shift
	done
	if [ -x /etc/init.d/cron ] && pidof cron >/dev/null
	then
		touch "${BASEDIR}/reenable_cron"
		invoke-rc.d cron stop
	fi
	ucr set \
		local/repository=no \
		repository/mirror=no \
		repository/online=yes \
		repository/online/server="${server}" \
		repository/online/port="${port}" \
		repository/online/prefix="${prefix}" \
		"${extra[@]}" >&3 2>&3
	ucr commit /etc/apt/sources.list.d/*.list >&3 2>&3
	ucr set update/available= >&3 2>&3
}

config_mirror () { # Configure mirror to use repository from local apache
	local server=localhost
	local port=80
	local prefix="${REPOPREFIX}"
	local mirror="${BASEDIR}/mirror"
	declare -a extra
	while [ $# -ge 1 ]
	do
		case "${1}" in
			/*) prefix="${1#/}" ;;
			:[1-9]*) port="${1#:}" ;;
			?*=*) extra+=("${1}") ;;
			*:[1-9]*) server="${1%:*}" ; port="${1##*:}" ;;
			*) server="${1}" ;;
		esac
		shift
	done
	mkdir -p "${mirror}"
	if [ -x /etc/init.d/cron ] && pidof cron >/dev/null
	then
		touch "${BASEDIR}/reenable_cron"
		invoke-rc.d cron stop
	fi
	ucr set \
		local/repository=yes \
		repository/online=no \
		repository/mirror=yes \
		repository/mirror/basepath="${mirror}" \
		repository/mirror/server="${server}" \
		repository/mirror/port="${port}" \
		repository/mirror/prefix="${prefix}" \
		"${extra[@]}" >&3 2>&3
	ucr commit /etc/apt/mirror.list >&3 2>&3
}

allpatchlevels () { # All ${major}.${minor}-0 ... ${major}.${minor}-${patchlevel}
	set -- ${1//[.-]/ }
	declare -i patchlevel
	for ((patchlevel=0; patchlevel<=${3}; patchlevel+=1))
	do
		echo "${1}.${2}-${patchlevel}"
	done
}

allminors () { # All ${major}.0-0 ... ${major}.${minor}-0 ... ${major}.${minor}-${patchlevel}
	set -- ${1//[.-]/ }
	declare -i minor
	for ((minor=0; minor<=${2}; minor+=1))
	do
		echo "${1}.${minor}-0"
	done
	allpatchlevels "${1}.${2}-${3}"
}

declare -a DIRS
mkpdir () { # Create pool directory ${dir}
	declare -a versions parts archs
	while [ $# -ge 1 ]
	do
		case "${1}" in
			[1-9]*.[0-9]*-[0-9]*) versions+=("${1}") ;;
			[1-9]*.[0-9]*--errata[0-9]*) versions+=("${1}") ;;
			[1-9]*.[0-9]*--hotfixes) versions+=("${1}") ;;
			[1-9]*.[0-9]*--component/*) versions+=("${1}") ;;
			maintained|unmaintained) parts+=("${1}") ;;
			all|i386|amd64) archs+=("${1}") ;;
			extern|*--sec*) echo "Deprecated ${1}" >&2 ; return 2 ;;
			*) echo "Unknown ${1}" >&2 ; return 2 ;;
		esac
		shift
	done
	local version part arch
	for version in "${versions[@]}"
	do
		for part in "${parts[@]}"
		do
			for arch in "${archs[@]}"
			do
				DIR="${REPODIR}/${version%%-*}/${part}/${version#*--}/${arch}"
				DIRS+=("${DIR}")
				mkdir -p "${DIR}"
				touch "${DIR}/Packages"
			done
		done
	done
	return 0
}

mkdeb () { # Create dummy package [name [version [arch [dir [postinst]]]]]
	local name="${1:-test}"
	local version="${2:-1}"
	local arch="${3:-all}"
	local dir="${4:-${DIR}}"
	mkdir -p "${BASEDIR}/${name}-${version}/DEBIAN"
	cat <<-EOF >"${BASEDIR}/${name}-${version}/DEBIAN/control"
	Package: ${name}
	Version: ${version}
	Architecture: ${arch}
	Maintainer: UCS Test <test@univention.de>
	Installed-Size: 1
	Section: unknown
	Priority: optional
	Description: test $0
	EOF
	cat <<-EOF >"${BASEDIR}/${name}-${version}/DEBIAN/postinst"
	#!/bin/sh
	echo "${name}-${version}" >>"${BASEDIR}/install.log"
	${5}
	EOF
	chmod 755 "${BASEDIR}/${name}-${version}/DEBIAN/postinst"
	DEB="${BASEDIR}/${name}_${version}_${arch}.deb"
	dpkg-deb -b "${BASEDIR}/${name}-${version}" "${DEB}" >&3 2>&3
	[ -z "${dir}" ] || cp "${DEB}" "${dir}/"
}

mkdsc () { # Create dummy source package [name [version [arch [dir]]]]
	local name="${1:-test}"
	local version="${2:-1}"
	local arch="${3:-all}"
	local dir="${4:-${DIR}}"
	mkdir -p "${BASEDIR}/${name}-${version}/debian"
	cat <<-EOF >"${BASEDIR}/${name}-${version}/debian/changelog"
	${pkgname} (${version}) unstable; urgency=low

	  * ucs-test $0

	 -- Univention GmbH <packages@univention.de>  $(date -R)
	EOF
	cat <<-EOF >"${BASEDIR}/${name}-${version}/debian/control"
	Source: ${pkgname}
	Maintainer: Univention GmbH <packages@univention.de>
	Standards-Version: 3.6.1

	Package: ${pkgname}
	Architecture: ${ARCH}
	EOF
	cat <<-EOF >"${BASEDIR}/${name}-${version}/debian/rules"
	#!/usr/bin/make -f
	clean build binary-indep binary-arch binary: true
	EOF
	: >"${BASEDIR}/${name}-${version}/debian/copyright"
	(cd "${BASEDIR}" && dpkg-source -b "${pkgname}-${version}") >&3 2>&3
	TGZ="${BASEDIR}/${name}_${version}.tar.gz"
	DSC="${BASEDIR}/${name}_${version}.dsc"
	if mkgpg
	then
		gpgsign "${DSC}"
	fi
	[ -z "${dir}" ] || mv "${DSC}" "${TGZ}" "${dir}/"
}

mkpkg () { # Create Package files for ${1}. Optional arguments go to dpkg-scanpackages.
	local dir="${1:-${DIR}}"
	shift
	cd "${dir}/../.."
	local subdir="${dir#${PWD}/}"
	dpkg-scanpackages "${@}" "${subdir}" > "${dir}/Packages" 2>&3
	gzip -n -9 <"${dir}/Packages" >"${dir}/Packages.gz"
	bzip2 -9 <"${dir}/Packages" >"${dir}/Packages.bz2"
	cd "${OLDPWD}"

	case "${_update_secure_apt}" in
		0|false|no|off) return 0 ;;
	esac
	mkgpg
	cd "${dir}"
	rm -f Release Release.tmp Release.gpg
	apt-ftparchive \
		-o "APT::FTPArchive::Release::Origin=Univention" \
		-o "APT::FTPArchive::Release::Label=Univention" \
		-o "APT::FTPArchive::Release::Version=${subdir%%/*}" \
		-o "APT::FTPArchive::Release::Codename=${subdir}" \
		release . >Release.tmp 2>&3
	mv Release.tmp Release

	gpgsign Release
	cd "${OLDPWD}"
}

gpgsign () { # sign file
	mkgpg
	local out sign
	case "${1:-}" in
	Release|*.sh)
		sign=--detach-sign
		out="${1}.gpg"
		cp "$1" "${GPG_DIR}/in"
		;;
	""|-)
		sign=--detach-sign
		out="$2"
		cat "$1" >"${GPG_DIR}/in"
		;;
	*.dsc)
		sign=--clearsign
		out="${1}"
		(cat "$1" && echo "") >"${GPG_DIR}/in"
		;;
	*)
		echo "Failed to sign '${1}'" >&2
		return 1
		;;
	esac
	rm -f "${GPG_DIR}/out"
	chroot "${GPG_DIR}" "${GPG_BIN}" \
		--batch \
		--keyring "${GPGPUB#${GPG_DIR}}" \
		--secret-keyring "${GPGSEC#${GPG_DIR}}" \
		--armor \
		--default-key "${GPGID}" \
		"${sign}" \
		--output out in
	cp "${GPG_DIR}/out" "${out}"
}

mksrc () { # Create Sources files for ${1}. Optional arguments go to dpkg-scansources.
	local dir="${1:-${DIR}}"
	shift
	cd "${dir}/../.."
	local subdir="${dir#${PWD}/}"
	dpkg-scansources "${@}" "${subdir}" > "${dir}/Sources" 2>&3
	gzip -n -9 <"${dir}/Sources" >"${dir}/Sources.gz"
	bzip2 -9 <"${dir}/Sources" >"${dir}/Sources.bz2"
	cd "${OLDPWD}"

	case "${_update_secure_apt}" in
		0|false|no|off) return 0 ;;
	esac
	mkgpg
	cd "${dir}"
	rm -f Release Release.tmp Release.gpg
	apt-ftparchive \
		-o "APT::FTPArchive::Release::Origin=Univention" \
		-o "APT::FTPArchive::Release::Label=Univention" \
		-o "APT::FTPArchive::Release::Version=${subdir%%/*}" \
		-o "APT::FTPArchive::Release::Codename=${subdir}" \
		release . >Release.tmp 2>&3
	mv Release.tmp Release

	gpgsign Release
	cd "${OLDPWD}"
}

mkgpg () { # Create GPG-key for secure APT
	GPG_BIN=/usr/bin/gpg
	GPG_DIR="${BASEDIR}/gpg.chroot"
	mkdir -p "${GPG_DIR}${HOME}/.gnupg"
	# Non-blocking GnuPG using /dev/_u_random
	(
		echo "${GPG_BIN}"
		ldd "${GPG_BIN}" | grep --only '/\S\+'
		echo /dev/urandom
	) | cpio --pass-through --make-directories --dereference "${GPG_DIR}"
	ln -s urandom "${GPG_DIR}/dev/random"
	GPGREQ="${GPG_DIR}/test.req"
	cat <<-EOF >"${GPGREQ}"
	Key-Type: DSA
	Key-Length: 1024
	Name-Real: ucs-test-key
	Name-Comment: internal only
	Name-Email: ucs-test@univention.de
	Expire-Date: 1d
	%pubring test.pub
	%secring test.sec
	%commit
	EOF
	GPGSTATUS="${GPG_DIR}/test.status"
	chroot "${GPG_DIR}" "${GPG_BIN}" --batch --status-fd 3 --gen-key "${GPGREQ#${GPG_DIR}}" 3>"${GPGSTATUS}"
	GPGID=$(sed -ne 's/^\[GNUPG:\] KEY_CREATED P //p' "${GPGSTATUS}")
	GPGPUB="${GPG_DIR}/test.pub"
	GPGSEC="${GPG_DIR}/test.sec"
	apt-key add "${GPGPUB}"
	mkgpg () { true; }
	return 0
}

mksh () { # Create shell scripts $@ in $1
	local dir="${1}" ret='$?'
	shift
	while [ $# -ge 1 ]
	do
		case "${1}" in
		--return) ret="${2}" ; shift 2 ;;
		esac
		cat <<-EOF >"${dir}/${1}.sh"
		#!/bin/sh
		echo "${dir}/${1}.sh ${RANDOM}" "\$@" >>"${BASEDIR}/install.log"
		exit ${ret}
		EOF
		chmod 755 "${dir}/${1}.sh"
		case "${_repository_online_verify}" in
			0|false|no|off) return 0 ;;
		esac
		if mkgpg
		then
			gpgsign "${dir}/${1}.sh"
		fi
		shift
	done
}

split_repo_path () { # Split repository path into atoms
	local oldifs="${IFS}"
	local IFS=/
	set -- ${1#${REPODIR}/}
	IFS="${oldifs}"
	local version part arch
	version="${1}"
	part="${2}"
	case "${3}" in
		"${version}-"[0-9]*) version="${3}" ;;
		errata*) version="${version}--${3}" ;;
		hotfixes) version="${version}--hotfixes" ;;
		component) version="${version}--component/${4}" ; shift ;;
		*) echo "Unknown ${3}" >&2 ; return 2 ;;
	esac
	arch="${4}"
	echo "${version}" "${part}" "${arch}"
}

checkapt () { # Check for apt-source statement ${1}
	local files=/etc/apt/sources.list.d/*.list
	local prefix=deb
	local pattern
	while [ $# -ge 1 ]
	do
		case "${1}" in
			--mirror) files=/etc/apt/mirror.list && shift ; continue ;;
			--source|source) prefix=deb-src && shift ; continue ;;
			http*) pattern="^${prefix} ${1}" ;;
			[1-9]*.[0-9]*-[0-9]*) pattern="^${prefix} .*/${1%-*}/.* ${1}/.*/$" ;;
			[1-9]*.[0-9]*--errata[0-9]*) pattern="^${prefix} .*/${1%%-*}/.* ${1#*--}/.*/" ;;
			[1-9]*.[0-9]*--hotfixes) pattern="^${prefix} .*/${1%%-*}/.* hotfixes/.*/" ;;
			[1-9]*.[0-9]*--component/*) pattern="^${prefix} .*/${1%%-*}/.*/component/\? ${1#*--component/}/.*/" ;;
			maintained|unmaintained) pattern="^${prefix} .*/${1}/\(component/\?\)\? .*/.*/" ;;
			all|${ARCH}|extern) pattern="^${prefix} .*/\(component/\?\)\? .*/${1}/" ;;
			i386|amd64) shift ; continue ;;
			/*) set -- "$@" $(split_repo_path "${1}") && shift ; continue ;;
			*) echo "Unknown ${1}" >&2 ; return 2 ;;
		esac
		if ! grep -q "${pattern}" ${files}
		then
			echo "Failed '${pattern}'" >&2
			grep -v '^#\|^[[:space:]]*$' ${files} >&2
			return 1
		fi
		shift
	done
}

checkdeb () { # Check is package was installed in versions $@
	local pkgname="${1}"
	while [ $# -gt 1 ]
	do
		shift
		if ! grep -Fqx "${pkgname}-${1}" "${BASEDIR}/install.log"
		then
			echo "Failed ${pkgname}-${1}" >&2
			cat "${BASEDIR}/install.log" >&2
			return 1
		fi
	done
}

checkmirror () { # Check mirror for completeness: required-dirs... -- forbidden-dirs...
	local srcdir="${REPODIR}"
	local dstdir="${BASEDIR}/mirror"
	local skeldir="${dstdir}/skel/${REPOPREFIX}"
	local port=80

	# Symlink
	test $(readlink "${dstdir}/mirror/univention-repository") = .

	# Directories
	local invert
	while [ $# -ge 1 ]
	do
		if [ "${1}" = -- ]
		then
			invert=!
		else
			test ${invert} -d "${dstdir}/mirror/${1#${srcdir}/}" || return 1
		fi
		shift
	done

	# Mirrored files
	local cmd uri dist
	while read cmd uri dist
	do
		[ "${cmd}" = deb ] || continue
		[[ "${uri}" =~ 'http://localhost'(":${port}")?"/${REPOPREFIX}/"(.*) ]] || continue
		local prefix="${BASH_REMATCH[2]}"
		cmp "${srcdir}/${prefix}/${dist}/Packages" "${skeldir}/${prefix}/${dist}/Packages"
		cmp "${srcdir}/${prefix}/${dist}/Packages.gz" "${skeldir}/${prefix}/${dist}/Packages.gz"
		test -s "${dstdir}/mirror/${prefix}/${dist}/Packages" || return 1
		test -s "${dstdir}/mirror/${prefix}/${dist}/Packages.gz" || return 1

		local oldifs="${IFS}"
		local IFS=$'\n'
		set -- $(cd "${srcdir}" && find "${prefix}/${dist}" -name \*.deb -o -name \*.sh)
		IFS="${oldifs}"
		while [ $# -ge 1 ]
		do
			cmp "${srcdir}/${1}" "${dstdir}/mirror/${1}" || return 1
			shift
		done
	done </etc/apt/mirror.list
}
