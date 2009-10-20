#!/bin/sh
for widget in $(grep "dojo.require" ../univention-webui/webui/includes/* | sed -n 's/.*dojo.require(\\\?"\(.[^\\]*\)\\\?").*/\1/gp' | sort | uniq); do echo \"$widget\",; done
