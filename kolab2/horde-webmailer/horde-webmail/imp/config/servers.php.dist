<?php
/**
 * $Horde: imp/config/servers.php.dist,v 1.50.2.23 2008-07-03 13:06:15 jan Exp $
 *
 * This file is where you specify what mail servers people using your
 * installation of IMP can log in to.
 *
 * Properties that can be set for each server:
 *
 * name: This is the plaintext, english name that you want displayed
 *       to people if you are using the drop down server list.
 *
 * server: The hostname of the mail server to connect to.
 *
 * hordeauth: If this parameter is present and true, then IMP will attempt
 *            to use the user's existing credentials (the username/password
 *            they used to log in to Horde) to log in to this source. If this
 *            parameter is 'full', the username will be used unmodified;
 *            otherwise everything after and including the first @ in the
 *            username will be stripped off before attempting authentication.
 *
 * protocol: One of the following strings:
 *             + 'imap/notls'
 *             + 'imap/ssl'
 *             + 'imap/tls'
 *             + 'pop3/notls'
 *             + 'pop3/ssl'
 *             + 'pop3/tls'
 *
 *           If using 'pop3/*' you will connect to a POP3 mail server and
 *           all folder options will be automatically turned off (POP3 does
 *           not support folders).  If you want folders (and for much
 *           improved performance) it is HIGHLY RECOMMENDED that IMAP should
 *           be used instead.
 *
 *           NOTE: Due to limitations within PHP, IMP can only support auto-
 *                 detection of namespace parameters with IMAP TLS connections
 *                 (e.g 'imap/tls') if using PHP version 5.1.0 or greater.
 *                 If using a version of PHP less than 5.1.0, the following
 *                 options are available:
 *                 1. RECOMMENDED - If a secure IMAP connection is needed, use
 *                    a direct connection to a SSL enabled IMAP port
 *                    (e.g. 'imap/ssl').
 *                 2. If you absolutely must use TLS, then it is REQUIRED to
 *                    define the 'namespace' parameter (see below).
 *
 *           The ssl and tls options will only work if you've compiled PHP
 *           against a SSL-enabled version of c-client, used the
 *           --with-imap-ssl and --with-openssl flags when compiling PHP,
 *           and you have a mail server server which supports SSL.
 *
 *           ** The test script can help automatically determine the   **
 *           ** correct protocol value to use.  See the 'Testing IMP'  **
 *           ** section of imp/docs/INSTALL for instructions on how to **
 *           ** access the test script.                                **
 *
 *           NOTE - If you are using a self-signed server certificate with
 *           either imap/ssl, imap/tls, pop3/ssl, or pop3/tls, you MUST add
 *           '/novalidate-cert' to the end of the protocol string. For imap,
 *           this would be 'imap/ssl/novalidate-cert' or
 *           'imap/tls/novalidate-cert', and for pop3 it would be
 *           'pop3/ssl/novalidate-cert' or 'pop3/tls/novalidate-cert'. This
 *           is necessary to tell c-client not to complain about the lack of
 *           a valid CA on the certificate.
 *
 * port: The port that the mail service/protocol you selected runs on.
 *       Default values:
 *         'pop3'    110
 *         'pop3s'   995
 *         'imap'    143
 *         'imaps'   993
 *
 *       ** The test script can help automatically determine the      **
 *       ** correct port value to use.  See the 'Testing IMP' section **
 *       ** of imp/docs/INSTALL for instructions on how to access the **
 *       ** test script.                                              **
 *
 * maildomain: What to put after the @ when sending mail. i.e. if you want
 *             all mail to look like 'From: user@example.com' set
 *             maildomain to 'example.com'. It is generally useful when
 *             the sending host is different from the mail receiving host. This
 *             will also be used to complete unqualified addresses when
 *             composing mail.
 *
 * smtphost: If specified, and $conf['mailer']['type'] is set to 'smtp',
 *           IMP will use this host for outbound SMTP connections.  This
 *           value overrides any existing $conf['mailer']['params']['host']
 *           value at runtime.
 *
 * smtpport: If specified, and $conf['mailer']['type'] is set to 'smtp',
 *           IMP will use this port for outbound SMTP connections.  This value
 *           overrides any existing $conf['mailer']['params']['port'] value at
 *           runtime.
 *
 * realm: ONLY USE REALM IF YOU ARE USING IMP FOR HORDE AUTHENTICATION,
 *        AND YOU HAVE MULTIPLE SERVERS AND USERNAMES OVERLAP BETWEEN
 *        THOSE SERVERS. If you only have one server, or have multiple
 *        servers with no username clashes, or have full user@example.com
 *        usernames, you DO NOT need a realm setting. If you set one, an
 *        '@' symbol plus the realm will be appended to the username that
 *        users log in to IMP with to create the username that Horde treats
 *        the user as. So with a realm of 'example.com', the username
 *        'jane' would be treated by Horde (NOT your IMAP/POP server) as
 *        'jane@example.com', and the username 'jane@example.com' would be
 *        treated as 'jane@example.com@example.com' - an occasion where you
 *        probably don't need a realm setting.
 *
 * preferred: Only useful if you want to use the same servers.php file
 *            for different machines: if the hostname of the IMP machine is
 *            identical to one of those in the preferred list, then the
 *            corresponding option in the select box will include SELECTED
 *            (i.e. it is selected per default). Otherwise the first entry
 *            in the list is selected.
 *
 * quota: Use this if you want to display a users quota status on various
 *        IMP pages. Set 'driver' equal to the mailserver and 'params'
 *        equal to any extra parameters needed by the driver (see the
 *        comments located at the top of imp/lib/Quota/[quotadriver].php
 *        for the parameters needed for each driver).
 *
 *        The optional 'format' parameter is supported by all drivers and
 *        specifies the formats of the quota messages in the user
 *        interface. The parameter must be specified as a hash with the four
 *        possible elements 'long', 'short', 'nolimit_long', and
 *        'nolimit_short' with according versions of the quota message. The
 *        strings will be passed through sprintf().
 *        These are the built-in default values, though they might look
 *        differently in some translations:
 *          'long'          -- Quota status: %.2f MB / %.2f MB  (%.2f%%)
 *          'short'         -- %.0f%% of %.0f MB
 *          'nolimit_long'  -- Quota status: %.2f MB / NO LIMIT
 *          'nolimit_short' -- %.0f MB
 *
 *        Currently available drivers:
 *          false        --  Disable quota checking (DEFAULT).
 *
 *          'command'    --  Use the UNIX quota command to handle quotas.
 *          'hook'       --  Use the _imp_hook_quota function to handle quotas.
 *          'imap'       --  Use the IMAP QUOTA extension to handle quotas.
 *                           You must be connecting to a IMAP server capable
 *                           of the QUOTAROOT command to use this driver.
 *          'logfile'    --  Allow quotas on servers where IMAP Quota
 *                           commands are not supported, but quota info
 *                           appears in the servers messages log for the IMAP
 *                           server.
 *          'maildir'    --  Use Maildir++ quota files to handle quotas.
 *          'mdaemon'    --  Use Mdaemon servers to handle quotas.
 *          'mercury32'  --  Use Mercury/32 servers to handle quotas.
 *          'sql'        --  Use arbitrary SQL queries to handle quotas.
 *
 * admin: Use this if you want to enable mailbox management for administrators
 *        via Horde's user administration interface.  The mailbox management
 *        gets enabled if you let IMP handle the Horde authentication with the
 *        'application' authentication driver.  Your IMAP server needs to
 *        support mailbox management via IMAP commands.
 *        Do not define this value if you do not want mailbox management.
 *
 * acl: Use this if you want to use Access Control Lists (folder sharing)
 *      Set 'driver' equal to the type of ACL your server supports and
 *      'params' to an array containing any additional parameters the
 *      driver needs. Not all IMAP servers currently support this
 *      feature.
 *
 *      At present the only drivers supported are 'rfc2086' and 'rfc4314' (in
 *      Horde 3.1+), neither of which require any parameters.
 *
 *      SECURITY NOTE: If you do not have the PEAR Auth_SASL module
 *      installed, the 'rfc2086' driver will send user passwords to the
 *      IMAP server in plain text when retrieving ACLs.
 *
 *
 * *** The following options should NOT be set unless you REALLY know what ***
 * *** you are doing! FOR MOST PEOPLE, AUTO-DETECTION OF THESE PARAMETERS  ***
 * *** (the default if the parameters are not set) SHOULD BE USED!         ***
 *
 * namespace: The list of namespaces that exist on the server.  This entry
 *            must be an array. Example:
 *            'namespace' => array('#shared/', '#news/', '#ftp/', '#public/')
 *            This parameter must be set if using a TLS connection.
 *            Additionally, this parameter may be set if not using a TLS
 *            connection and you want to allow access to namespaces that may
 *            not be publicly advertised by the IMAP server (see RFC
 *            2342 [3]). These additional namespaces will be added to the list
 *            of available namespaces returned by the server.
 *
 * imap_config: Manually set IMAP server configuration information. Please see
 *              http://wiki.horde.org/ImpImapConfig for information on this
 *              parameter.  THIS PARAMETER IS NOT OFFICIALLY SUPPORTED BY THE
 *              HORDE PROJECT.  This entry must be an array with the following
 *              elements:
 *              'namespace' - (array) The namespace configuration of the
 *                            server.  See the return from
 *                            IMAP_Client::getNamespace() (located in
 *                            imp/lib/IMAP/Client.php) for the structure of
 *                            this array.
 *              'search_charset' - (array) A list of charsets the IMAP server
 *                                 supports for searches.
 *
 * timeout: Manually set server timeouts. This option only works with PHP >=
 *          4.3.3. This entry must be an array with the following possible
 *          elements (if an element is missing, the default value is used):
 *          IMAP_OPENTIMEOUT - (integer) The timeout for open actions.
 *          IMAP_READTIMEOUT - (integer) The timeout for read actions.
 *          IMAP_WRITETIMEOUT - (integer) The timeout for write actions.
 *          IMAP_CLOSETIMEOUT - (integer) The timeout for close actions.
 *
 * login_tries: Manually set the number of login tries we make to the server.
 *              The PHP imap_open() function will try to login 3 times to a
 *              server before failing.  This value indicates the number of
 *              times we call imap_open() before IMP fails (we pause one second
 *              between imap_open() calls). The default value is 3 (meaning IMP
 *              may attempt to login to the server 9 times).  If you have a
 *              mail server that will lock out an account if a certain number
 *              of incorrect login attempts occur within a certain period of
 *              time, you may want to set this to a lower value.  The minimum
 *              value for this setting is 1.
 */

