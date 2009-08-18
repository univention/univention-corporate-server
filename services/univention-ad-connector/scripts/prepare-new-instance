#!/bin/bash
#
# Univention AD Connector
#  preparation script for a new parallel running connector instance
#
# Copyright (C) 2004-2009 Univention GmbH
#
# http://www.univention.de/
# 
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA


usage() {
    echo "Script for preparation of a further instance of Univention AD Connector"
    echo "usage: [-f] -a <delete|create> -c $0 <new config basename> "
    echo "examples:"
    echo "$0 -a create -c connector2"
    echo "         creates a new connector-instance with leading name \"connector\""
    echo "         for UCR-variables, paths, init-script etc.. "
    echo "$0 -f -a create -c connector2"
    echo "         same as above, but force action even if the given config"
    echo "         basename already exists. All files are updated from the origin"
    echo "         ones (including the mapping!) but no UCR-variables are changed."
    echo "$0 -a delete -c connector2"
    echo "         Stops the connector, removes files and UCR-Variables for"
    echo "         basename \"connector2\""
}

CONFIGBASENAME=""
createflag="0"
deleteflag="0"
force="0"

while getopts 'hfa:c:' OPTION
do
    case $OPTION in
	h)
	    usage
	    exit 0
	    ;;
	a)
	    case "$OPTARG" in
		create) 
		    createflag="1"
		    ;;
		delete) 
		    deleteflag="1"
		    ;;
		*)
		    echo "ERROR: unknown command given by -a: use \"create\" or \"delete\""
		    echo ""
		    usage
		    exit 1
		    ;;
	    esac
	    ;;
	c)	
	    CONFIGBASENAME="$OPTARG"
	    ;;
	f)
	    forceflag="1"
	    ;;
	?)	
	    usage
	    exit 1
	    ;;
    esac
done

if [ -z "$CONFIGBASENAME" ]
then
    echo "ERROR: no config base given, use \"-c\""
    echo ""
    usage
    exit 1
fi

if [ "$CONFIGBASENAME" = "connector" ]
then
    echo "ERROR: \"connector\" is the default config base that must not be changed by this script!"
    exit 2
fi


if [ "$createflag" = "0" -a "$deleteflag" = "0" ]
then
    echo "ERROR: neither create nor delete given, use \"-a\""
    echo ""
    usage
    exit 1
fi


if [ "$createflag" = "1" ]
then
    
    if [ -e /etc/univention/"$CONFIGBASENAME" ]
    then
	if [ "$forceflag" = "1" ]
	then
	    echo "WARNING: given config base already created, recreate as requested by \"-f\""
	else
	    echo "ERROR: given config base already created, if you want to recreate it use \"-f\""
	    exit 2
	fi    
    fi

    echo "-- initialise UCR"
    univention-config-registry set "$CONFIGBASENAME"/ad/ldap/port?389 "$CONFIGBASENAME"/ad/listener/dir?/var/lib/univention-"$CONFIGBASENAME"/ad "$CONFIGBASENAME"/ad/mapping/group/language?de "$CONFIGBASENAME"/ad/mapping/group/primarymail?false "$CONFIGBASENAME"/ad/mapping/group/win2000/description?false "$CONFIGBASENAME"/ad/mapping/syncmode?sync "$CONFIGBASENAME"/ad/mapping/user/primarymail?false "$CONFIGBASENAME"/ad/mapping/user/win2000/description?false "$CONFIGBASENAME"/ad/poll/sleep?5 "$CONFIGBASENAME"/ad/retryrejected?10 "$CONFIGBASENAME"/debug/function?0 "$CONFIGBASENAME"/debug/level?1 "$CONFIGBASENAME"/password/service/encoding?iso8859-15
    
    echo "-- copy mapping"
    cp -a /etc/univention/connector /etc/univention/"$CONFIGBASENAME"
    sed -i "s|@%@connector/ad/|@%@$CONFIGBASENAME/ad/|" /etc/univention/"$CONFIGBASENAME"/ad/mapping
    
    echo "-- copy startup script"
    cp /usr/sbin/univention-ad-connector /usr/sbin/univention-ad-"$CONFIGBASENAME"
    sed -i "s|/usr/lib/python2.4/site-packages/univention/connector/ad/main.py.*|/usr/lib/python2.4/site-packages/univention/connector/ad/main.py --configbase \"$CONFIGBASENAME\"|" /usr/sbin/univention-ad-"$CONFIGBASENAME"
    sed -i "s|/etc/univention/connector/ad/mapping|/etc/univention/$CONFIGBASENAME/ad/mapping|g" /usr/sbin/univention-ad-"$CONFIGBASENAME"
    
    
    echo "-- copy init script"
    cp /etc/init.d/univention-ad-connector /etc/init.d/univention-ad-"$CONFIGBASENAME"
    sed -i "s|univention-ad-connector|univention-ad-$CONFIGBASENAME|" /etc/init.d/univention-ad-"$CONFIGBASENAME"
    
    echo "-- register initscript"
    update-rc.d univention-ad-"$CONFIGBASENAME" defaults 97
    
    echo "-- prepare second listener-instance"
    mkdir -p /var/lib/univention-"$CONFIGBASENAME"/ad/tmp
    chgrp nogroup /var/lib/univention-"$CONFIGBASENAME"/ad/tmp

