#!/bin/bash

set -e -x

# shellcheck source=lib.sh
. product-tests/umc/lib.sh

run_umc_tests