/* Any entries whose key value ('foo' in $servers['foo']) begin with '_'
 * (an underscore character) will be treated as prompts, and you won't be
 * able to log in to them. The only property these entries need is 'name'.
 * This lets you put labels in the list, like this example: */
$servers['_prompt'] = array(
    'name' => _("Choose a mail server:")
);

/* Example configurations: */

$servers['imap'] = array(
    'name' => 'IMAP Server',
    'server' => 'imap.example.com',
    'hordeauth' => false,
    'protocol' => 'imap/notls',
    'port' => 143,
    'maildomain' => 'example.com',
    'smtphost' => 'smtp.example.com',
    'smtpport' => 25,
    'realm' => '',
    'preferred' => '',
);

$servers['cyrus'] = array(
    'name' => 'Cyrus IMAP Server',
    'server' => 'cyrus.example.com',
    'hordeauth' => false,
    'protocol' => 'imap/notls',
    'port' => 143,
    'maildomain' => 'example.com',
    'smtphost' => 'smtp.example.com',
    'smtpport' => 25,
    'realm' => '',
    'preferred' => '',
    'admin' => array(
        'params' => array(
            'login' => 'cyrus',
            'password' => 'cyrus_pass',
            // The 'userhierarchy' parameter defaults to 'user.'
            // If you are using a nonstandard hierarchy for personal
            // mailboxes, you will need to set it here.
            'userhierarchy' => 'user.',
            // Although these defaults are normally all that is required,
            // you can modify the following parameters from their default
            // values.
            'protocol' => 'imap/notls',
            'hostspec' => 'localhost',
            'port' => 143
        )
    ),
    'quota' => array(
        'driver' => 'imap',
        'params' => array('hide_quota_when_unlimited' => true),
    ),
    'acl' => array(
        'driver' => 'rfc2086',
    ),
);

