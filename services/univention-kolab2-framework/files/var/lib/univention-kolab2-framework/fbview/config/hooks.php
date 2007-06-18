<?php
/**
 * Horde Hooks configuration file.
 *
 * This file is where you define any hooks, for preferences or general
 * Horde use, that your installation uses. The functions in this file
 * can vastly change how your installation behaves, so make sure to
 * test out any changes here before doing them in a production
 * environment.
 *
 * Hook function names are automatically determined. The format of the
 * name is:
 *
 * _<type of hook>_hook_<name of hook>.
 *
 * Types of hooks that are defined in this file are 'prefs' (hooks to set the
 * value of preferences), 'horde' (hooks for the Horde  Framework scripts) and
 * 'app' (where app is any Horde application name, like 'imp') hooks that are
 * application specific.
 *
 * So, a hook to set the preference 'theme' would be named "_prefs_hook_theme".
 *
 * NOTE 1: Having a hook function in this file does NOT mean that the hook will
 * automatically be used. YOU MUST enable the hook. For preferences, set
 * 'hook' => true in that preferences attributes; for other hooks, there will be * a configuration option in each application's conf.php file such as
 * $conf['hooks']['hookname'] which must be set to true.
 *
 * NOTE 2: Preferences hooks are ONLY executed on login. Preferences are cached
 * during a users session and, to avoid unnecessary overhead every time a
 * preference is accessed, the results of hooks are cached as well. This leads
 * to ...
 *
 * NOTE 3: Any preference that is NOT LOCKED, that is set by a hook, WILL BE
 * SAVED WITH THAT VALUE. This means several things:
 *  1) Users will get the results of the hook set for them in their preferences. *  2) By virtue of this, the next time they log in and load their preferences,
 *     the hook will NOT be called, because in their last session, we saved the
 *     results of the hook for them. However, if the preference is locked, the
 *     result of the hook will never be saved.
 *
 * $Horde: horde/config/hooks.php.dist,v 1.62 2004/04/21 19:05:00 chuck Exp $
 */

// Example theme hook function. This shows how you can access things like the
// currently logged in user, global variables, server config, etc. It isn't,
// however, something you probably want to actually use in production, by virtue
// of demonstrating all those. :)
if (!function_exists('_prefs_hook_theme')) {
    function _prefs_hook_theme($username = null)
    {
        if (Auth::getAuth() != 'chuck') {
            return 'mozilla';
        }

        global $registry;
        switch ($registry->getApp()) {
        case 'imp':
            return 'brown';

        case 'turba':
            return 'orange';

        case 'kronolith':
            return 'green';

        default:
            return '';
        }
    }
}

// Example from_addr hook function. THIS FUNCTION ASSUMES THAT YOU ARE USING AN
// LDAP SERVER and that your /etc/ldap.conf or wherever it is correctly set to a
// valid host.
//
// You get passed NOTHING; you are responsible for bringing in to scope any
// information you need. You can "global" anything else you need. Return an
// address - either just the user@ side or a full address - and it will be used.
//
// If you want to use this code you will need to uncomment it below.
if (!function_exists('_prefs_hook_from_addr')) {
    /*
    function _prefs_hook_from_addr($name = null)
    {
        if (is_null($name)) {
            $name = Auth::getAuth();
        }
        if (!empty($name)) {
            $base_context = 'o=myorg';
            $scope = 'sub';

            // You will probably need to replace cd= with uid=; this
            // syntax is for Netware 5.1 nldap.
            $cmd  = '/usr/bin/ldapsearch -b ' . $base_context . ' -s ' . $scope . ' cn=';
            $cmd .= escapeShellCmd(Auth::getAuth());
            $cmd .= ' | /usr/bin/grep mail | /usr/bin/awk \'{print $2}\'';
            $mails = `$cmd`;
            $mail_array = explode("\n", $mails);

            // Send back the first email found, not the whole list.
            $mail = $mail_array['0'];

            // If no email address is found, then the login name will
            // be used.
            return (empty($mail) ? '' : $mail);
        }

        return '';
    }
    */

    // Here is another way of doing the same thing.

    /*
    function _prefs_hook_from_addr($user = null)
    {
        $ldapServer = '172.31.0.236';
        $ldapPort = '389';
        $searchBase = 'o=myorg';

        $ds = @ldap_connect($ldapServer, $ldapPort);

        if (is_null($user)) {
            $user = Auth::getAuth();
        }

        // You will probably need to replace cn= with uid=; this
        // syntax is for Netware 5.1 nldap.
        $searchResult = @ldap_search($ds, $searchBase, 'cn=' . $user);
        $information = @ldap_get_entries($ds, $searchResult);
        if ($information[0]['mail'][0] != '') {
            $name = $information[0]['mail'][0];
        } else {
            $name = $information[0]['cn'][0];
        }

        ldap_close($ds);

        return (empty($name) ? $user : $name);
    }
    */
}

