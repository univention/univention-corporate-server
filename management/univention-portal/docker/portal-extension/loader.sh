#!/bin/sh
# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2024 Univention GmbH

set -eu

echo "Copying the plugins into the target"
for source in /plugins/*
do
    plugin_type=$(basename "${source}")
    target="/target/${plugin_type}"
    if [ -d "${target}" ]
    then
        echo "COPY - Plugin type ${plugin_type} in /target, copying files."
        cp -av "${source}" /target
    else
        echo "SKIP - Plugin type ${plugin_type} not in /target, skipping."
    fi
done