$servers['pop'] = array(
    'name' => 'POP3 Server',
    'server' => 'pop.example.com',
    'hordeauth' => false,
    'protocol' => 'pop3',
    'port' => 110,
    'maildomain' => 'example.com',
    'smtphost' => 'smtp.example.com',
    'smtpport' => 25,
    'realm' => '',
    'preferred' => '',
);

$servers['exchange'] = array(
    'name' => 'Exchange 5.5 server',
    'server' => 'exchange.example.com',
    'hordeauth' => false,
    'protocol' => 'imap',
    'port' => 143,
    'maildomain' => '',
    'smtphost' => 'smtp.example.com',
    'realm' => '',
    'preferred' => '',
);

if ($GLOBALS['conf']['kolab']['enabled']) {
    require_once 'Horde/Kolab.php';

    if (!is_callable('Kolab', 'getServer')) {
        $server = $GLOBALS['conf']['kolab']['imap']['server'];
    } else {
        $server = Kolab::getServer('imap');
    }

    $servers['kolab'] = array(
        'name' => 'Kolab Cyrus IMAP Server',
        'server' => $server,
        'hordeauth' => 'full',
        'protocol' => 'imap/notls/novalidate-cert',
        'port' => $GLOBALS['conf']['kolab']['imap']['port'],
        'maildomain' => $GLOBALS['conf']['kolab']['imap']['maildomain'],
        'realm' => '',
        'preferred' => '',
        'quota' => array(
            'driver' => 'imap',
            'params' => array('hide_quota_when_unlimited' => true),
        ),
        'acl' => array(
            'driver' => 'rfc2086',
        ),
    );
}
