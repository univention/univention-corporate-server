#!/bin/bash

set -e

# shellcheck disable=SC1091
. scenarios/veyon/utils-veyon.sh

destroy_veyon_aws_instances
