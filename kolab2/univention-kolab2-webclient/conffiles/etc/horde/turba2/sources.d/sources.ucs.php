<?php
@%@BCWARNING=// @%@

/**
 * $Horde: turba/config/sources.php.dist,v 1.97.6.36 2008/09/12 10:02:42 jan Exp $
 *
 * This file is where you specify the sources of contacts available to users
 * at your installation. It contains a large number of EXAMPLES. Please
 * remove or comment out those examples that YOU DON'T NEED. There are a
 * number of properties that you can set for each server, including:
 *
 * title:       This is the common (user-visible) name that you want displayed
 *              in the contact source drop-down box.
 *
 * type:        The types 'ldap', 'sql', 'imsp', 'group', 'favourites' and
 *              'prefs' are currently supported. Preferences-based address
 *              books are not intended for production installs unless you
 *              really know what you're doing - they are not searchable, and
 *              they won't scale well if a user has a large number of entries.
 *
 * params:      These are the connection parameters specific to the contact
 *              source. See below for examples of how to set these.
 *
 * Special params settings:
 *
 *   charset:       The character set that the backend stores data in. Many
 *                  LDAP servers use utf-8. Database servers typically use
 *                  iso-8859-1.
 *
 *   tls:           Only applies to LDAP servers. If true, then try to use a
 *                  TLS connection to the server.
 *
 *   scope:         Only applies to LDAP servers. Can be set to 'one' to
 *                  search one level of the LDAP directory, or 'sub' to search
 *                  all levels. 'one' will work for most setups and should be
 *                  much faster. However we default to 'sub' for backwards
 *                  compatibility.
 *
 *   checkrequired: Only applies to LDAP servers. If present, this value causes
 *                  the driver to consult the LDAP schema for any attributes
 *                  that are required by the given objectclass(es). Required
 *                  attributes will be provided automatically if the
 *                  'checkrequired_string' parameter is present.
 *                  *NOTE* You must have the Net_LDAP PEAR library installed
 *                  for this to work.
 *
 *   checksyntax:   Only applies to LDAP servers. If present, this value causes
 *                  the driver to inspect the LDAP schema for particular
 *                  attributes by the type defined in the corresponding schema
 *                  *NOTE* You must have the Net_LDAP PEAR library installed
 *                  for this to work.
 *
 *   deref:         Only applies to LDAP servers. If set, should be one of:
 *                    LDAP_DEREF_NEVER
 *                    LDAP_DEREF_SEARCHING
 *                    LDAP_DEREF_FINDING
 *                    LDAP_DEREF_ALWAYS
 *                  This tells the LDAP server when to dereference
 *                  aliases. See http://www.php.net/ldap for more
 *                  information.
 *
 *   dn:            Only applies to LDAP servers. Defines the list of LDAP
 *                  attributes that build a valid DN.
 *
 *   objectclass:   Only applies to LDAP servers. Defines a list of
 *                  objectclasses that contacts must belong to, and
 *                  that new objects will be created with.
 *
 *   filter:        Filter helps to filter your result based on certain
 *                  condition in SQL and LDAP backends. A filter can be
 *                  specified to avoid some unwanted data. For example, if the
 *                  source is an external sql database, to select records with
 *                  the delete flag = 0:
 *                  'filter' = 'deleted=0'
 *
 * map:         This is a list of mappings from the Turba attribute names (on
 *              the left) to the attribute names by which they are known in
 *              this contact source (on the right). Turba also supports
 *              composite fields. A composite field is defined by mapping the
 *              field name to an array containing a list of component fields
 *              and a format string (similar to a printf() format string;
 *              however, note that positioned parameters like %1$s will NOT
 *              work). 'attribute' defines where the composed value is saved,
 *              and can be left out. 'parse' defines a list of format strings
 *              and field names that should be used for splitting up composite
 *              fields, in the order of precedence, and can be left out. Here
 *              is an example:
 *              ...
 *              'name' => array('fields' => array('firstname', 'lastname'),
 *                              'format' => '%s %s',
 *                              'attribute' => 'object_name'),
 *              'firstname' => 'object_firstname',
 *              'lastname' => 'object_lastname',
 *              ...
 *
 *              Standard Turba attributes are:
 *                __key     : A backend-specific ID for the entry (any value
 *                            as long as it is unique inside that source;
 *                            required)
 *                __uid     : Globally unique ID of the entry (used for
 *                            synchronizing and must be able to be set to any
 *                            value)
 *                __owner   : User name of the contact's owner
 *                __type    : Either 'Object' or 'Group'
 *                __members : Serialized PHP array with list of Group members.
 *              More Turba attributes are defined in config/attributes.php.
 *
 * tabs:        All fields can be grouped into tabs with this optional entry.
 *              This list is multidimensional hash, the keys are the tab
 *              titles.
 *              Here is an example:
 *              'tabs' => array(
 *                  'Names' => array('firstname', 'lastname', 'alias'),
 *                  'Addresses' => array('homeAddress', 'workAddress')
 *              );
 *
 * search:      A list of Turba attribute names that can be searched for this
 *              source.
 *
 * strict:      A list of native field/attribute names that must
 *              always be matched exactly in a search.
 *
 * approximate: Only applies to LDAP servers. If set, should be an
 *              array of native field/attribute names to search
 *              "approximately" (for example, "Sánchez", "Sanchez",
 *              and "Sanchéz" will all match a search string of
 *              "sanchez").
 *
 * export:      If set to true, this source will appear on the Export menu,
 *              allowing users to export the contacts to a CSV (etc.) file.
 *
 * browse:      If set to true, this source will be browseable via the Browse
 *              menu item, and empty searches against the source will return
 *              all contacts.
 *
 * use_shares:  If this is present and true, Horde_Share functionality will
 *              be enabled for this source - allowing users to share their
 *              personal address books as well as to create new ones. Since
 *              Turba only supports having one backend configured for
 *              creating new shares, use the 'shares' configuration option to
 *              specify which backend will be used for creating new shares.
 *              All permission checking will be done against Horde_Share, but
 *              note that any 'extended' permissions (such as max_contacts)
 *              will still be enforced. Also note that the backend driver
 *              must have support for using this. Currently SQL and IMSP.
 *
 * list_name_field:  If this is present and non-empty, it will be taken as the
 *                   field to store contact list names in.
 *                   This is required when using a composite field as the 'name'
 *                   field.
 *
 * alternative_name: If this is present and non-empty, it will be taken as the
 *                   field to use an alternative in case that the name field is
 *                   empty.
 *
 * Here are some example configurations:
 */

