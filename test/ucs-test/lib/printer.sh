#!/bin/bash

. "$TESTLIBPATH/base.sh" || exit 137
. "$TESTLIBPATH/random.sh" || exit 137

getprintername () { # Generate a name for a printer. E.g. PRINTERNAME=$(getprintername)
    random_chars 10 "${_lowerletters}${_ciphers}"
}

create_localprinter () { #Creates a printer. E.g. createlocalprinter $PRINTERNAME
	TMP_PRINTERNAME="${1:?printername, e.g \$(getprintername)}"
	shift
	info "create printer $TMP_PRINTERNAME"

	udm-test shares/printer create \
		--position "cn=printers,$ldap_base" \
		--set name="$TMP_PRINTERNAME" \
		--set spoolHost="$hostname.$domainname" \
		--set uri="parallel:/ /dev/lp0" \
		--set model="foomatic-ppds/Apple/Apple-12_640ps-Postscript.ppd.gz" \
		"$@"
}

remove_printer () { # Remove a printer. E.g. removeprinter $PRINTERNAME
	TMP_PRINTERNAME="${1:?printername}"
	info "remove printer $TMP_PRINTERNAME"
	udm-test shares/printer remove \
		--dn "cn=$TMP_PRINTERNAME,cn=printers,$ldap_base"
}

set_printer_sambaname () { # Set the Sambaname for a printer. E.g. setsambaname $PRINTERNAME $PRINTERSAMBANAME
	PRINTERNAME="${1:?printer name}"
	SAMBANAME="${2:?samba printer name}"
	info  "setting the sambaName for printer $PRINTERNAME to the value $SAMBANAME"
	udm-test shares/printer modify \
		--dn "cn=$PRINTERNAME,cn=printers,$ldap_base" \
		--set sambaName="$SAMBANAME"
}

# vim:set filetype=sh ts=4:
