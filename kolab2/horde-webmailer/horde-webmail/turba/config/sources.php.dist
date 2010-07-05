<?php
/**
 * $Horde: turba/config/sources.php.dist,v 1.97.6.41 2009-08-05 21:06:10 jan Exp $
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
 *   root:          Only applies to LDAP servers. Defines the base DN where to
 *                  start the search, i.e. dc=example,dc=com.
 *
 *   bind_dn:       Only applies to LDAP servers which do not allow anonymous
 *                  connections. Active Directory servers do not allow it by
 *                  default, so before using one as a Turba source, you must
 *                  create a "rightless" user, which is only allowed to connect
 *                  to the server, and set the bind_dn parameter like
 *                  'rightless@example.com' (not cn=rightless,dc=example,dc=com)
 *
 *   bind_password: Only applies to LDAP servers which do not allow anonymous
 *                  connection. You should set this to the cleartext password
 *                  for the user specified in 'bind_dn'.
 *
 *   referrals:     Only applies to LDAP servers. If set, should be 0 or 1.
 *                  See the LDAP documentation about the corresponding
 *                  parameter REFERRALS. Windows 2003 Server requires that you
 *                  set this parameter to 0.
 *
 *   sizelimit:     Only applies to LDAP servers. If set, limit the search to
 *                  the specified number of entries. Value 0 or no value means
 *                  no limit. Keep in mind that servers can impose their own
 *                  search limits.
 *
 *   objectclass:   Only applies to LDAP servers. Defines a list of
 *                  objectclasses that contacts must belong to, and that new
 *                  objects will be created with.
 *
 *   filter:        Filter helps to filter your result based on certain
 *                  condition in SQL and LDAP backends. A filter can be
 *                  specified to avoid some unwanted data. For example, if the
 *                  source is an external sql database, to select records with
 *                  the delete flag = 0: 'filter' => 'deleted=0'.
 *                  Don't enclose filter in brackets - this will done
 *                  automatically. Also keep in mind that a full filter line
 *                  will be built from 'filter' and 'objectclass' parameters.
 *
 *   version:       Only applies to LDAP servers. If set, specify LDAP server
 *                  version, can be 2 or 3. Active Directory servers
 *                  require version 3.
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

/**
 * A local address book in an SQL database. This implements a private
 * per-user address book. Sharing of this source with other users may be
 * accomplished by enabling Horde_Share for this source by setting
 * 'use_shares' => true.
 *
 * Be sure to create a turba_objects table in your Horde database from the
 * schema in turba/scripts/db/turba.sql if you use this source.
 */
