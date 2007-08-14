<?php
// Warning: This file is auto-generated and might be overwritten by
//          univention-baseconfig.
//          Please edit the following file instead:
// Warnung: Diese Datei wurde automatisch generiert und kann durch
//          univention-baseconfig überschrieben werden.
//          Bitte bearbeiten Sie an Stelle dessen die folgende Datei:
//
// 	/etc/univention/templates/files/etc/horde/turba2/sources.php
//

/**
 * $Horde: turba/config/sources.php.dist,v 1.97.6.16 2005/11/07 10:03:26 jan Exp $
 *
 * This file is where you specify the sources of contacts available to users
 * at your installation. It contains a large number of EXAMPLES. Please
 * remove or comment out those examples that YOU DON'T NEED. There are a
 * number of properties that you can set for each server, including:
 *
 * title:       This is the common (user-visible) name that you want displayed
 *              in the contact source drop-down box.
 *
 * type:        The types 'ldap', 'sql', 'imsp' and 'prefs' are currently
 *              supported. Preferences-based address books are not intended
 *              for production installs unless you really know what you're
 *              doing - they are not searchable, and they won't scale well if
 *              a user has a large number of entries.
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
 *
 *   checksyntax:   Only applies to LDAP servers. If present, this value causes
 *                  the driver to inspect the LDAP schema for particular
 *                  attributes by the type defined in the corresponding schema
 *
 * map:         This is a list of mappings from the standard Turba attribute
 *              names (on the left) to the attribute names by which they are
 *              known in this contact source (on the right). Turba also
 *              supports composite fields. A composite field is defined by
 *              mapping the field name to an array containing a list of
 *              component fields and a format string (similar to a printf()
 *              format string). Here is an example:
 *              ...
 *              'name' => array('fields' => array('firstname', 'lastname'),
 *                              'format' => '%s %s'),
 *              'firstname' => 'object_firstname',
 *              'lastname' => 'object_lastname',
 *              ...
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
 * strict:      A list of native field/attribute names that must always be
 *              matched exactly in a search.
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
 *              must have support for using this. Currently SQL only.
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
/*$cfgSources['localsql'] = array(
    'title' => _("My Address Book"),
    'type' => 'sql',
    // The default connection details are pulled from the Horde-wide SQL
    // connection configuration.
    //
    // The old example illustrates how to use an alternate database
    // configuration.
    //
    // New Example:
    'params' => array_merge($conf['sql'], array('table' => 'turba_objects')),

    // Old Example:
    // 'params' => array(
    //     'phptype' => 'mysql',
    //     'hostspec' => 'localhost',
    //     'username' => 'horde',
    //     'password' => '*****',
    //     'database' => 'horde',
    //     'table' => 'turba_objects',
    //     'charset' => 'iso-8859-1'
    // ),
    'map' => array(
        '__key' => 'object_id',
        '__owner' => 'owner_id',
        '__type' => 'object_type',
        '__members' => 'object_members',
        '__uid' => 'object_uid',
        'name' => 'object_name',
        'email' => 'object_email',
        'alias' => 'object_alias',
        'homeAddress' => 'object_homeaddress',
        'workAddress' => 'object_workaddress',
        'homePhone' => 'object_homephone',
        'workPhone' => 'object_workphone',
        'cellPhone' => 'object_cellphone',
        'fax' => 'object_fax',
        'title' => 'object_title',
        'company' => 'object_company',
        'notes' => 'object_notes',
        'pgpPublicKey' => 'object_pgppublickey',
        'smimePublicKey' => 'object_smimepublickey',
        'freebusyUrl' => 'object_freebusyurl'
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
);*/

