<?php
/**
 * $Horde: ingo/config/backends.php.dist,v 1.20.8.12 2008-12-15 02:33:07 chuck Exp $
 *
 * Ingo works purely on a preferred mechanism for server selection. There are
 * a number of properties that you can set for each backend:
 *
 * driver:       The Ingo_Driver driver to use to store the script on the
 *               backend server. Valid options:
 *                   'null'       --  No backend server
 *                   'timsieved'  --  Cyrus timsieved server
 *                   'vfs'        --  Use Horde VFS
 *                   'ldap'       --  LDAP server
 *
 * preferred:    This is the field that is used to choose which server is
 *               used. The value for this field may be a single string or an
 *               array of strings containing the hostnames to use with this
 *               server.
 *
 * hordeauth:    Ingo uses the current logged in username and password. If
 *               you want the full username@realm to be used to connect then
 *               set this to 'full' otherwise set this to true and just the
 *               username will be used to connect to the driver.
 *
 * params:       An array containing any additional information that the
 *               Ingo_Driver class needs.
 *
 * script:       The type of Ingo_Script driver this server uses.
 *               Valid options:
 *                   'imap'      --  IMAP client side filtering
 *                   'maildrop'  --  Maildrop scripts
 *                   'procmail'  --  Procmail scripts
 *                   'sieve'     --  Sieve scripts
 *
 * scriptparams: An array containing any additional information that the
 *               Ingo_Script driver needs.
 *
 * shares:       Some drivers support sharing filter rules with other users.
 *               Users can then configure filters for each other if they
 *               give them permissions to do so. If you want to enable this
 *               feature, you need to set this parameter to true.
 */

/* IMAP Example */
$backends['imap'] = array(
    'driver' => 'null',
    'preferred' => 'example.com',
    'hordeauth' => true,
    'params' => array(),
    'script' => 'imap',
    'scriptparams' => array(),
    'shares' => false
);

/* Maildrop Example */
$backends['maildrop'] = array(
    'driver' => 'vfs',
    'preferred' => 'example.com',
    'hordeauth' => true,
    'params' => array(
        // Hostname of the VFS server
        'hostspec' => 'ftp.example.com',
        // Name of the maildrop config file to write
        'filename' => '.mailfilter',
        // The VFS username to use, defaults to current user. If you want to
        // use a different user, you also need to disable 'hordeauth' above.
        // 'username' => 'user',
        // The VFS password to use, defaults to current user's password
        // 'password' => 'secret',
        // The path to the .mailfilter filter file, defaults to the filters'
        // owner's home directory.
        // You can use the following variables:
        //   %u = name of the filters' owner
        //   %d = domain name of the filters' owner
        //   %U = the 'username' from above
        // Example:
        //   '/data/maildrop/filters/%d/%u'
        //   This would be translated into:
        //   '/data/maildrop/filters/<filter_owners_domainname>/<filter_owners_username>/.mailfilter'
        // 'vfs_path' => '/path/to/maildrop',

        // VFS: FTP example
        // The VFS driver to use
        'vfstype' => 'ftp',
        // Port of the VFS server
        'port' => 21,
        // Specify permissions for uploaded files if necessary:
        // 'file_perms' => '0640',

        // VFS: SSH2 example
        // The VFS driver to use
        // 'vfstype' => 'ssh2',
        // Port of the VFS server
        // 'port' => 22,
    ),
    'script' => 'maildrop',
    'scriptparams' => array(
        // What path style does the IMAP server use ['mbox'|'maildir']?
        'path_style' => 'mbox',
        // Strip 'INBOX.' from the beginning of folder names in generated
        // scripts?
        'strip_inbox' => false,
        // An array of variables to append to every generated script.
        // Use if you need to set up specific environment variables.
        'variables' => array(
            // Example for the $PATH variable
            // 'PATH' => '/usr/bin'
        )
    ),
    'shares' => false
);

/* Procmail Example */
$backends['procmail'] = array(
    'driver' => 'vfs',
    'preferred' => 'example.com',
    'hordeauth' => true,
    'params' => array(
        // Hostname of the VFS server
        'hostspec' => 'ftp.example.com',
        // Name of the procmail config file to write
        'filename' => '.procmailrc',
        // The VFS username to use, defaults to current user. If you want to
        // use a different user, you also need to disable 'hordeauth' above.
        // 'username' => 'user',
        // The VFS password to use, defaults to current user's password
        // 'password' => 'secret',
        // The path to the .procmailrc filter file, defaults to the filters'
        // owner's home directory.
        // You can use the following variables:
        //   %u = name of the filters' owner
        //   %U = the 'username' from above
        // Example:
        //   '/data/procmail/filters/%u'
        //   This would be translated into:
        //   '/data/procmail/filters/<filter_owners_username>/.procmailrc'
        // 'vfs_path' => '/path/to/procmail',

        // If procmail needs an external command for mail delivery, you
        // can specify it below. You can also set a prefix for the mailbox name
        // eg. for /usr/local/sbin/dmail +INBOX
        // 'delivery_agent' => '/usr/local/sbin/dmail',
        // 'delivery_mailbox_prefix' => '+',

        // If you need procmail to be called from .forward in the user's home
        // directory, set the file and the content below:
        // 'forward_file' => '.forward',
        // 'forward_string' => '"|/usr/local/bin/procmail"',

        // if the GNU utilities cannot be found in the path
        // or have different names, you can specify their location below
        // 'date' => '/opt/csw/bin/gdate',
        // 'echo' => '/opt/csw/bin/gecho',
        // 'ls' => '/opt/csw/bin/gls',

        // VFS: FTP example
        // The VFS driver to use
        'vfstype' => 'ftp',
        // Port of the VFS server
        'port' => 21,

        // VFS: SSH2 example
        // The VFS driver to use
        // 'vfstype' => 'ssh2',
        // Port of the VFS server
        // 'port' => 22,
    ),
    'script' => 'procmail',
    'scriptparams' => array(
        // What path style does the IMAP server use ['mbox'|'maildir']?
        'path_style' => 'mbox',
        // An array of variables to append to every generated script.
        // Use if you need to set up specific environment variables.
        'variables' => array(
            // Example for the $PATH variable
            // 'PATH' => '/usr/bin',
            // Example for the $DEFAULT variable
            // 'DEFAULT' => '$HOME/Maildir',
            // Example for the $VACATION_DIR variable (used to store vacation files)
            // 'VACATION_DIR' => '$HOME',
        )
    ),
    'shares' => false
);