$cfgSources['localsql'] = array(
    'title' => _("My Address Book"),
    'type' => 'sql',
    // The default connection details are pulled from the Horde-wide SQL
    // connection configuration.
    'params' => array_merge($GLOBALS['conf']['sql'], array('table' => 'turba_objects')),
    // Using two tables as datasource.
    // 'params' => array_merge($GLOBALS['conf']['sql'],
    //                         array('table' => 'leaddetails LEFT JOIN leadaddress ON leaddetails.leadid = leadaddress.leadaddressid',
    //                               'filter' => 'leaddetails.converted = 0')),
    'map' => array(
        '__key' => 'object_id',
        '__owner' => 'owner_id',
        '__type' => 'object_type',
        '__members' => 'object_members',
        '__uid' => 'object_uid',
        'firstname' => 'object_firstname',
        'lastname' => 'object_lastname',
        'middlenames' => 'object_middlenames',
        'namePrefix' => 'object_nameprefix',
        'nameSuffix' => 'object_namesuffix',
        'name' => array('fields' => array('namePrefix', 'firstname',
                                          'middlenames', 'lastname',
                                          'nameSuffix'),
                        'format' => '%s %s %s %s %s',
                        'parse' => array(
                            array('fields' => array('firstname', 'middlenames',
                                                    'lastname'),
                                  'format' => '%s %s %s'),
                            array('fields' => array('firstname', 'lastname'),
                                  'format' => '%s %s'))),
        // This is a shorter version of a "name" composite field which only
        // consists of the first name and last name.
        // 'name' => array('fields' => array('firstname', 'lastname'),
        //                 'format' => '%s %s'),
        'alias' => 'object_alias',
        'birthday' => 'object_bday',
        // The photo field requires at least Horde 3.3 and a matching type
        // field.
        // 'photo' => 'object_photo',
        // 'phototype' => 'object_phototype',
        'homeStreet' => 'object_homestreet',
        'homePOBox' => 'object_homepob',
        'homeCity' => 'object_homecity',
        'homeProvince' => 'object_homeprovince',
        'homePostalCode' => 'object_homepostalcode',
        'homeCountry' => 'object_homecountry',
        // This is an example composite field for addresses, so you can display
        // the various map links. If you use this, be sure to add 'homeAddress'
        // to the 'tabs' parameter below.
        // 'homeAddress' => array('fields' => array('homeStreet', 'homeCity',
        //                                          'homeProvince',
        //                                          'homePostalCode'),
        //                        'format' => "%s \n %s, %s  %s"),
        'workStreet' => 'object_workstreet',
        'workPOBox' => 'object_workpob',
        'workCity' => 'object_workcity',
        'workProvince' => 'object_workprovince',
        'workPostalCode' => 'object_workpostalcode',
        'workCountry' => 'object_workcountry',
        'timezone' => 'object_tz',
        'email' => 'object_email',
        'homePhone' => 'object_homephone',
        'workPhone' => 'object_workphone',
        'cellPhone' => 'object_cellphone',
        'fax' => 'object_fax',
        'pager' => 'object_pager',
        'title' => 'object_title',
        'role' => 'object_role',
        'company' => 'object_company',
        // The logo field requires at least Horde 3.3 and a matching type
        // field.
        // 'logo' => 'object_logo',
        // 'logotype' => 'object_logotype',
        'category' => 'object_category',
        'notes' => 'object_notes',
        'website' => 'object_url',
        'freebusyUrl' => 'object_freebusyurl',
        'pgpPublicKey' => 'object_pgppublickey',
        'smimePublicKey' => 'object_smimepublickey',
    ),
    'tabs' => array(
        _("Personal") => array('firstname', 'lastname', 'middlenames',
                               'namePrefix', 'nameSuffix', 'name', 'alias',
                               'birthday', 'photo'),
        _("Location") => array('homeStreet', 'homePOBox', 'homeCity',
                               'homeProvince', 'homePostalCode', 'homeCountry',
                               'workStreet', 'workPOBox', 'workCity',
                               'workProvince', 'workPostalCode', 'workCountry',
                               'timezone'),
        _("Communications") => array('email', 'homePhone', 'workPhone',
                                     'cellPhone', 'fax', 'pager'),
        _("Organization") => array('title', 'role', 'company', 'logo'),
        _("Other") => array('category', 'notes', 'website', 'freebusyUrl',
                            'pgpPublicKey', 'smimePublicKey'),
    ),
    'search' => array(
        'name',
        'email'
    ),
    'strict' => array(
        'object_id',
        'owner_id',
        'object_type',
    ),
    'export' => true,
    'browse' => true,
    'use_shares' => true,
    'list_name_field' => 'lastname',
    'alternative_name' => 'company',
);

/**
 * A local address book in an LDAP directory. This implements a public
 * (shared) address book.
 *
 * To store distribution lists in the LDAP directory, you'll need to include
 * horde/scripts/ldap/horde.schema in your LDAP configuration.
 *
 * To store freebusy information in the LDAP directory, you'll need to include
 * turba/scripts/ldap/rfc2739.schema in your LDAP configuration.
 */