if (Util::extensionExists('ldap')) {
/**
 * A local address book in an LDAP directory. This implements a public
 * (shared) address book.
 * To store freebusy information in the LDAP directory, you'll need the
 * rfc2739.schema from
 * http://www.whitemiceconsulting.com/node/42
 */
/*$cfgSources['localldap'] = array(
    'title' => _("Shared Directory"),
    'type' => 'ldap',
    'params' => array(
        'server' => 'ldap.example.com',
        'port' => 389,
        'tls' => false,
        'root' => 'dc=example,dc=com',
        'bind_dn' => 'cn=admin,ou=users,dc=example,dc=com',
        'bind_password' => '********',
        'sizelimit' => 200,
        'dn' => array('cn'),
        'objectclass' => array('top',
                               'person',
                               'organizationalPerson',
                               'inetOrgPerson'),
        'scope' => 'one',
        'charset' => 'iso-8859-1',
        // Consult the LDAP schema to verify that all required attributes for
        // an entry are set and add them if needed.
        'checkrequired' => false,
        // Value used to fill in missing required attributes.
        'checkrequired_string' => ' ',
        // Check LDAP schema for valid syntax. If this is undefined an
        // address field is assumed to have postalAddress syntax; otherwise
        // the schema is consulted for the syntax to use.
        'checksyntax' => true,
        'version' => 3
    ),
    'map' => array(
        '__key' => 'dn',
        '__uid' => 'uid',
        'name' => 'cn',
        'email' => 'mail',
        'homePhone' => 'homephone',
        'workPhone' => 'telephonenumber',
        'cellPhone' => 'mobiletelephonenumber',
        'homeAddress' => 'homepostaladdress',
        // 'freebusyUrl' => 'calFBURL',
    ),
    'search' => array(
        'name',
        'email',
        'homePhone',
        'workPhone',
        'cellPhone',
        'homeAddress'
    ),
    'strict' => array(
        'dn',
    ),
    'export' => true,
    'browse' => true,
);*/

/**
 * A personal LDAP adressbook. This assumes that the login is
 * <username>@domain.com and that the users are stored on the same LDAP
 * server. Thus it is possible to bind with the username and password from
 * the user. For more info; please refer to the docs/LDAP file in the Turba
 * distribution.
 *
 * To store freebusy information in the LDAP directory, you'll need the
 * rfc2739.schema from
 * http://www.whitemiceconsulting.com/node/42
 */

// First we need to get the uid.
/*$uid = Auth::getBareAuth();
$basedn = 'dc=example,dc=com';
$cfgSources['personal_ldap'] = array(
    'title' => _("My Address Book"),
    'type' => 'ldap',
    'params' => array(
        'server' => 'localhost',
        'tls' => false,
        'root' => 'ou=' . $uid . ',ou=personal_addressbook,' . $basedn,
        'bind_dn' => 'uid=' . $uid . ',ou=People,' . $basedn,
        'bind_password' => Auth::getCredential('password'),
        'dn' => array('cn', 'uid'),
        'objectclass' => array('top',
                               'person',
                               'inetOrgPerson',
                               // 'calEntry',
                               'organizationalPerson'),
        'scope' => 'one',
        'charset' => 'utf-8',
        'version' => 3
    ),
    'map' => array(
        '__key' => 'dn',
        '__uid' => 'uid',
        'name' => 'cn',
        'email' => 'mail',
        'lastname' => 'sn',
        'title' => 'title',
        'company' => 'organizationname',
        'businessCategory' => 'businesscategory',
        'workAddress' => 'postaladdress',
        'workPostalCode' => 'postalcode',
        'workPhone' => 'telephonenumber',
        'fax' => 'facsimiletelephonenumber',
        'homeAddress' => 'homepostaladdress',
        'homePhone' => 'homephone',
        'cellPhone' => 'mobile',
        'notes' => 'description',
        // Evolution interopt attributes: (those that do not require the
        // evolution.schema)
        'office' => 'roomNumber',
        'department' => 'ou',
        'nickname' => 'displayName',
        'website' => 'labeledURI',

        // These are not stored on the LDAP server.
        'pgpPublicKey' => 'object_pgppublickey',
        'smimePublicKey' => 'object_smimepublickey',

        // From rfc2739.schema:
        // 'freebusyUrl' => 'calFBURL',

    ),
    'search' => array(
        'name',
        'email',
        'businessCategory',
        'title',
        'homePhone',
        'workPhone',
        'cellPhone',
        'homeAddress'
    ),
    'strict' => array(
        'dn',

    ),
    'export' => true,
    'browse' => true,
);*/

/**
 * Public netcenter, bigfoot, and verisign LDAP directories.
 */
/*$cfgSources['netcenter'] = array(
    'title' => _("Netcenter Member Directory"),
    'type' => 'ldap',
    'params' => array(
        'server' => 'memberdir.netscape.com',
        'port' => 389,
        'tls' => false,
        'root' => 'ou=member_directory,o=netcenter.com',
        'dn' => array('cn'),
        'objectclass' => 'person',
        'filter' => '',
        'scope' => 'sub',
        'charset' => 'iso-8859-1'
    ),
    'map' => array(
        '__key' => 'dn',
        'name' => 'cn',
        'email' => 'mail',
        'alias' => 'givenname'
    ),
    'search' => array(
        'name',
        'email',
        'alias'
    ),
    'strict' => array(
        'dn'
    ),
    'export' => false,
    'browse' => false,
);*/

/*$cfgSources['bigfoot'] = array(
    'title' => 'Bigfoot',
    'type' => 'ldap',
    'params' => array(
        'server' => 'ldap.bigfoot.com',
        'port' => 389,
        'tls' => false,
        'root' => '',
        'scope' => 'sub',
        'charset' => 'iso-8859-1'
    ),
    'map' => array(
        '__key' => 'dn',
        'name' => 'cn',
        'email' => 'mail',
        'alias' => 'givenname'
    ),
    'search' => array(
        'name',
        'email',
        'alias'
    ),
    'strict' => array(
        'dn'
    ),
    'export' => false,
    'browse' => false,
);*/

/*$cfgSources['verisign'] = array(
    'title' => _("Verisign Directory"),
    'type' => 'ldap',
    'params' => array(
        'server' => 'directory.verisign.com',
        'port' => 389,
        'tls' => false,
        'root' => '',
        'scope' => 'sub',
        'charset' => 'iso-8859-1'
    ),
    'map' => array(
        '__key' => 'dn',
        'name' => 'cn',
        'email' => 'mail'
    ),
    'search' => array(
        'name',
        'email'
    ),
    'strict' => array(
        'dn'
    ),
    'export' => false,
    'browse' => false,
);*/

// End LDAP check.
}