// Here is an example signature hook function to set the signature from the
// system taglines file; the string "%TAG%" (if present in a user's signature)
// will be replaced by the content of the file "/usr/share/tagline" (generated
// by the "TaRT" utility).
//
// Notice how we global in the $prefs array to get the user's current signature.
if (!function_exists('_prefs_hook_signature')) {
    function _prefs_hook_signature($username = null)
    {
        $sig = $GLOBALS['prefs']->getValue('signature');
        if (preg_match('/%TAG%/', $sig)) {
            $tag = `cat /usr/share/tagline`;
            $sig = preg_replace('|%TAG%|', $tag, $sig);
        }
        return $sig;
    }
}

// IE on Mac hangs when there are several icons to be loaded. At least on some 
// systems. This hook disables the show_icons preference from Krononlith for
// these browsers.
if (!function_exists('_prefs_hook_show_icons')) {
    function _prefs_hook_show_icons()
    {
        global $browser;
        if ($browser->getPlatform() == 'mac' && $browser->getBrowser() == 'msie') {
            return false;
        } else {
            return true;
        }
    }
}

// This hook is called when a user submits a signup request.  It allows
// a chance to alter or validate the data submitted by a user before any
// attempts are made to add them to the system.
if (!function_exists('_horde_hook_signup_preprocess')) {
    function _horde_hook_signup_preprocess($info) {
        $info['user_name'] = String::lower($info['user_name']);
        return $info;
    }
}

// This hook is called when a signup is queued for administrative approval.
// This example sends a notification message to the web server
// administrator's e-mail address.
if (!function_exists('_horde_hook_signup_queued')) {
    function _horde_hook_signup_queued_walkdata($fields, $data) 
    {
        $msg = '';
        foreach ($data as $field => $value) {
            if ($field == 'password' || $field == 'url') {
                continue;
            }

            if (is_array($value)) {
                $msg .= _horde_hook_signup_queued_walkdata($fields, $value);
            } else {
                $field = isset($fields[$field]['label']) ?
                         $fields[$field]['label'] : $field;
                $msg .= "$field: $value\n";
            }
        }
        return $msg;
    } 

    function _horde_hook_signup_queued($userID, $data) 
    {
        require_once 'Mail.php';
        global $conf, $registry;

        $headers = array(
            'To'      => $_SERVER['SERVER_ADMIN'],
            'From'    => $_SERVER['SERVER_ADMIN'],
            'Subject' => 'New ' . $registry->getParam('name', 'horde') . ' Signup'
        );

        $extraFields = Horde::callHook('_horde_hook_signup_getextra');

        $msg  = _("A new signup has been received and is awaiting your approval.");
        $msg .= "\n\n";
        $msg .= _horde_hook_signup_queued_walkdata($extraFields, $data);
        $msg .= "\n";
        $msg .= sprintf(_("You can approve this signup at %s"), Horde::applicationUrl('admin/user.php', true, -1));

        $mailer = &Mail::factory($conf['mailer']['type'], $conf['mailer']['params']);
        return $mailer->send($_SERVER['SERVER_ADMIN'], $headers, $msg);
    }
}

// Here is an example _horde_hook_preauthenticate that make Horde respect the
// Unix convention of not allowing login when a file named /etc/nologin exist.
// This function get passed the username, credential and realm information but
// they are not used in this example.
if (!function_exists('_horde_hook_preauthenticate')) {
    function _horde_hook_preauthenticate($userID, $credential, $realm)
    {
        return !file_exists('/etc/nologin');
    }
}