/* Sieve Example */
$backends['sieve'] = array(
    'driver' => 'timsieved',
    'preferred' => 'example.com',
    'hordeauth' => true,
    'params' => array(
        // Hostname of the timsieved server
        'hostspec' => 'mail.example.com',
        // Login type of the server
        'logintype' => 'PLAIN',
        // Enable/disable TLS encryption
        'usetls' => true,
        // Port number of the timsieved server
        'port' => 2000,
        // Name of the sieve script
        'scriptname' => 'ingo',
        // The following settings can be used to specify an administration
        // user to update all users' scripts. If you want to use an admin
        // user, you also need to disable 'hordeauth' above. You have to use
        // an admin user if you want to use shared rules.
        // 'username' => 'cyrus',
        // 'password' => '*****',
    ),
    'script' => 'sieve',
    'scriptparams' => array(),
    'shares' => false
);

/* sivtest Example */
$backends['sivtest'] = array(
    'driver' => 'sivtest',
    'preferred' => 'example.com',
    'hordeauth' => true,
    'params' => array(
        // Hostname of the timsieved server
        'hostspec' => 'mail.example.com',
        // Login type of the server
        'logintype' => 'GSSAPI',
        // Enable/disable TLS encryption
        'usetls' => true,
        // Port number of the timsieved server
        'port' => 2000,
        // Name of the sieve script
        'scriptname' => 'ingo',
        // Location of sivtest
        'command' => '/usr/bin/sivtest',
        // name of the socket we're using
        'socket' => Horde::getTempDir() . '/sivtest.'
            . md5(uniqid(rand())) . '.sock',
    ),
    'script' => 'sieve',
    'scriptparams' => array(),
    'shares' => false,
);

/* Sun ONE/JES Example (LDAP/Sieve) */
$backends['ldapsieve'] = array(
    'driver' => 'ldap',
    'preferred' => 'example.com',
    'hordeauth' => false,
    'params' => array(
        //
        // Hostname of the ldap server
        //
        'hostspec' => 'ldap.example.com',
        //
        // Port number of the timsieved server
        //
        'port' => 389,
        //
        // LDAP Protocol Version (default = 2).  3 is required for TLS.
        //
        'version' => 3,
        //
        // Whether or not to use TLS.  If using TLS, you MUST configure
        // OpenLDAP (either /etc/ldap.conf or /etc/ldap/ldap.conf) with the CA
        // certificate which signed the certificate of the server to which you
        // are connecting.  e.g.:
        //
        // TLS_CACERT /usr/share/ca-certificates/mozilla/Equifax_Secure_CA.crt
        //
        // You MAY have problems if you are using TLS and your server is
        // configured to make random referrals, since some OpenLDAP libraries
        // appear to check the certificate against the original domain name,
        // and not the referred-to domain.  This can be worked around by
        // putting the following directive in the ldap.conf:
        //
        // TLS_REQCERT never
        //
        'tls' => true,
        //
        // Bind DN (for bind and script distinguished names, %u is replaced
        // with username, and %d is replaced with the internet domain
        // components (e.g. "dc=example, dc=com") if available).
        //
        'bind_dn' => 'cn=ingo, ou=applications, dc=example, dc=com',
        //
        // Bind password.  If not provided, user's password is used (useful
        // when bind_dn contains %u).
        //
        'bind_password' => 'secret',
        //
        // How to find user object.
        //
        'script_base' => 'ou=People, dc=example, dc=com',
        'script_filter' => '(uid=%u)',
        //
        // Attribute script is stored in.  Will not touch non-Ingo scripts.
        //
        'script_attribute' => 'mailSieveRuleSource'
    ),
    'script' => 'sieve',
    'scriptparams' => array()
);

/* Kolab Example (using Sieve) */
if ($GLOBALS['conf']['kolab']['enabled']) {
    require_once 'Horde/Kolab.php';

    if (!is_callable('Kolab', 'getServer')) {
        $server = $GLOBALS['conf']['kolab']['imap']['server'];
    } else {
        $server = Kolab::getServer('imap');
    }

    $backends['kolab'] = array(
        'driver' => 'timsieved',
        'preferred' => '',
        'hordeauth' => 'full',
        'params' => array(
            'hostspec' => $server,
            'logintype' => 'PLAIN',
            'usetls' => false,
            'port' => $GLOBALS['conf']['kolab']['imap']['sieveport'],
            'scriptname' => 'kmail-vacation.siv'
        ),
        'script' => 'sieve',
        'scriptparams' => array(),
        'shares' => false
    );
}