// $cfgSources['localldap'] = array(
//     'title' => _("Shared Directory"),
//     'type' => 'ldap',
//     'params' => array(
//         'server' => 'ldap.example.com',
//         'port' => 389,
//         'tls' => false,
//         'root' => 'dc=example,dc=com',
//         'bind_dn' => 'cn=admin,ou=users,dc=example,dc=com',
//         // For Active Directory:
//         // 'bind_dn' => 'username@example.com',
//         'bind_password' => '********',
//         'sizelimit' => 200,
//         // For Active Directory:
//         // 'sizelimit' => 0,
//         'dn' => array('cn'),
//         'objectclass' => array('top',
//                                'person',
//                                'organizationalPerson',
//                                'inetOrgPerson'),
//                                // Add 'turbaContact' to this array if using
//                                // 'turbaType' attribute below, and 'calEntry'
//                                // if using 'freebusyUrl'.
//         // For Active Directory:
//         // 'objectclass' => array('organizationalPerson',
//         //                        'user',
//         //                        'group',
//         //                        'contact'),
//         'scope' => 'one',
//         // For Active Directory:
//         // 'scope' => 'sub',
//         'charset' => 'utf-8',
//         // Consult the LDAP schema to verify that all required attributes for
//         // an entry are set and add them if needed.
//         'checkrequired' => false,
//         // Value used to fill in missing required attributes.
//         'checkrequired_string' => ' ',
//         // Check LDAP schema for valid syntax. If this is false an address
//         // field is assumed to have postalAddress syntax; otherwise the schema
//         // is consulted for the syntax to use.
//         'checksyntax' => false,
//         'version' => 3,
//
//         // For Active Directory you probably want to also set the following
//         // parameters:
//         // 'deref' => LDAP_DEREF_ALWAYS,
//         // 'filter' => '&(SAMAccountName=*)(mail=*)',
//         // 'referrals' => 0,
//     ),
//     'map' => array(
//         '__key' => 'dn',
//
//         // Remove this mapping if using Active Directory server:
//         '__uid' => 'uid',
//
//         // From horde.schema.  Make sure you have 'turbaContact' objectClass
//         // included above:
//         // '__type' => 'turbaType',
//         // '__members' => 'turbaMembers',
//
//         'name' => 'cn',
//         'email' => 'mail',
//         'homePhone' => 'homephone',
//         'workPhone' => 'telephonenumber',
//         'cellPhone' => 'mobiletelephonenumber',
//         'homeAddress' => 'homepostaladdress',
//
//         // From rfc2739.schema:
//         // 'freebusyUrl' => 'calFBURL',
//
//         // For Active Directory servers:
//         // 'name' => 'displayname',
//         // 'title' => 'title',
//         // 'cellPhone' => 'mobile',
//         // 'department' => 'department',
//         // 'company' => 'company',
//     ),
//     'search' => array(
//         'name',
//         'email',
//         'homePhone',
//         'workPhone',
//         'cellPhone',
//         'homeAddress'
//     ),
//     'strict' => array(
//         'dn',
//     ),
//     'approximate' => array(
//         'cn',
//     ),
//     // For Active Directory servers:
//     // 'approximate' => array(
//     //     'displayname',
//     //     'samaccountname',
//     // ),
//     'export' => true,
//     'browse' => true,
// );

/**
 * A personal LDAP address book. This assumes that the login is
 * <username>@domain.com and that the users are stored on the same LDAP
 * server. Thus it is possible to bind with the username and password from the
 * user. For more info; please refer to the docs/LDAP file in the Turba
 * distribution.
 *
 * To store distribution lists in the LDAP directory, you'll need to include
 * horde/scripts/ldap/horde.schema in your LDAP configuration.
 *
 * To store freebusy information in the LDAP directory, you'll need to include
 * turba/scripts/ldap/rfc2739.schema in your LDAP configuration.
 */