// Here is an example of validating the user's right to login to Horde by
// consulting group membership in an LDAP directory.  That way, if your Horde
// installation is configured to authenticate against IMP which in turn
// authenticate via IMAP, it is still possible to limit access to Horde by group
// membership.  The following example had been made with an MS Active Directory 
// in mind.  Note that if the LDAP directory is unavailable or some other error 
// occur, authentication will fail.
if (!function_exists('_horde_hook_postauthenticate')) {
    function _horde_hook_postauthenticate($userID, $credential, $realm)
    {
        $ldapServer = 'ad.example.com';
        $ldapPort = '389';
        // Note that credential is sent plain-text in this case, so don't use
        // privileged account here or setup SSL (by using port 636 above).
        $binddn = 'cn=WithoutPrivilege,dc=ulaval-dev,dc=ca';
        $bindpw = 'Remember this is sent in the clear unless SSL is used';
        $searchBase = 'ou=People,dc=example,dc=com';
        // Attribute to match $userID against in search
        $userAttr = 'sAMAccountName'; 
        // Group membership attribute, need to be all lowercase
        $groupAttr = 'memberof'; 
        // Attribute to check for right to use Horde
        $groupdn = 'cn=HordeUser,ou=People,dc=example,dc=com'; 
        $ret = true;

        $ds = @ldap_connect($ldapServer, $ldapPort);

        if (@ldap_bind($ds, $binddn, $bindpw)) {
            $searchResult = @ldap_search($ds, $searchBase, $userAttr . '=' . $userID, array($groupAttr), 0, 1, 5);
            if ($information = @ldap_get_entries($ds, $searchResult)) {
                // make pattern case-insensitive
                $pattern = '/' . $groupdn . '/i'; 
                foreach ($information[0][$groupAttr] as $group) {
                    if (preg_match($pattern, $group)) {
                        $ret = true;
                        break;
                    }
                }
            }
        }

        ldap_close($ds);
        return $ret;
    }
}

// Here is an example of creating credentials needed by the LDAP Auth driver for
// adding/deleting/updating users.
if (!function_exists('_horde_hook_authldap')) {
    function _horde_hook_authldap($userID, $credentials = null)
    {
        $entry['dn'] = 'uid=' . $userID . ',ou=People,dc=example.com';
        if (isset($credentials) && isset($credentials['user_fullname'])) {
            $entry['cn'] = $credentials['user_fullname'];
        } else {
            $entry['cn'] = $userID;
        }
        $entry['sn'] = $userID;
        $entry['objectclass'][0] = 'top';
        $entry['objectclass'][1] = 'person';
        $entry['objectclass'][2] = 'qmailuser';
        $entry['objectclass'][3] = 'CourierMailACcount';
        $entry['mailhost'] = 'mail.example.com';
        $entry['mailMessageStore'] = '/home/mail/' . $userID;
        $entry['homeDirectory'] = '/home/mail/' . $userID;
        $entry['mailbox'] = $entry['homeDirectory'] . '/Maildir';
        $entry['uid'] = $userID;
        $entry['accountStatus'] = 'active';
        $entry['mailQuota'] = '104857600S';
        $entry['mail'] = $userID;
        $entry['uidNumber'] = 501;
        $entry['gidNumber'] = 501;

        // need to check for new users (password) and edited users (user_pass_2)
        if (isset($credentials) && isset($credentials['password'])) {
            $entry['userPassword'] =  '{MD5}' . base64_encode(mHash(MHASH_MD5, $credentials['password']));
        } else if (isset($credentials) && isset($credentials['user_pass_2'])) {
            $entry['userPassword'] =  '{MD5}' . base64_encode(mHash(MHASH_MD5, $credentials['user_pass_2']));
        }
        $entry['deliveryMode'] = 'nolocal';
        return $entry;
    }
}

// Here is an example fullname hook function to set the fullname from the GECOS
// information in the passwd file.
if (!function_exists('_prefs_hook_fullname')) {
    function _prefs_hook_fullname($user = null)
    {
        if (is_null($user)) {
            $user = Auth::getBareAuth();
        }
        $array = posix_getpwnam($user);
        $gecos_array = explode(',', $array['gecos']);
        return (empty($gecos_array) ? $user : $gecos_array[0]);
    }
}

