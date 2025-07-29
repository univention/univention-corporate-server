#!/bin/bash

# Univention Mail Dovecot
# Mail quate warning script
#
# SPDX-FileCopyrightText: 2015-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

PERCENT=$1
USER=$2

MSG=$(ucr get mail/dovecot/quota/warning/text/$PERCENT)
SUBJECT=$(ucr get mail/dovecot/quota/warning/subject)

cat <<EOF | /usr/lib/dovecot/dovecot-lda -d $USER -o "plugin/quota=maildir:User quota:noenforcing"
From: postmaster@$(hostname -f)
To: $USER
Subject: $SUBJECT

${MSG/\$PERCENT/$PERCENT}
EOF