/* First we need to get the uid. */
// $_ldap_uid = Auth::getBareAuth();
// $_ldap_basedn = 'dc=example,dc=com';
// $cfgSources['personal_ldap'] = array(
//     'title' => _("My Address Book"),
//     'type' => 'ldap',
//     'params' => array(
//         'server' => 'localhost',
//         'tls' => false,
//         'root' => 'ou=' . $_ldap_uid . ',ou=personal_addressbook,' . $_ldap_basedn,
//         'bind_dn' => 'uid=' . $_ldap_uid . ',ou=People,' . $_ldap_basedn,
//         'bind_password' => Auth::getCredential('password'),
//         'dn' => array('uid'),
//         'objectclass' => array('top',
//                                'person',
//                                // 'turbaContact',
//                                'inetOrgPerson',
//                                // 'calEntry',
//                                'organizationalPerson'),
//         'scope' => 'one',
//         'charset' => 'utf-8',
//         'version' => 3
//     ),
//     'map' => array(
//         '__key' => 'dn',
//         '__uid' => 'uid',
//
//         // From horde.schema:
//         // '__type' => 'turbaType',
//         // '__members' => 'turbaMembers',
//
//         'name' => 'cn',
//         'email' => 'mail',
//         'lastname' => 'sn',
//         'title' => 'title',
//         'company' => 'organizationname',
//         'businessCategory' => 'businesscategory',
//         'workAddress' => 'postaladdress',
//         'workPostalCode' => 'postalcode',
//         'workPhone' => 'telephonenumber',
//         'fax' => 'facsimiletelephonenumber',
//         'homeAddress' => 'homepostaladdress',
//         'homePhone' => 'homephone',
//         'cellPhone' => 'mobile',
//         'notes' => 'description',
//
//         // Evolution interopt attributes: (those that do not require the
//         // evolution.schema)
//         'office' => 'roomNumber',
//         'department' => 'ou',
//         'nickname' => 'displayName',
//         'website' => 'labeledURI',
//
//         // These are not stored on the LDAP server.
//         'pgpPublicKey' => 'object_pgppublickey',
//         'smimePublicKey' => 'object_smimepublickey',
//
//         // From rfc2739.schema:
//         // 'freebusyUrl' => 'calFBURL',
//     ),
//     'search' => array(
//         'name',
//         'email',
//         'businessCategory',
//         'title',
//         'homePhone',
//         'workPhone',
//         'cellPhone',
//         'homeAddress'
//     ),
//     'strict' => array(
//         'dn',
//     ),
//     'approximate' => array(
//         'cn',
//     ),
//     'export' => true,
//     'browse' => true,
// );

/**
 * Public netcenter and verisign LDAP directories.
 */
// $cfgSources['netcenter'] = array(
//     'title' => _("Netcenter Member Directory"),
//     'type' => 'ldap',
//     'params' => array(
//         'server' => 'memberdir.netscape.com',
//         'port' => 389,
//         'tls' => false,
//         'root' => 'ou=member_directory,o=netcenter.com',
//         'dn' => array('cn'),
//         'objectclass' => 'person',
//         'filter' => '',
//         'scope' => 'sub',
//         'charset' => 'iso-8859-1'
//     ),
//     'map' => array(
//         '__key' => 'dn',
//         'name' => 'cn',
//         'email' => 'mail',
//         'alias' => 'givenname'
//     ),
//     'search' => array(
//         'name',
//         'email',
//         'alias'
//     ),
//     'strict' => array(
//         'dn'
//     ),
//     'approximate' => array(
//         'cn',
//     ),
//     'export' => false,
//     'browse' => false,
// );
//
// $cfgSources['verisign'] = array(
//     'title' => _("Verisign Directory"),
//     'type' => 'ldap',
//     'params' => array(
//         'server' => 'directory.verisign.com',
//         'port' => 389,
//         'tls' => false,
//         'root' => '',
//         'scope' => 'sub',
//         'charset' => 'iso-8859-1'
//     ),
//     'map' => array(
//         '__key' => 'dn',
//         'name' => 'cn',
//         'email' => 'mail'
//     ),
//     'search' => array(
//         'name',
//         'email'
//     ),
//     'strict' => array(
//         'dn'
//     ),
//     'approximate' => array(
//         'cn',
//     ),
//     'export' => false,
//     'browse' => false,
// );

/**
 * A preferences-based address book. This will always be private. You can add
 * any attributes you like to the map and it will just work; you can also
 * create multiple prefs-based address books by changing the 'name' parameter.
 * This is best for address books that are expected to remain small; it's not
 * the most efficient, but it can't be beat for getting up and running
 * quickly, especially if you already have Horde preferences working. Note
 * that it is not searchable, though - searches will simply return the whole
 * address book.
 */
// $cfgSources['prefs'] = array(
//     'title' => _("Private Address Book"),
//     'type' => 'prefs',
//     'params' => array(
//         'name' => 'prefs',
//         'charset' => NLS::getCharset()
//     ),
//     'map' => array(
//         '__key' => 'id',
//         '__type' => '_type',
//         '__members' => '_members',
//         '__uid' => 'uid',
//         'name' => 'name',
//         'email' => 'mail',
//         'alias' => 'alias'
//     ),
//     'search' => array(
//         'name',
//         'email',
//         'alias'
//     ),
//     'strict' => array(
//         'id',
//         '_type',
//     ),
//     'export' => true,
//     'browse' => true,
// );