// This is another example of how to get the user's full name, in this case from// an ldap server. In this example we look if a Spanish name exists and return
// this or the standard 'cn' entry if not.
if (!function_exists('_prefs_hook_fullname')) {
    function _prefs_hook_fullname($user = null)
    {
        $ldapServer = 'ldap.example.com';
        $ldapPort = '389';
        $searchBase = 'ou=people,o=example.com';
        $ldapcharset = 'utf-8';
        $outputcharset = NLS::getCharset();

        $ds = @ldap_connect($ldapServer, $ldapPort);

        if (is_null($user)) {
            $user = Auth::getAuth();
        }
        $searchResult = @ldap_search($ds, $searchBase, 'uid=' . $user);
        $information = @ldap_get_entries($ds, $searchResult);
        if ($information[0]['cn;lang-es'][0] != '') {
            $name = $information[0]['cn;lang-es'][0];
        } else {
            $name = $information[0]['cn'][0];
        }

        ldap_close($ds);

        $name = String::convertCharset($name, $ldapcharset, $outputcharset);
        return (empty($name) ? $user : $name);
    }
}

// Here is an example _username_hook_frombackend function. It appends the
// virtual domain to the user name.
//
// ex. $HTTP_HOST = 'mail.mydomain.com', $userID = 'myname' returns:
//   'myname@mydomain.com'
if (!function_exists('_username_hook_frombackend')) {
    function _username_hook_frombackend($userID)
    {
        $vdomain = getenv('HTTP_HOST');
        $vdomain = preg_replace('|^mail\.|i', '', $vdomain);
        $vdomain = String::lower($vdomain);

        return $userID . '@' . $vdomain;
    }
}

// Here is an example _username_hook_tobackend function as a counterpart of the
// previous example. It strips the virtual domain from the user name.
//
// ex. $HTTP_HOST = 'mail.mydomain.com', $userID = 'myname' returns:
//   'myname@mydomain.com'
if (!function_exists('_username_hook_tobackend')) {
    function _username_hook_tobackend($userID)
    {
        $vdomain = getenv('HTTP_HOST');
        $vdomain = preg_replace('|^mail\.|i', '', $vdomain);
        $vdomain = '@' . String::lower($vdomain);

        if (substr($userID, -strlen($vdomain)) == $vdomain) {
            $userID = substr($userID, 0, -strlen($vdomain));
        }

        return $userID;
    }
}

// Here is an example _username_hook_frombackend function. It converts the user
// name to all lower case. This might be necessary if an authentication backend
// is case insensitive to take into account that Horde's preference system is
// case sensitive.
//
// ex. $userID = 'MyName' returns: 'myname'
if (!function_exists('_username_hook_frombackend')) {
    function _username_hook_frombackend($userID)
    {
        return String::lower($userID);
    }
}

// Here is an example _horde_hook_signup_getextra function. It returns any extra
// fields which need to be filled in when a non registered user wishes to sign
// up.
// The example here takes the hypothetical case where we would want to store
// extra information about a user into a turba sql address book. All this
// function does then is to include the attributes.php file from the turba
// config directory and return the $attributes array.
// Otherwise any structure that would return an array with the following syntax
// would be valid:
//   $somearray['somefieldname'] = array(...
//      label    - the text that the user will see attached to this field
//      type     - any allowed Horde_Form field type
//      params   - any allowed parameter to Horde_Form field types
//      required - boolean, true or false whether this field is mandatory
//      readonly - boolean, true or false whether this editable
//      desc     - any help text attached to the field
// NOTE: You DO NEED Turba to be correctly installed before you can use this
// example below.
if (!function_exists('_horde_hook_signup_getextra')) {
    function _horde_hook_signup_getextra()
    {
        global $registry;
        require $registry->getParam('fileroot', 'turba') . '/config/attributes.php';
        return $attributes;
    }
}

