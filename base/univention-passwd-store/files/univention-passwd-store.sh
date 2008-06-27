#! /bin/sh

set -e

# nothing to be done for root
if [ "$USER" = "root" ]; then 
    exit 0
fi

if [ -z "$PASSWD" ]; then
	exit 0
fi

PASSWDDIR="$HOME/.univention-passwd-store"
PASSWDFILE="$PASSWDDIR/session_passwd"

# prepare dir
test -d "$PASSWDDIR" || mkdir "$PASSWDDIR"
chown "$USER":nogroup "$PASSWDDIR"
chmod 0100 "$PASSWDDIR"

if [ -e "$PASSWDFILE"]; then
	rm -f "$PASSWDFILE"
fi

# prepare file
touch "$PASSWDFILE"
chown "$USER":nogroup "$PASSWDFILE"
chmod 0600 "$PASSWDFILE"

# store passwd
echo -n "$PASSWD" > "$PASSWDFILE"

# restrict access
chmod 0400 "$PASSWDFILE"