/**
 * An address book based on message recipients. This will always be private and
 * read-only. The address book content is provided by the
 * contacts/favouriteRecipients API method which should be implemented by a
 * mail client that collects the most regular message recipients, like IMP
 * 4.2.
 */
$cfgSources['favourites'] = array(
    'title' => _("Favourite Recipients"),
    'type' => 'favourites',
    'params' => array(
        'limit' => 10
    ),
    'map' => array(
        '__key' => 'email',
        'name' => 'email',
        'email' => 'email'
    ),
    'search' => array(
        'name',
        'email'
    ),
    'strict' => array(
        'id',
    ),
    'export' => true,
    'browse' => true,
);

/**
 * This source creates an address book for each group the current user is a
 * member in.  The address book will always be read only, and the group members
 * must have an email address entered in their default identity.  No email
 * address will result in that member not being included in the address book.
 */
//$grpSource = array(
//    'title' => _("Group"),
//    'type' => 'group',
//    'params' => array(
//       'name' => ''
//    ),
//    'map' => array(
//        '__key' => 'email',
//        'name' => 'name',
//        'email' => 'email'
//    ),
//    'search' => array(
//        'name',
//        'email'
//    ),
//    'export' => true,
//    'browse' => true,
//);

//require_once 'Horde/Group.php';
//$_group_driver = &Group::singleton();
//$_group_list = $_group_driver->getGroupMemberships(Auth::getAuth());
//foreach ($_group_list as $_group_id => $_group_name) {
//    $cfgSources['group_' . $_group_id] = $grpSource;
//    $cfgSources['group_' . $_group_id]['params'] = array('gid' => $_group_id);
//    $cfgSources['group_' . $_group_id]['title'] = $_group_name;
//}

/**
 * IMSP based address book.
 *
 * Communicates with an IMSP backend server.
 *
 * Notes:
 * You should configure the user's "main" address book here. The name of the
 * address book is set in the 'name' element of the params array. It should
 * be configured to be the same as the IMSP server username. Any other
 * address books the user has access to will automatically be configured at
 * runtime.
 *
 * In the params array, accepted values for auth_method are 'cram_md5',
 * 'imtest', and 'plaintext' - these must match a IMSP_Auth_ driver. If you
 * are using the imtest driver for Cyrus, please read the
 * framework/Net_IMSP/Auth/imtest.php file for more configuration information.
 *
 * Groups in other IMSP-aware applications are just entries with multiple
 * email addresses in the email field and a 'group' field set to flag the
 * entry as a group. (The Cyrusoft applications, Mulberry and Silkymail both
 * use a field named 'group' set to equal 'group' to signify this). A
 * Turba_Object_Group is basically a List of existing Turba_Objects. The IMSP
 * driver will map between these two structures when reading and writing
 * groups.
 * The only caveat is that IMSP groups that contain email addresses which do
 * not have a cooresponding contact entry will be ignored. The group_id_field
 * should be set to the IMSP field that flags the entry as a 'group' entry and
 * the group_id_value should be set to the value given to that field.
 *
 * By default, the username and password that were used to login to Horde is
 * used to login to the IMSP server. If these credentials are different,
 * there is a user preference in Horde to allow another username / password to
 * be entered. The alternate credentials are always used if present.
 *
 * In the map array, since IMSP uses the 'name' attribute as a key, this is
 * what __key is mapped to ... and a dynamic field 'fullname' is added and
 * mapped to the horde 'name' field. This is populated with the IMSP 'name'
 * field when the object is read from the server.
 *
 * If you wish to keep track of ownership of individual contacts, set
 * 'contact_ownership' = true. Note that entries created using other clients
 * will not be created this way and will therefore have no 'owner'. Set
 * 'contact_ownership' = false and the __owner field will be automatically
 * populated with the current username.
 *
 * To integrate with Horde_Share (requires Horde 3.2 or better) set use_shares
 * to true, and uncomment the IMSP Horde_Share hooks in horde/config/hooks.php.
 */