// Following on from the example in the above function, this is how a sample
// _horde_hook_signup_addextra function would look like.
// Here we connect to the database using the sql parameters configured in $conf
// and store the extra fields in turba_objects, using the $userId as the key for
// the object and values from the $extra array.
// You could create your own sql syntax or code to store this in whichever
// backend you require.
// NOTE: You DO NEED Turba to be correctly installed before you can use this
// example below. It also assumes that you are using an SQL backend.
if (!function_exists('_horde_hook_signup_addextra')) {
    function _horde_hook_signup_addextra($userID, $extra)
    {
        global $conf;

        require_once 'DB.php';
        $_db = &DB::connect($conf['sql'], true);

        $fields = array();
        $values = array();
        foreach ($extra as $field => $value) {
            $fields[] = 'object_' . String::lower($field);
            $values[] = $_db->quote(String::convertCharset($value, NLS::getCharset(), $conf['sql']['charset']));
        }
        $fields[] = 'object_id';
        $values[] = $_db->quote($userID);

        $query  = 'INSERT INTO turba_objects ( owner_id, ' . implode(', ', $fields) . ')';
        $query .= ' VALUES ( \'admin\', ' . implode(', ', $values) . ')';
        $result = $_db->query($query);

        return DB::isError($result) ? $result : true;
    }
}

// Here is an example _imp_hook_trailer function to set the trailer from the
// system taglines file; the string "@@TAG@@" (if present in a trailer) will be
// replaced by the content of the file "/usr/share/tagline" (generated by the
// "TaRT" utility).
if (!function_exists('_imp_hook_trailer')) {
    function _imp_hook_trailer($trailer)
    {
        if (preg_match('/@@TAG@@/', $trailer)) {
            $tag = `cat /usr/share/tagline`;
            $trailer = preg_replace('|@@TAG@@|', $tag, $trailer);
        }
        return $trailer;
    }
}

// Here is an another example _imp_hook_trailer function to set the trailer from// the LDAP directory for each domain. This function replaces the current
// trailer with the data it gets from ispmanDomainSignature.
if (!function_exists('_imp_hook_trailer')) {
    function _imp_hook_trailer($trailer)
    {
        $vdomain = getenv('HTTP_HOST');
        $vdomain = preg_replace('|^.*?\.|i', '', $vdomain);
        $vdomain = String::lower($vdomain);
        $ldapServer = 'localhost';
        $ldapPort = '389';
        $searchBase = 'ispmanDomain=' . $vdomain  . ",o=ispman";

        $ds = @ldap_connect($ldapServer, $ldapPort);
        $searchResult = @ldap_search($ds, $searchBase, 'uid=' . $vdomain);
        $information = @ldap_get_entries($ds, $searchResult);
        $trailer= $information[0]['ispmandomainsignature'][0];
        ldap_close($ds);

        return $trailer;
    }
}

// Here is an example _imp_hook_vinfo function. If $type == 'vdomain', this
// function returns the HTTP_HOST variable after removing the 'mail.' subdomain.
//
// If $type == 'username', this function returns a unique username composed of
// $_SESSION['imp']['user'] + vdomain.
//
// ex. $HTTP_HOST = 'mail.mydomain.com', $_SESSION['imp']['user'] = 'myname':
//   $vdomain  = 'mydomain.com'
//   $username = 'myname_mydomain_com'
if (!function_exists('_imp_hook_vinfo')) {
    function _imp_hook_vinfo($type = 'username')
    {
        $vdomain = getenv('HTTP_HOST');
        $vdomain = preg_replace('|^mail\.|i', '', $vdomain);
        $vdomain = String::lower($vdomain);

        if ($type == 'username') {
            return preg_replace('|\.|', '_', $_SESSION['imp']['user'] . '_' . $vdomain);
        } elseif ($type == 'vdomain') {
            return $vdomain;
        } else {
            return PEAR::raiseError('invalid type: ' . $type);
        }
    }
}

// Here is an example of the _imp_hook_fetchmail_filter function to run
// SpamAssassin on email before it is written to the mailbox.
// Note: to use the spamassassin instead of spamd, change 'spamc' to
// 'spamassassin -P' and add any other important arguments, but realize spamc
// is MUCH faster than spamassassin.
// WARNING: Make sure to use the --noadd-from filter on spamd or spamassassin
if (!function_exists('_imp_hook_fetchmail_filter')) {
    function _imp_hook_fetchmail_filter($message)
    {
        // Where does SpamAssassin live, and what username should we use
        // for preferences?
        $cmd = '/usr/local/bin/spamc';
        $username = Auth::getAuth();
        // If you use the _sam_hook_username() hook, uncomment the next line
        //$username = _sam_hook_username($username);
        $username = escapeshellarg($username);

        // Also, we remove the file ourselves; this hook may be called
        // hundreds of times per run depending on how many messages we fetch
        $file = Horde::getTempFile('horde', false);

        // Call SpamAssassin; pipe the new message to our tempfile
        $fp = popen("$cmd -u $username > $file", 'w');
        fwrite($fp, $message);
        pclose($fp);

        // Read the new message from the temporary file
        $fp = fopen($file, 'r');
        $message = fread($fp, filesize($file));
        fclose($fp);
        unlink($file);
        return $message;
    }
}