/**
 * A preferences-based adressbook. This will always be private. You can add
 * any attributes you like to the map and it will just work; you can also
 * create multiple prefs-based address books by changing the 'name' parameter.
 * This is best for address books that are expected to remain small; it's not
 * the most efficient, but it can't be beat for getting up and running
 * quickly, especially if you already have Horde preferences working. Note
 * that it is not searchable, though - searches will simply return the whole
 * address book.
 */
/*$cfgSources['prefs'] = array(
    'title' => _("Private Address Book"),
    'type' => 'prefs',
    'params' => array(
        'name' => 'prefs',
        'charset' => NLS::getCharset()
    ),
    'map' => array(
        '__key' => 'id',
        '__type' => '_type',
        '__members' => '_members',
        '__uid' => 'uid',
        'name' => 'name',
        'email' => 'mail',
        'alias' => 'alias'
    ),
    'search' => array(
        'name',
        'email',
        'alias'
    ),
    'strict' => array(
        'id',
        '_type',
    ),
    'export' => true,
    'browse' => true,
);*/

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
 */
// Check that IMSP is configured in Horde but fall through if there is no
// configuration at all - in case we don't have at least a 3.0.6 Horde
// install.  (In that case, be sure to change the params array below to suit
// your needs).
if (!empty($GLOBALS['conf']['imsp']['enabled']) ||
    !isset($GLOBALS['conf']['imsp']['enabled'])) {
    // First, get the user name to login to IMSP server with.
    $uid = $GLOBALS['prefs']->getValue('imsp_auth_user');
    $pass = $GLOBALS['prefs']->getValue('imsp_auth_pass');
    if (!strlen($uid)) {
        $uid = Auth::getBareAuth();
        $pass = Auth::getCredential('password');
    }
    // Note we always use the horde username to append to the key even if we
    // have an alternate username set in prefs.  This is to prevent the
    // (fringe) case where an IMSP username for one user might be a valid
    // horde username for another user.
    $cfgKey = 'IMSP_' . Auth::getAuth();
    $cfgSources[$cfgKey] = array(
        'title' => _("IMSP"),
        'type' => 'imsp',
        'params' => array(
            'server'  => $GLOBALS['conf']['imsp']['server'],
            'port'    => $GLOBALS['conf']['imsp']['port'],
            'auth_method' => $GLOBALS['conf']['imsp']['auth_method'],
            // socket, command, and auth_mechanism are for imtest driver.
            'socket'  => isset($GLOBALS['conf']['imsp']['socket']) ?
                         $GLOBALS['conf']['imsp']['socket'] . $uid . '.sck' :
                         '',
            'command' => isset($GLOBALS['conf']['imsp']['command']) ?
                         $GLOBALS['conf']['imsp']['command'] : '' ,
            'auth_mechanism' => isset($GLOBALS['conf']['imsp']['auth_mechanism']) ?
                                $GLOBALS['conf']['imsp']['auth_mechanism'] : '',
            'username' => $uid,
            'password' => $pass,
            'name' => $uid,
            'group_id_field' => 'group',
            'group_id_value' => 'group',
            'contact_ownership' => false,
            // Dynamically generated acl rights for current user.
            'my_rights' => '',
            // Flags this as the user's 'root' IMSP address book.
            'is_root' => true
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
        );

    /**
     * Get any other address books this user might be privy to.
     * The values for attributes such as 'export' and 'browse' for books
     * that are added below will be the same as the values set in the default
     * book above. Any entries defined explicitly in cfgSources[]
     * will override any entries gathered dynamically below.
     */
    require_once 'Net/IMSP/Utils.php';
    $result = Net_IMSP_Utils::getAllBooks($cfgSources[$cfgKey]);
    $count = 2;
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
                $cfgSources[sprintf('IMSP_%d', $count++)] = $result[$i];
            }
        }
    } else {
        $notification->push($result);
    }
}
/* End IMSP sources. */

