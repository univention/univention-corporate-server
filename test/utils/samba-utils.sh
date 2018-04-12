#!/bin/bash

set -x

function create_gpo {
    samba-tool gpo create $1 -U $2 --password=$3
}

function link_gpo_to_container {
    gpo=$(samba-tool gpo listall | grep $1 -B 1 | grep GPO | grep -oE "[^ ]+$")
    samba-tool gpo setlink $2 $gpo -U $3 --password=$4
}
