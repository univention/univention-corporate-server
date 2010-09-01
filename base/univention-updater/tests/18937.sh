#!/bin/bash
#
# univention-repository-updater kopiert pre- und postup.sh nicht
#

TMPDIR="$(mktemp -d)"
trap "rm -rf '$TMPDIR'" EXIT
REPODIR="$TMPDIR/apt"
mkdir "$REPODIR"
cd "$REPODIR"

declare -a DIRS
mkpdir () { # Create pool directory ${dir}
	declare -a versions parts archs
	while [ $# -ge 1 ]
	do
		case "${1}" in
			[1-9]*.[0-9]*-[0-9]*) versions+=("${1}") ;;
			[1-9]*.[0-9]*--sec[0-9]*) versions+=("${1}") ;;
			[1-9]*.[0-9]*--hotfixes) versions+=("${1}") ;;
			[1-9]*.[0-9]*--component/*) versions+=("${1}") ;;
			maintained|unmaintained) parts+=("${1}") ;;
			all|i386|amd64|extern) archs+=("${1}") ;;
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
	mkdir -p "${TMPDIR}/${name}-${version}/DEBIAN"
	cat <<-EOF >"${TMPDIR}/${name}-${version}/DEBIAN/control"
	Package: ${name}
	Version: ${version}
	Architecture: ${arch}
	Maintainer: UCS Test <test@univention.de>
	Installed-Size: 1
	Section: unknown
	Priority: optional
	Description: test
	EOF
	cat <<-EOF >"${TMPDIR}/${name}-${version}/DEBIAN/postinst"
	#!/bin/sh
	echo "${name}-${version}" >>"${TMPDIR}/install.log"
	${5}
	EOF
	chmod 755 "${TMPDIR}/${name}-${version}/DEBIAN/postinst"
	DEB="${TMPDIR}/${name}_${version}_${arch}.deb"
	dpkg-deb -b "${TMPDIR}/${name}-${version}" "${DEB}"
	[ -n "${dir}" ] && cp "${DEB}" "${dir}/"
}

mkpkg () { # Create Package files for ${1}. Optional arguments go to dpkg-scanpackages.
	local dir="${1:-${DIR}}"
	shift
	cd "${dir}/../.."
	dpkg-scanpackages "${@}" "${dir#${PWD}/}" /dev/null >"${dir}/Packages"
	gzip -n -9 <"${dir}/Packages" >"${dir}/Packages.gz"
	bzip2 -9 <"${dir}/Packages" >"${dir}/Packages.bz2"
	cd "${OLDPWD}"
}

mksh () { # Create shell scripts $@ in $1
	local dir="${1}"
	shift
	while [ $# -ge 1 ]
	do
		cat <<-EOF >"${dir}/${1}.sh"
		#!/bin/sh
		echo "${dir}/${1}.sh ${RANDOM}" >>"${TMPDIR}/install.log"
		EOF
		chmod 755 "${dir}/${1}.sh"
		shift
	done
}

declare -i v
for ver in 2.0-{0,1,2,-sec{1,2,3,4,5,6,7}} 2.1-{0,1,2,-sec{1,2,3,4}} 2.2-{0,1,2,3,-sec{1,2,3,4,5}} 2.3-{0,1,2,-sec{1,2,3,4}}
do
  for arch in amd64 i386 extern all
  do
    mkpdir "$ver" maintained "$arch"
    mkdeb test "$v" i386
    mkpkg "$DIR"
    v+=1
  done
  mksh "$DIR" preup postup
done

rm -rf /var/lib/univention-repository/{.univention_install,var,skel,mirror}

invoke-rc.d apache2 stop
python -m SimpleHTTPServer 80 2>"$TMPDIR/http.log" &
pid=$!
ucr set repository/mirror/server=localhost
ucr unset repository/mirror/version/end
univention-repository-update net

declare -i rc=0
error () {
	rc+=1
	echo "E: $@" >&2
}

for sh in $(find -not -path \*/sec\* -name p\*up.sh)
do
	cmp "$sh" "/var/lib/univention-repository/mirror/$sh" || error "$sh"
done
[ . = "$(readlink /var/lib/univention-repository/mirror/univention-repository)" ] || error "$(ls -l /var/lib/univention-repository/mirror)"

kill -INT "$pid"
invoke-rc.d apache2 start

exit "$rc"
