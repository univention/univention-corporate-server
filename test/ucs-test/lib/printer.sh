#!/bin/bash

. "$TESTLIBPATH/base.sh" || exit 137
. "$TESTLIBPATH/random.sh" || exit 137

function getprintername () { # Generate a name for a printer. E.g. PRINTERNAME=$(getprintername)
    random_chars 10 "${_lowerletters}${_ciphers}"
}

function create_localprinter () { #Creates a printer. E.g. createlocalprinter $PRINTERNAME
    if [ -n "$1" ]
    then
        TMP_PRINTERNAME="$1"
    else
        error "You have to supply a printername to the function createlocalprinter. (E.g. PRINTERNAME=\$(getprintername) and then createlocalprinter \$PRINTERNAME)"
	return 1
    fi

    info "create printer $TMP_PRINTERNAME"

    univention-directory-manager shares/printer create --position "cn=printers,$ldap_base" --set "name=$TMP_PRINTERNAME" --set "spoolHost=$hostname.$domainname" --set "uri=parallel:/ /dev/lp0" --set "model=foomatic-ppds/Apple/Apple-12_640ps-Postscript.ppd.gz"

}

function remove_printer () { # Remove a printer. E.g. removeprinter $PRINTERNAME
    if [ -n "$1" ]
    then
        TMP_PRINTERNAME="$1"
    else
        error "You have to supply a printername to the function removeprinter. E.g. removeprinter \$PRINTERNAME"
	return 1
    fi
    info "remove printer $TMP_PRINTERNAME"
    univention-directory-manager shares/printer remove --dn="cn=$TMP_PRINTERNAME,cn=printers,$ldap_base"
}

function set_printer_sambaname () { # Set the Sambaname for a printer. E.g. setsambaname $PRINTERNAME $PRINTERSAMBANAME
    if [ -n "$1" ]
    then
	PRINTERNAME="$1"
    else
        error "You have to supply a printername to the function set_printer_sambaname. E.g. setsambaname $PRINTERNAME $PRINTERSAMBANAME"
	return 1
    fi
    if [ -n "$2" ]
    then
	SAMBANAME="$2"
    else
        error "You have to supply a sambaname to the function set_printer_sambaname. E.g. setsambaname $PRINTERNAME $PRINTERSAMBANAME"
	return 1
    fi

    info  "setting the sambaName for printer $PRINTERNAME to the value $SAMBANAME"
    univention-directory-manager shares/printer modify --dn="cn=$PRINTERNAME,cn=printers,$ldap_base" --set sambaName="$SAMBANAME"

}

# vim:syntax=sh