// Here is an example signature hook function to set the signature from the
// system taglines file; the string "%TAG%" (if present in a user's signature)
// will be replaced by the content of the file "/usr/share/tagline" (generated
// by the "TaRT" utility).
//
// Notice how we global in the $prefs array to get the user's current signature.
if (!function_exists('_imp_hook_signature')) {
    function _imp_hook_signature($sig)
    {
        if (preg_match('/%TAG%/', $sig)) {
            $tag = `cat /usr/share/tagline`;
            $sig = preg_replace('/%TAG%/', $tag, $sig);
        }

        return $sig;
    }
}

// This is an example hook function for the IMP redirection scheme. This
// function is called when the user opens a mailbox in IMP, and allows
// the client to be redirected based on the mailbox name. The return
// value of this function should be a valid page within a horde application
// which will be placed in a "Location" header to redirect the client.
// The only parameter is the name of the mailbox which the user has opened.
// If an empty string is returned the user is not redirected.
if (!function_exists('_imp_hook_mbox_redirect')) {
    function _imp_hook_mbox_redirect($mailbox)
    {
        require_once 'Horde/Kolab.php';

        if (strpos($mailbox, "INBOX/Calendar") !== false
            || preg_match("!^user/[^/]+/Calendar!", $mailbox))
        {
            return $GLOBALS['registry']->getParam('webroot', 'kronolith');
        } elseif (strpos($mailbox, "INBOX/Tasks") !== false
            || preg_match("!^user/[^/]+/Tasks!", $mailbox))
        {
            return $GLOBALS['registry']->getParam('webroot', 'nag');
        } elseif (strpos($mailbox, "INBOX/Notes") !== false
            || preg_match("!^user/[^/]+/Notes!", $mailbox))
        {
            return $GLOBALS['registry']->getParam('webroot', 'mnemo');
        } elseif (strpos($mailbox, "INBOX/Contacts") !== false
            || preg_match("!^user/[^/]+/Contacts!", $mailbox))
        {
            return $GLOBALS['registry']->getParam('webroot', 'turba');
        }

        return '';
    }
}

// This is an example hook function for the IMP mailbox icon scheme. This
// function is called when the folder list is created and a "standard" folder
// is to be displayed - it allows custom folder icons to be specified.
// ("Standard" means all folders except the INBOX, sent-mail folders and
// trash folders.)
// If a mailbox name doesn't appear in the below list, the default mailbox
// icon is displayed.
if (!function_exists('_imp_hook_mbox_icons')) {
    function _imp_hook_mbox_icons()
    {
        require_once 'Horde/Kolab.php';

        $kc = new Kolab_Cyrus($GLOBALS['conf']['kolab']['server']);
        $mailboxes = $kc->listMailBoxes();
        $newmailboxes = array();

        foreach ($mailboxes as $box) {
            $box = preg_replace("/^{[^}]+}/", "", $box);
            if (strpos($box, "INBOX/Calendar") !== false
                || preg_match("!^user/[^/]+/Calendar!", $box))
            {
                $newmailboxes[$box] = Horde::img(
                    $GLOBALS['registry']->getParam('icon', 'kronolith'),
                    _("Calendar"),
                    'border="0" width="16" height="16" style="vertical-align:middle"',
                    ''
                );
            } elseif (strpos($box, "INBOX/Tasks") !== false
                || preg_match("!^user/[^/]+/Tasks!", $box))
            {
                $newmailboxes[$box] = Horde::img(
                    $GLOBALS['registry']->getParam('icon', 'nag'),
                    _("Tasks"),
                    'border="0" width="16" height="16" style="vertical-align:middle"',
                    ''
                );
            } elseif (strpos($box, "INBOX/Notes") !== false
                || preg_match("!^user/[^/]+/Notes!", $box))
            {
                $newmailboxes[$box] = Horde::img(
                    $GLOBALS['registry']->getParam('icon', 'mnemo'),
                    _("Notes"),
                    'border="0" width="16" height="16" style="vertical-align:middle"',
                    ''
                );
            } elseif (strpos($box, "INBOX/Contacts") !== false
                || preg_match("!^user/[^/]+/Contacts!", $box))
            {
                $newmailboxes[$box] = Horde::img(
                    $GLOBALS['registry']->getParam('icon', 'turba'),
                    _("Contacts"),
                    'border="0" width="16" height="16" style="vertical-align:middle"',
                    ''
                );
            }
        }

        return $newmailboxes;
    }
}

