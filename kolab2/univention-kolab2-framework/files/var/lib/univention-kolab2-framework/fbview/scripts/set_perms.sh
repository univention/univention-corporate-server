#!/bin/sh
#
# set_perms.sh - Jon Parise <jon@csh.rit.edu>
#
# $Horde: horde/scripts/set_perms.sh,v 1.7 2001/04/15 01:55:32 chuck Exp $

# "Dangerous" PHP scripts
#
DANGEROUS_FILES="test.php"

# Default non-web server user who will own the tree.
#
OWNER=root

# Introductory text
#
cat << EOF

This script will set the permissions on your Horde
tree so that the files will be accessible by the web
server.

You can cancel this script at any time using Ctrl-C.

EOF

# Verify that we're at the top of the Horde tree.
#
pwd
echo
echo -n "Is this directory the top of your Horde installation? [y,N] "
read RESPONSE 
if [ "$RESPONSE" != "y" -a "$RESPONSE" != "Y" ]; then
    echo
    echo -n "Enter your Horde directory: "
    read DIR  
	if [ "x$DIR" = "x" ]; then
		echo "Exiting..."
		exit
	else
    	cd $DIR
	fi
fi
echo

# Get the web server's group.
#
echo -n "Under what group does the web process run? [nobody] "
read WEB_GROUP
if [ "x$WEB_GROUP" = "x" ]; then
    WEB_GROUP="nobody" 
fi

# Ask before proceeding.
#
echo
echo -n "Proceed with changing ownership and permissions? [y,N] "
read RESPONSE 
if [ "$RESPONSE" != 'y' -a "$RESPONSE" != 'Y' ]; then
    echo "Exiting..."
    exit
fi

# Set the user and group ownership recursively.
#
echo
echo -n "Setting ownership recursively... "
chown -R $OWNER .
chgrp -R $WEB_GROUP .
echo "done."

# Set the permissions on files (0640) and directories (0750).
#
echo -n "Setting permissions recursively... "
find . -type f -exec chmod 0640 {} \;
find . -type d -exec chmod 0750 {} \;
echo "done."

# Disable any "dangerous" PHP scripts in the distribution (0000).
#
echo -n "Disabling potentially \"dangerous\" PHP scripts... "
for FILE in $DANGEROUS_FILES; do
	if [ -f $FILE ]; then
		chmod 0000 $FILE
	fi
done
echo "done."

# Say good-bye.
#
echo
echo "If you received any errors, you may not have sufficient access"
echo "to change file ownership and permissions."
echo