/* Begin Kolab sources. */
if (!empty($GLOBALS['conf']['kolab']['enabled'])) {

    /* A global address book for a Kolab Server. This is typically a
     * read-only public directory, stored in the default Kolab LDAP server.
     * The user accessing this should have read permissions to the shared
     * directory in LDAP. */
    $cfgSources['kolab_global'] = array(
        'title' => _("Global Address Book"),
        'type' => 'ldap',
        'params' => array(
            'server' => $GLOBALS['conf']['kolab']['ldap']['server'],
            'port' => $GLOBALS['conf']['kolab']['ldap']['port'],
            'tls' => false,
            'root' => $GLOBALS['conf']['kolab']['ldap']['basedn'],
            'sizelimit' => 200,
            'dn' => array('cn'),
			'filter' => 'objectClass=inetOrgPerson',
            'objectclass' => array(
                'inetOrgPerson'
            ),
            'scope' => 'sub',
            #'charset' => 'iso-8859-1',
            'charset' => 'utf-8',
            'version' => 3,
            'bind_dn' => $GLOBALS['conf']['kolab']['ldap']['binddn'],
            'bind_password' => $GLOBALS['conf']['kolab']['ldap']['bindpw'],
        ),
        'map' => array(
            '__key'             => 'dn',
            'name'              => 'cn',
            'firstname'         => 'givenName',
            'lastname'          => 'sn',
            'email'             => 'mailPrimaryAddress',
#            'alias'             => 'alias',
            'title'             => 'title',
            'company'           => 'o',
            'workStreet'        => 'street',
            'workCity'          => 'l',
#            'workProvince'      => 'st',
            'workPostalCode'    => 'postalCode',
#            'workCountry'       => 'c',
#            'homePhone'         => 'homePhone',
            'workPhone'         => 'telephoneNumber',
#            'cellPhone'         => 'mobile',
#            'fax'               => 'fax',
            'notes'             => 'description',
#            'freebusyUrl'       => 'kolabHomeServer',
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
#            'workProvince',
            'workPostalCode',
#            'workCountry',
#            'homePhone',
            'workPhone',
#            'cellPhone',
#            'fax',
            'notes',
        ),
        'strict' => array(
            'dn',
        ),
        'export' => true,
        'browse' => true,
    );

    /**
     * The local address books for a Kolab user. These are stored in specially
     * flagged contact folder within the users Cyrus IMAP mailbox.
     */

    // This would usually get called at a later timepoint in turba/lib/base.php
    // but we need the list of shares right now
    require_once 'Horde/Share.php';
    $GLOBALS['turba_shares'] = &Horde_Share::singleton($registry->getApp());
    $books = Turba::listShares();

	/* create a default kolab addressbook for the user, if non exists */
    if( empty($books) ) {
        $params = array(
	        'sourceType' => 'kolab'
        );
        Turba::createShare( md5(mt_rand()), $params );
        $books = Turba::listShares();
    }

    foreach ($books as $folder => $share) {

        $cfgSources[$folder] =
            array(
                  'title' => $share->getName(),
                  'type' => 'kolab',
                  'params' =>
                  array(
                        'share' => $folder,
                        ),
                  'map' =>
                  array(
                        '__key'             => 'uid',
                        '__owner'           => 'owner',
                        //'__uid'             => 'uid',
                        'name'              => 'full-name',
                        'firstname'         => 'given-name',
                        'lastname'          => 'last-name',
                        'title'             => 'job-title',
                        'company'           => 'organization',
                        'notes'             => 'body',
                        'website'           => 'web-page',
                        'nickname'          => 'nick-name',
                        'email'             => 'smtp-address',
                        'homeStreet'        => 'home-street',
                        'homeCity'          => 'home-locality',
                        'homeProvince'      => 'home-region',
                        'homePostalCode'    => 'home-postal-code',
                        'homeCountry'       => 'home-country',
                        'workStreet'        => 'business-street',
                        'workCity'          => 'business-locality',
                        'workProvince'      => 'business-region',
                        'workPostalCode'    => 'business-postal-code',
                        'workCountry'       => 'business-country',
                        'homePhone'         => 'home1',
                        'workPhone'         => 'business1',
                        'cellPhone'         => 'mobile',
                        'fax'               => 'businessfax',
                        ),
                  'search' =>
                  array(
                        'name',
                        'firstname',
                        'lastname',
                        'email',
                        'title',
                        'company',
                        'homeStreet',
                        'homeCity',
                        'homeProvince',
                        'homePostalCode',
                        'homeCountry',
                        'workStreet',
                        'workCity',
                        'workProvince',
                        'workPostalCode',
                        'workCountry',
                        'homePhone',
                        'workPhone',
                        'cellPhone',
                        'fax',
                        'notes',
                        'website',
                        'nickname',
                        ),
                  'strict' =>
                  array(
                        'uid'
                        ),
                  'export' => true,
                  'browse' => true,
                  );
    }

}
/* End Kolab sources. */