fi

if [ "$deleteflag" = "1" ]
then

    echo "-- stop connector"
    /etc/init.d/univention-ad-"$CONFIGBASENAME" stop

    echo "-- unregister initscript"
    update-rc.d -f univention-ad-"$CONFIGBASENAME" remove

    echo "-- remove init script"
    rm /etc/init.d/univention-ad-"$CONFIGBASENAME"

    echo "-- remove startup script"
    rm /usr/sbin/univention-ad-"$CONFIGBASENAME"

    echo "-- unset known UCR variables"
    univention-config-registry unset "$CONFIGBASENAME"/ad/ldap/base 
    univention-config-registry unset "$CONFIGBASENAME"/ad/ldap/binddn 
    univention-config-registry unset "$CONFIGBASENAME"/ad/ldap/bindpw 
    univention-config-registry unset "$CONFIGBASENAME"/ad/ldap/certificate 
    univention-config-registry unset "$CONFIGBASENAME"/ad/ldap/host 
    univention-config-registry unset "$CONFIGBASENAME"/ad/ldap/port 
    univention-config-registry unset "$CONFIGBASENAME"/ad/listener/dir 
    univention-config-registry unset "$CONFIGBASENAME"/ad/mapping/group/language 
    univention-config-registry unset "$CONFIGBASENAME"/ad/mapping/group/primarymail 
    univention-config-registry unset "$CONFIGBASENAME"/ad/mapping/group/win2000/description 
    univention-config-registry unset "$CONFIGBASENAME"/ad/mapping/syncmode 
    univention-config-registry unset "$CONFIGBASENAME"/ad/mapping/user/primarymail 
    univention-config-registry unset "$CONFIGBASENAME"/ad/mapping/user/win2000/description 
    univention-config-registry unset "$CONFIGBASENAME"/ad/poll/sleep 
    univention-config-registry unset "$CONFIGBASENAME"/ad/retryrejected 
    univention-config-registry unset "$CONFIGBASENAME"/debug/function 
    univention-config-registry unset "$CONFIGBASENAME"/debug/level 
    univention-config-registry unset "$CONFIGBASENAME"/password/service/encoding
    
    echo "-- remove config-dir /etc/univention$CONFIGBASENAME"
    rm -r /etc/univention/"$CONFIGBASENAME"
    
    echo "-- remove listener-dir"
    rm -r /var/lib/univention-"$CONFIGBASENAME"/ad

fi