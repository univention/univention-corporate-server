#!/bin/sh
SRC=${1:-$(dirname "$0")/../src}
set -x
"${SRC}/univention-virtual-machine-manager"
"${SRC}/univention-virtual-machine-manager" --help
"${SRC}/univention-virtual-machine-manager" nodes
"${SRC}/univention-virtual-machine-manager" nodes --help
"${SRC}/univention-virtual-machine-manager" error
"${SRC}/univention-virtual-machine-manager" error --help
[ -e "${SRC}/uvmm" ] || ln -s univention-virtual-machine-manager "${SRC}/uvmm"
"${SRC}/uvmm"
"${SRC}/uvmm" --help
"${SRC}/uvmm" nodes
"${SRC}/uvmm" nodes --help
"${SRC}/uvmm" error
"${SRC}/uvmm" error --help
[ -e "${SRC}/uvmm-nodes" ] || ln -s univention-virtual-machine-manager "${SRC}/vmm-nodes"
"${SRC}/uvmm-nodes"
"${SRC}/uvmm-nodes" --help