// Check that IMSP is configured in Horde but fall through if there is no
// configuration at all - in case we don't have at least a 3.0.6 Horde
// install.  (In that case, be sure to change the params array below to suit
// your needs.
if (!empty($GLOBALS['conf']['imsp']['enabled']) ||
    !isset($GLOBALS['conf']['imsp']['enabled'])) {
    // First, get the user name to login to IMSP server with.
    $_imsp_auth_user = $GLOBALS['prefs']->getValue('imsp_auth_user');
    $_imsp_auth_pass = $GLOBALS['prefs']->getValue('imsp_auth_pass');
    if (!strlen($_imsp_auth_user)) {
        $_imsp_auth_user = Auth::getBareAuth();
        $_imsp_auth_pass = Auth::getCredential('password');
    }
    $cfgSources['imsp'] = array(
        'title' => _("IMSP"),
        'type' => 'imsp',
        'params' => array(
            'server'  => $GLOBALS['conf']['imsp']['server'],
            'port'    => $GLOBALS['conf']['imsp']['port'],
            'auth_method' => $GLOBALS['conf']['imsp']['auth_method'],
            // socket, command, and auth_mechanism are for imtest driver.
            'socket'  => isset($GLOBALS['conf']['imsp']['socket']) ?
                         $GLOBALS['conf']['imsp']['socket'] . $_imsp_auth_user . '.sck' :
                         '',
            'command' => isset($GLOBALS['conf']['imsp']['command']) ?
                         $GLOBALS['conf']['imsp']['command'] : '' ,
            'auth_mechanism' => isset($GLOBALS['conf']['imsp']['auth_mechanism']) ?
                                $GLOBALS['conf']['imsp']['auth_mechanism'] : '',
            'username' => $_imsp_auth_user,
            'password' => $_imsp_auth_pass,
            'name' => $_imsp_auth_user,
            'group_id_field' => 'group',
            'group_id_value' => 'group',
            'contact_ownership' => false,
            // Dynamically generated acl rights for current user.
            'my_rights' => '',
            ),
        'map' => array(
            '__key' => 'name',
            '__type' => '__type',
            '__members' => '__members',
            '__owner' => '__owner',
            '__uid' => '__uid',
            'name' => 'fullname',
            'email' => 'email',
            'alias' => 'alias',
            'company' => 'company',
            'notes' => 'notes',
            'workPhone' => 'phone-work',
            'fax' => 'fax',
            'homePhone' => 'phone-home',
            'cellPhone' => 'cellphone',
            'freebusyUrl' => 'freebusyUrl'
            ),
        'search' => array(
            'name',
            'email',
            'alias',
            'company',
            'homePhone'
            ),
        'strict' => array(),
        'export' => true,
        'browse' => true,
        'use_shares' => false,
        );

    /**
     * Get any other address books this user might be privy to.
     * The values for attributes such as 'export' and 'browse' for books
     * that are added below will be the same as the values set in the default
     * book above. Any entries defined explicitly in cfgSources[]
     * will override any entries gathered dynamically below.
     */
     if (empty($cfgSources['imsp']['use_shares'])) {
        require_once 'Net/IMSP/Utils.php';
        $result = Net_IMSP_Utils::getAllBooks($cfgSources['imsp']);

        if (!is_a($result, 'PEAR_Error')) {
            $resultCount = count($result);
            for ($i = 0; $i < $resultCount; $i++) {
                // Make sure we didn't define this source explicitly,
                // but set the acls from the server regardless.
                $dup = false;
                foreach ($cfgSources as $key => $thisSource) {
                    if (($thisSource['type'] == 'imsp') &&
                        ($thisSource['params']['name'] == $result[$i]['params']['name'])) {

                        $dup = true;
                        $acl = $result[$i]['params']['my_rights'];
                        $cfgSources[$key]['params']['my_rights'] = $acl;
                        break;
                    }
                }
                if (!$dup) {
                    $cfgSources[$result[$i]['params']['name']] = $result[$i];
                }
            }
        } else {
            $notification->push($result);
        }
     }
}
/* End IMSP sources. */

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
                                             'format' => 'https://%s/freebusy/%s.ifb'),
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

// Load global configuration stanzas in .d directory
$directory = dirname(__FILE__) . '/sources.d';
if (file_exists($directory) && is_dir($directory)) {
    $sub_files = glob("$directory/*.php");
    if ($sub_files) {
        foreach ($sub_files as $sub_file) {
            ob_start();
            $success = include $sub_file;
            $output = ob_get_clean();
        }
    }
}
