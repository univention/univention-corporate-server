#!/bin/bash

set -e

# shellcheck disable=SC1091
. scenarios/veyon/utils-veyon.sh

get_veyon_aws_instances table