// Here an example _sam_hook_username function to set the username that
// SpamAssassin sees to one different from the Horde username.
if (!function_exists('_sam_hook_username')) {
    function _sam_hook_username($horde_uid)
    {
        if (strstr($horde_uid, '@')) {
            $parts = explode('@', $horde_uid);
            return $parts[0];
        } else {
            return $horde_uid;
        }
    }
}

// Here is an example _turba_hook_encode_password (and decode). encode is called
// when we store a value; decode when we display it.
// Passwords should be MD5 encoded, but not displayed.
if (!function_exists('_turba_hook_encode_password')) {
    function _turba_hook_encode_password($new_password, $old_password)
    {
        if (is_null($new_password) || $new_password == '' ||
            $new_password == '[Not Displayed]') {
            return $old_password;
        } else {
            return md5($new_password);
        }
    }
    function _turba_hook_decode_password($password)
    {
        if (strstr($_SERVER['PHP_SELF'], 'editobject')) {
            return null;
        } else {
            return '[Not Displayed]';
        }
    }
}

// Here is an example _passwd_hook_username function to translate what the user
// enters, in the username box, into what the backend expects. If we want to add
// @example.com to the end of the username then enable the hook and use this
// funciton.
if (!function_exists('_passwd_hook_username')) {
    function _passwd_hook_username($userid)
    {
        return $userid . '@example.com';
    }
}

// Here is an example _passwd_hook_default_username function to set the username
// the passwd module sees when resetting passwords based on userid and realm.
// The default is to take a username of user@domain.tld and change it to user.
// If we want to leave it untouched, enable the hook and use this function.
if (!function_exists('_passwd_hook_default_username')) {
    function _passwd_hook_default_username($userid)
    {
        return $userid;
    }
}

// Here is an example _passwd_hook_userdn function that you can use to provide
// your ldap server with a userdn so that you do not have to perform anonymous
// binds. The function takes Auth::getAuth() as a parameter
if (!function_exists('_passwd_hook_userdn')) {
    function _passwd_hook_userdn($auth)
    {
        return 'uid=' . $auth . ',o=example.com';
    }
}

// This is an example of a hook to set custom tags to be included in a Giapeto
// page template. In this example a tag containing the current date is set to
// the $template object and which is then available in the page template as:
//     <tag:date />
if (!function_exists('_giapeto_hook_settags')) {
    function _giapeto_hook_settags(&$template)
    {
        $template->set('date', strftime('%a, %e %b %Y'));
    }
}

// This is an example of a group hook.  To use it you must set the group
// driver to hooks in conf.php.  Then you must create a IT_department
// group (because that is how we know what hook to call).  You can add
// users to the group as normal, and in addition this function will be
// called to dynamically include users in the group.  In this example we
// will look up whether or not this user is part of the IT department
// using an external database.
if (!function_exists('_group_hook_IT_department')) {
    function _group_hook_IT_department($userName)
    {
        global $conf;

        $dept = 'IT';
        include_once 'DB.php';
        $_db = &DB::connect($conf['sql'], true);
        $query = sprintf('SELECT COUNT(*) FROM departments WHERE user_name=%s AND department=%s',
                $_db->quote($userName), $_db->quote($dept));
        $result = $_db->getOne($query);
        if (!is_a($result, 'PEAR_Error') && $result > 0) {
            return true;
        } else {
            return false;
        }
    }
}
