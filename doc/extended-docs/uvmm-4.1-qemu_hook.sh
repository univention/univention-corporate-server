#!/bin/sh
object="${1}"
operation="${2}"
sub_operation="${3}"
extra_argument="${4}"

SRC_BRIDGE="eth0"
DST_BRIDGE="br0"

convert_network () {
	xsltproc \
		--stringparam src_bridge "${SRC_BRIDGE}" \
		--stringparam dst_bridge "${DST_BRIDGE}" \
		"${0}.xsl" -
}

case "${operation}/${sub_operation}" in
prepare/begin) ;;
start/begin) ;;
started/begin) ;;
stopped/end) ;;
release/end) ;;
migrate/begin) convert_network ;;
restore/begin) convert_network ;;
reconnect/begin) ;;
attach/begin) ;;
*) echo "${0} ${*}" >&2 ;;
esac