/* Begin Kolab sources. */
if (!empty($GLOBALS['conf']['kolab']['enabled'])) {

    /* Only use LDAP if we have that extension in PHP */
    if (function_exists('ldap_connect')) {
        require_once 'Horde/Kolab.php';

        if (!is_callable('Kolab', 'getServer')) {
            $_kolab_server = $GLOBALS['conf']['kolab']['ldap']['server'];
        } else {
            $_kolab_server = Kolab::getServer('ldap');
        }

        /* A global address book for a Kolab Server. This is typically a
         * read-only public directory, stored in the default Kolab LDAP server.
         * The user accessing this should have read permissions to the shared
         * directory in LDAP. */
        $cfgSources['kolab_global'] = array(
            'title' => _("Global Address Book"),
            'type' => 'ldap',
            'params' => array(
                'server' => $_kolab_server,
                'port' => $GLOBALS['conf']['kolab']['ldap']['port'],
                'tls' => false,
                'root' => $GLOBALS['conf']['kolab']['ldap']['basedn'],
                'sizelimit' => 200,
                'dn' => array('cn'),
                'objectclass' => array(
                    'inetOrgPerson'
                ),
                'scope' => 'sub',
                'charset' => 'utf-8',
                'version' => 3,
                'bind_dn' => '',
                'bind_password' => '',
            	'read_only' => true,
            ),
            'map' => array(
                '__key'             => 'dn',
                'name'              => 'cn',
                'firstname'         => 'givenName',
                'lastname'          => 'sn',
                'email'             => 'mail',
                'alias'             => 'alias',
                'title'             => 'title',
                'company'           => 'o',
                'workStreet'        => 'street',
                'workCity'          => 'l',
                'workProvince'      => 'st',
                'workPostalCode'    => 'postalCode',
                'workCountry'       => 'c',
                'homePhone'         => 'homePhone',
                'workPhone'         => 'telephoneNumber',
                'cellPhone'         => 'mobile',
                'fax'               => 'fax',
                'notes'             => 'description',
                'kolabHomeServer'   => 'kolabHomeServer',
                'freebusyUrl'       => array('fields' => array('kolabHomeServer', 'email'),
                                             'format' => 'https://%s/freebusy/%s.xfb',
                                             'defaults' => array('kolabHomeServer' => $GLOBALS['conf']['kolab']['imap']['server'])),
            ),
            'search' => array(
                'name',
                'firstname',
                'lastname',
                'email',
                'title',
                'company',
                'workAddress',
                'workCity',
                'workProvince',
                'workPostalCode',
                'workCountry',
                'homePhone',
                'workPhone',
                'cellPhone',
                'fax',
                'notes',
            ),
            'strict' => array(
                'dn',
            ),
            'export' => true,
            'browse' => true,
        );
    }

    /**
     * The local address books for a Kolab user. These are stored in specially
     * flagged contact folder within the users Cyrus IMAP mailbox.
     *
     * Still missing attributes are:
     *
     *   picture, sensitivity
     */

    $cfgSources['kolab'] = array(
        'title' => _("Contacts"),
        'type' => 'kolab',
        'params' => array(
            'charset' => 'utf-8',
        ),
        'list_name_field' => 'lastname',
        'map' => array(
            '__key' => 'uid',
            '__uid' => 'uid',
            '__type' => '__type',
            '__members' => '__members',
            /* Personal */
            'name' => array('fields' => array('firstname', 'middlenames', 'lastname'),
                            'format' => '%s %s %s',
                            'parse' => array(
                                array('fields' => array('firstname', 'middlenames',
                                                        'lastname'),
                                      'format' => '%s %s %s'),
                                array('fields' => array( 'lastname', 'firstname'),
                                      'format' => '%s, %s'),
                                array('fields' => array('firstname', 'lastname'),
                                      'format' => '%s %s'),
                            )),
            'firstname'         => 'given-name',
            'lastname'          => 'last-name',
            'middlenames'       => 'middle-names',
            'namePrefix'        => 'prefix',
            'nameSuffix'        => 'suffix',
            'initials'          => 'initials',
            'nickname'          => 'nick-name',
            'photo'             => 'photo',
            'phototype'         => 'phototype',
            'gender'            => 'gender',
            'birthday'          => 'birthday',
            'spouse'            => 'spouse-name',
            'anniversary'       => 'anniversary',
            'children'          => 'children',
            /* Location */
            'workStreet'        => 'addr-business-street',
            'workCity'          => 'addr-business-locality',
            'workProvince'      => 'addr-business-region',
            'workPostalCode'    => 'addr-business-postal-code',
            'workCountry'       => 'addr-business-country',
            'homeStreet'        => 'addr-home-street',
            'homeCity'          => 'addr-home-locality',
            'homeProvince'      => 'addr-home-region',
            'homePostalCode'    => 'addr-home-postal-code',
            'homeCountry'       => 'addr-home-country',
            /* Communications */
            'emails'            => 'emails',
            'homePhone'         => 'phone-home1',
            'workPhone'         => 'phone-business1',
            'cellPhone'         => 'phone-mobile',
            'fax'               => 'phone-businessfax',
            'instantMessenger'  => 'im-address',
            /* Organization */
            'title'             => 'job-title',
            'role'              => 'profession',
            'company'           => 'organization',
            'department'        => 'department',
            'office'            => 'office-location',
            'manager'           => 'manager-name',
            'assistant'         => 'assistant',
            /* Other */
            'category'          => 'categories',
            'notes'             => 'body',
            'website'           => 'web-page',
            'freebusyUrl'       => 'free-busy-url',
            'language'          => 'language',
            'latitude'          => 'latitude',
            'longitude'         => 'longitude',
            /* Invisible */
            'email'             => 'email',
            'pgpPublicKey'      => 'pgp-publickey',
        ),
        'tabs' => array(
            _("Personal") => array('name', 'firstname', 'lastname', 'middlenames',
                                   'namePrefix', 'nameSuffix', 'initials', 'nickname',
                                   'photo', 'gender', 'birthday', 'spouse', 'anniversary',
                                   'children'),
            _("Location") => array('homeStreet', 'homeCity', 'homeProvince',
                                   'homePostalCode', 'homeCountry', 'workStreet',
                                   'workCity', 'workProvince', 'workPostalCode',
                                   'workCountry'),
            _("Communications") => array('emails', 'homePhone', 'workPhone',
                                         'cellPhone', 'fax', 'instantMessenger'),
            _("Organization") => array('title', 'role', 'company', 'department',
                                       'office', 'manager', 'assistant'),
            _("Other") => array('category', 'notes', 'website', 'freebusyUrl',
                                'language', 'latitude', 'longitude'),
        ),
        'search' => array(
            /* Personal */
            'name',
            'firstname',
            'lastname',
            'middlenames',
            'namePrefix',
            'nameSuffix',
            'initials',
            'nickname',
            'gender',
            'birthday',
            'spouse',
            'anniversary',
            'children',
            /* Location */
            'workStreet',
            'workCity',
            'workProvince',
            'workPostalCode',
            'workCountry',
            'homeStreet',
            'homeCity',
            'homeProvince',
            'homePostalCode',
            'homeCountry',
            /* Communications */
            'emails',
            'homePhone',
            'workPhone',
            'cellPhone',
            'fax',
            'instantMessenger',
            /* Organization */
            'title',
            'role',
            'company',
            'department',
            'office',
            'manager',
            'assistant',
            /* Other */
            'category',
            'notes',
            'website',
            'language',
        ),
        'strict' => array(
            'uid',
        ),
        'export' => true,
        'browse' => true,
        'use_shares' => true,
        'shares_only' => true,
    );
}
/* End Kolab sources. */
?>
