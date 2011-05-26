#!/bin/sh
#
# Bug #17913: Test multifile handling
#
set -e

file_dir='/etc/univention/templates/files'
info_dir='/etc/univention/templates/info'

#####
cat >"${info_dir}/a.info" <<-EOF
Type: subfile
Multifile: tmp/agg
Subfile: tmp/a
EOF
mkdir -p "${file_dir}/tmp"
echo a >"${file_dir}/tmp/a"
univention-config-registry register a
test -z "$(dpkg-divert --list /tmp/agg)"
test ! -f /tmp/agg

#####
cat >"${info_dir}/b.info" <<-EOF
Type: multifile
Multifile: tmp/agg

Type: subfile
Multifile: tmp/agg
Subfile: tmp/b
EOF
mkdir -p "${file_dir}/tmp"
echo b >"${file_dir}/tmp/b"
univention-config-registry register b
test -n "$(dpkg-divert --list /tmp/agg)"
test -f /tmp/agg
grep -q '^a$' /tmp/agg
grep -q '^b$' /tmp/agg

#####
cat >"${info_dir}/c.info" <<-EOF
Type: multifile
Multifile: tmp/agg

Type: subfile
Multifile: tmp/agg
Subfile: tmp/c
EOF
mkdir -p "${file_dir}/tmp"
echo c >"${file_dir}/tmp/c"
univention-config-registry register c
test -n "$(dpkg-divert --list /tmp/agg)"
test -f /tmp/agg
grep -q '^a$' /tmp/agg
grep -q '^b$' /tmp/agg
grep -q '^c$' /tmp/agg

#####
univention-config-registry unregister c
mv "${info_dir}/c."{info,old}
test -n "$(dpkg-divert --list /tmp/agg)"
test -f /tmp/agg
grep -q '^a$' /tmp/agg
grep -q '^b$' /tmp/agg
! grep -q '^c$' /tmp/agg

#####
univention-config-registry unregister b
mv "${info_dir}/b."{info,old}
test -z "$(dpkg-divert --list /tmp/agg)"
test ! -f /tmp/agg

#####
cat >"${info_dir}/d.info" <<-EOF
Type: multifile
Multifile: tmp/agg
EOF
univention-config-registry register d
test -n "$(dpkg-divert --list /tmp/agg)"
test -f /tmp/agg
grep -q '^a$' /tmp/agg
! grep -q '^b$' /tmp/agg
! grep -q '^c$' /tmp/agg

#####
univention-config-registry unregister a
mv "${info_dir}/a."{info,old}
test -z "$(dpkg-divert --list /tmp/agg)"
test ! -f /tmp/agg

#####
univention-config-registry unregister d
mv "${info_dir}/d."{info,old}
test -z "$(dpkg-divert --list /tmp/agg)"
test ! -f /tmp/agg

#####
rm "${info_dir}/"[abcd].old
