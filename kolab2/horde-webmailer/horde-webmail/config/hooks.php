<?php
/**
 * Horde Hooks configuration file.
 *
 * THE HOOKS PROVIDED IN THIS FILE ARE EXAMPLES ONLY.  DO NOT ENABLE THEM
 * BLINDLY IF YOU DO NOT KNOW WHAT YOU ARE DOING.  YOU HAVE TO CUSTOMIZE THEM
 * TO MATCH YOUR SPECIFIC NEEDS AND SYSTEM ENVIRONMENT.
 *
 * This file is where you define any hooks, for preferences or general Horde
 * use, that your installation uses. The functions in this file can vastly
 * change how your installation behaves, so make sure to test out any changes
 * here before doing them in a production environment.
 *
 * Hook function names are automatically determined. The format of the name
 * is:
 *
 * _<type of hook>_hook_<name of hook>.
 *
 * Types of hooks that are defined in this file are 'prefs' (hooks to set the
 * value of preferences), 'horde' (hooks for the Horde Framework scripts) and
 * 'app' (where app is any Horde application name, like 'imp') hooks that are
 * application specific.
 *
 * So, a hook to set the preference 'theme' would be named
 * "_prefs_hook_theme".
 *
 * NOTE 1: Having a hook function in this file does NOT mean that the hook
 * will automatically be used. YOU MUST enable the hook. For preferences, set
 * 'hook' => true in that preferences attributes; for other hooks, there will
 * be a configuration option in each application's conf.php file such as
 * $conf['hooks']['hookname'] which must be set to true.
 *
 * NOTE 2: Preferences hooks are ONLY executed on login. Preferences are
 * cached during a users session and, to avoid unnecessary overhead every time
 * a preference is accessed, the results of hooks are cached as well. This
 * leads to ...
 *
 * NOTE 3: Any preference that is NOT LOCKED, that is set by a hook, WILL BE
 * SAVED WITH THAT VALUE. This means several things:
 * 1) Users will get the results of the hook set for them in their
 *    preferences.
 * 2) By virtue of this, the next time they log in and load their
 *    preferences, the hook will NOT be called, because in their last session,
 *    we saved the results of the hook for them. However, if the preference is
 *    locked, the result of the hook will never be saved.
 *
 * $Horde: horde/config/hooks.php.dist,v 1.73.6.19 2009-08-13 15:43:56 jan Exp $
 */

// Example theme hook function. This shows how you can access things like the
// currently logged in user, global variables, server config, etc. It isn't,
// however, something you probably want to actually use in production, by
// virtue of demonstrating all those. :)

// if (!function_exists('_prefs_hook_theme')) {
//     function _prefs_hook_theme($username = null)
//     {
//         if (Auth::getAuth() != 'chuck') {
//             return 'mozilla';
//         }
//
//         global $registry;
//         switch ($registry->getApp()) {
//         case 'imp':
//             return 'brown';
//
//         case 'turba':
//             return 'orange';
//
//         case 'kronolith':
//             return 'green';
//
//         default:
//             return '';
//         }
//     }
// }

// Example preferences change hook. Preferences change hooks are named
// _prefs_change_hook_<prefname>, and are called with no arguments
// when a preference is changed to a new value (re-setting it to the
// same value will not trigger a call).

// if (!function_exists('_prefs_change_hook_theme')) {
//     function _prefs_change_hook_theme()
//     {
//         $GLOBALS['notification']->push('You changed your theme to ' . $GLOBALS['prefs']->getValue('theme') . '!');
//     }
// }

// Example from_addr hook function. THIS FUNCTION ASSUMES THAT YOU ARE USING
// AN LDAP SERVER and that your /etc/ldap.conf or wherever it is correctly set
// to a valid host.
//
// You get passed NOTHING; you are responsible for bringing in to scope any
// information you need. You can "global" anything else you need. Return an
// address - either just the user@ side or a full address - and it will be
// used.
//
// If you want to use this code you will need to uncomment it below.

// if (!function_exists('_prefs_hook_from_addr')) {
//     function _prefs_hook_from_addr($name = null)
//     {
//         if (is_null($name)) {
//             $name = Auth::getAuth();
//         }
//         if (!empty($name)) {
//             $base_context = 'o=myorg';
//             $scope = 'sub';
//
//             // You will probably need to replace cd= with uid=; this
//             // syntax is for Netware 5.1 nldap.
//             $cmd  = '/usr/bin/ldapsearch -b ' . $base_context . ' -s ' . $scope . ' cn=';
//             $cmd .= escapeShellCmd(Auth::getAuth());
//             $cmd .= ' | /usr/bin/grep mail | /usr/bin/awk \'{print $2}\'';
//             $mails = `$cmd`;
//             $mail_array = explode("\n", $mails);
//
//             // Send back the first email found, not the whole list.
//             $mail = $mail_array['0'];
//
//             // If no email address is found, then the login name will
//             // be used.
//             return (empty($mail) ? '' : $mail);
//         }
//
//         return '';
//     }
// }

// Here is another way of doing the same thing.

// if (!function_exists('_prefs_hook_from_addr')) {
//     function _prefs_hook_from_addr($user = null)
//     {
//         $ldapServer = '172.31.0.236';
//         $ldapPort = '389';
//         $searchBase = 'o=myorg';
//
//         $ds = @ldap_connect($ldapServer, $ldapPort);
//
//         if (is_null($user)) {
//             $user = Auth::getAuth();
//             if ($user === false) {
//                 return '';
//             }
//         }
//
//         // You will probably need to replace cn= with uid=; this
//         // syntax is for Netware 5.1 nldap.
//         $searchResult = @ldap_search($ds, $searchBase, 'cn=' . $user);
//         $information = @ldap_get_entries($ds, $searchResult);
//         if ($information === false || $information['count'] == 0) {
//             $name = '';
//         } else {
//             if ($information[0]['mail'][0] != '') {
//                 $name = $information[0]['mail'][0];
//             } else {
//                 $name = $information[0]['cn'][0];
//             }
//         }
//
//         ldap_close($ds);
//
//         return (empty($name) ? $user : $name);
//     }
// }

// Here is an example fullname hook function to set the fullname from the GECOS
// information in the passwd file.

// if (!function_exists('_prefs_hook_fullname')) {
//     function _prefs_hook_fullname($user = null)
//     {
//         if (is_null($user)) {
//             $user = Auth::getBareAuth();
//             if ($user === false) {
//                 return '';
//             }
//         }
//         $array = posix_getpwnam($user);
//         $gecos_array = explode(',', $array['gecos']);
//         return (empty($gecos_array) ? $user : $gecos_array[0]);
//     }
// }

// This is another example of how to get the user's full name, in this case
// from an ldap server. In this example we look if a Spanish name exists and
// return this or the standard 'cn' entry if not.

// if (!function_exists('_prefs_hook_fullname')) {
//     function _prefs_hook_fullname($user = null)
//     {
//         $ldapServer = 'ldap.example.com';
//         $ldapPort = '389';
//         $searchBase = 'ou=people,o=example.com';
//         $ldapcharset = 'utf-8';
//         $outputcharset = NLS::getCharset();
//
//         $ds = @ldap_connect($ldapServer, $ldapPort);
//
//         if (is_null($user)) {
//             $user = Auth::getAuth();
//             if ($user === false) {
//                 return '';
//             }
//         }
//         $searchResult = @ldap_search($ds, $searchBase, 'uid=' . $user);
//         $information = @ldap_get_entries($ds, $searchResult);
//         if ($information === false || $information['count'] == 0) {
//             $name = '';
//         } else {
//             if ($information[0]['cn;lang-es'][0] != '') {
//                 $name = $information[0]['cn;lang-es'][0];
//             } else {
//                 $name = $information[0]['cn'][0];
//             }
//         }
//
//         ldap_close($ds);
//
//         $name = String::convertCharset($name, $ldapcharset, $outputcharset);
//         return (empty($name) ? $user : $name);
//     }
// }

// IE on Mac hangs when there are several icons to be loaded. At least on some
// systems. This hook disables the show_icons preference from Krononlith for
// these browsers.

// if (!function_exists('_prefs_hook_show_icons')) {
//     function _prefs_hook_show_icons()
//     {
//         global $browser;
//         if ($browser->getPlatform() == 'mac' &&
//             $browser->getBrowser() == 'msie') {
//             return false;
//         } else {
//             return true;
//         }
//     }
// }

// This hook is called when a user submits a signup request.  It allows
// a chance to alter or validate the data submitted by a user before any
// attempts are made to add them to the system.

// if (!function_exists('_horde_hook_signup_preprocess')) {
//     function _horde_hook_signup_preprocess($info) {
//         $info['user_name'] = String::lower($info['user_name']);
//         return $info;
//     }
// }

// This hook is called when a signup is queued for administrative approval.
// This example sends a notification message to the web server
// administrator's e-mail address.

// if (!function_exists('_horde_hook_signup_queued')) {
//     function _horde_hook_signup_queued_walkdata($fields, $data)
//     {
//         $msg = '';
//         foreach ($data as $field => $value) {
//             if ($field == 'password' || $field == 'url') {
//                 continue;
//             }
//
//             if (is_array($value)) {
//                 $msg .= _horde_hook_signup_queued_walkdata($fields, $value);
//             } else {
//                 $field = isset($fields[$field]['label']) ?
//                          $fields[$field]['label'] : $field;
//                 $msg .= "$field: $value\n";
//             }
//         }
//         return $msg;
//     }
//
//     function _horde_hook_signup_queued($userID, $data)
//     {
//         require_once 'Mail.php';
//         global $conf, $registry;
//
//         $headers = array(
//             'To'      => $_SERVER['SERVER_ADMIN'],
//             'From'    => $_SERVER['SERVER_ADMIN'],
//             'Subject' => 'New ' . $registry->get('name', 'horde') . ' Signup'
//         );
//
//         $extraFields = Horde::callHook('_horde_hook_signup_getextra');
//
//         $msg  = _("A new signup has been received and is awaiting your approval.");
//         $msg .= "\n\n";
//         $msg .= _horde_hook_signup_queued_walkdata($extraFields, $data);
//         $msg .= "\n";
//         $msg .= sprintf(_("You can approve this signup at %s"), Horde::applicationUrl('admin/user.php', true, -1));
//
//         $mailer = Mail::factory($conf['mailer']['type'], $conf['mailer']['params']);
//         return $mailer->send($_SERVER['SERVER_ADMIN'], $headers, $msg);
//     }
// }

// Here is an example _horde_hook_signup_getextra function. It returns any
// extra fields which need to be filled in when a non registered user wishes
// to sign up.
// The example here takes the hypothetical case where we would want to store
// extra information about a user into a turba sql address book. All this
// function does then is to include the attributes.php file from the turba
// config directory and return the $attributes array.
// Otherwise any structure that would return an array with the following
// syntax would be valid:
//   $somearray['somefieldname'] = array(...
//      label    - the text that the user will see attached to this field
//      type     - any allowed Horde_Form field type
//      params   - any allowed parameter to Horde_Form field types
//      required - boolean, true or false whether this field is mandatory
//      readonly - boolean, true or false whether this editable
//      desc     - any help text attached to the field
// NOTE: You DO NEED Turba to be correctly installed before you can use this
// example below.

// if (!function_exists('_horde_hook_signup_getextra')) {
//     function _horde_hook_signup_getextra()
//     {
//         global $registry;
//         require $registry->get('fileroot', 'turba') . '/config/attributes.php';
//         return $attributes;
//     }
// }

// Following on from the example in the above function, this is how a sample
// _horde_hook_signup_addextra function would look like.
// Here we connect to the database using the sql parameters configured in
// $conf and store the extra fields in turba_objects, using the $userId as the
// key for the object and values from the $extra array.
// You could create your own sql syntax or code to store this in whichever
// backend you require.
// NOTE: You DO NEED Turba to be correctly installed before you can use this
// example below. It also assumes that you are using an SQL backend.

// if (!function_exists('_horde_hook_signup_addextra')) {
//     function _horde_hook_signup_addextra($userID, $extra, $password)
//     {
//         global $conf;
//
//         require_once 'DB.php';
//         $_db = &DB::connect($conf['sql'], true);
//
//         $fields = array();
//         $values = array();
//         foreach ($extra as $field => $value) {
//             $fields[] = 'object_' . String::lower($field);
//             $values[] = $_db->quote(String::convertCharset($value, NLS::getCharset(), $conf['sql']['charset']));
//         }
//         $fields[] = 'object_id';
//         $values[] = $_db->quote($userID);
//
//         $query  = 'INSERT INTO turba_objects ( owner_id, ' . implode(', ', $fields) . ')';
//         $query .= ' VALUES ( \'admin\', ' . implode(', ', $values) . ')';
//         $result = $_db->query($query);
//
//         return is_a($result, 'PEAR_Error') ? $result : true;
//     }
// }

// Here is an example _horde_hook_preauthenticate that make Horde respect the
// Unix convention of not allowing login when a file named /etc/nologin exist.
// This function get passed the username, credential and realm information but
// they are not used in this example.

// if (!function_exists('_horde_hook_preauthenticate')) {
//     function _horde_hook_preauthenticate($userID, $credential, $realm)
//     {
//         return !file_exists('/etc/nologin');
//     }
// }

// Here is an example of validating the user's right to login to Horde by
// consulting group membership in an LDAP directory.  That way, if your Horde
// installation is configured to authenticate against IMP which in turn
// authenticate via IMAP, it is still possible to limit access to Horde by
// group membership.  The following example had been made with an MS Active
// Directory in mind.  Note that if the LDAP directory is unavailable or some
// other error occur, authentication will fail.

// if (!function_exists('_horde_hook_postauthenticate')) {
//     function _horde_hook_postauthenticate($userID, $credential, $realm)
//     {
//         $ldapServer = 'ad.example.com';
//         $ldapPort = '389';
//         // Note that credential is sent plain-text in this case, so don't use
//         // privileged account here or setup SSL (by using port 636 above).
//         $binddn = 'cn=WithoutPrivilege,dc=ulaval-dev,dc=ca';
//         $bindpw = 'Remember this is sent in the clear unless SSL is used';
//         $searchBase = 'ou=People,dc=example,dc=com';
//         // Attribute to match $userID against in search
//         $userAttr = 'sAMAccountName';
//         // Group membership attribute, need to be all lowercase
//         $groupAttr = 'memberof';
//         // Attribute to check for right to use Horde
//         $groupdn = 'cn=HordeUser,ou=People,dc=example,dc=com';
//         $ret = true;
//
//         $ds = @ldap_connect($ldapServer, $ldapPort);
//
//         if (@ldap_bind($ds, $binddn, $bindpw)) {
//             $searchResult = @ldap_search($ds, $searchBase, $userAttr . '=' . $userID, array($groupAttr), 0, 1, 5);
//             if ($information = @ldap_get_entries($ds, $searchResult)) {
//                 // make pattern case-insensitive
//                 $pattern = '/' . $groupdn . '/i';
//                 foreach ($information[0][$groupAttr] as $group) {
//                     if (preg_match($pattern, $group)) {
//                         $ret = true;
//                         break;
//                     }
//                 }
//             }
//         }
//
//         ldap_close($ds);
//         return $ret;
//     }
// }

// Here is an example of creating credentials needed by the LDAP Auth driver
// for adding/deleting/updating users.

// if (!function_exists('_horde_hook_authldap')) {
//     function _horde_hook_authldap($userID, $credentials = null)
//     {
//         $entry['dn'] = 'uid=' . $userID . ',ou=People,dc=example.com';
//         if (isset($credentials) && isset($credentials['user_fullname'])) {
//             $entry['cn'] = $credentials['user_fullname'];
//         } else {
//             $entry['cn'] = $userID;
//         }
//         $entry['sn'] = $userID;
//         $entry['objectclass'][0] = 'top';
//         $entry['objectclass'][1] = 'person';
//         $entry['objectclass'][2] = 'qmailuser';
//         $entry['objectclass'][3] = 'CourierMailACcount';
//         $entry['mailhost'] = 'mail.example.com';
//         $entry['mailMessageStore'] = '/home/mail/' . $userID;
//         $entry['homeDirectory'] = '/home/mail/' . $userID;
//         $entry['mailbox'] = $entry['homeDirectory'] . '/Maildir';
//         $entry['uid'] = $userID;
//         $entry['accountStatus'] = 'active';
//         $entry['mailQuota'] = '104857600S';
//         $entry['mail'] = $userID;
//         $entry['uidNumber'] = 501;
//         $entry['gidNumber'] = 501;
//
//         // need to check for new users (password) and edited users (user_pass_2)
//         if (isset($credentials) && isset($credentials['password'])) {
//             $entry['userPassword'] =  '{MD5}' . base64_encode(pack('H*', md5($credentials['password'])));
//         } elseif (isset($credentials) && isset($credentials['user_pass_2'])) {
//             $entry['userPassword'] =  '{MD5}' . base64_encode(pack('H*', md5($credentials['user_pass_2'])));
//         }
//         $entry['deliveryMode'] = 'nolocal';
//         return $entry;
//     }
// }

// This example is of a function that can be called when a share listing is
// requested. It takes a userid, a permissions level, an optional string
// containing a userid to restrict the owner of the shares returned, and the
// result of the corresponding Horde_Share::listShares() call as its
// parameters. As is the case in the previous three functions, if a PEAR_Error
// result is returned the Horde_Share::listShares() call that triggered this
// hook will fail with the returned result.

// if (!function_exists('_horde_hook_share_list')) {
//     function _horde_hook_share_list($userid, $perm, $owner, &$share_list)
//     {
//         global $registry;
//         //error_log('Number of ' . $GLOBALS['registry']->getApp() . ' shares' . ($owner ?
//         //    ' owned by ' . $owner : '') . ' available to ' . $userid . ' at perms level ' .
//         //    $perm . ': ' .  count($share_list));
//         return true;
//     }
// }

// Here is an example _username_hook_frombackend function. It appends the
// virtual domain to the user name.
//
// ex. $HTTP_HOST = 'mail.mydomain.com', $userID = 'myname' returns:
//   'myname@mydomain.com'

// if (!function_exists('_username_hook_frombackend')) {
//     function _username_hook_frombackend($userID)
//     {
//         $vdomain = getenv('HTTP_HOST');
//         $vdomain = preg_replace('|^mail\.|i', '', $vdomain);
//         $vdomain = String::lower($vdomain);
//
//         return $userID . '@' . $vdomain;
//     }
// }

// Here is an example _username_hook_tobackend function as a counterpart of the
// previous example. It strips the virtual domain from the user name.
//
// ex. $HTTP_HOST = 'mail.mydomain.com', $userID = 'myname' returns:
//   'myname@mydomain.com'

// if (!function_exists('_username_hook_tobackend')) {
//     function _username_hook_tobackend($userID)
//     {
//         $vdomain = getenv('HTTP_HOST');
//         $vdomain = preg_replace('|^mail\.|i', '', $vdomain);
//         $vdomain = '@' . String::lower($vdomain);
//
//         if (substr($userID, -strlen($vdomain)) == $vdomain) {
//             $userID = substr($userID, 0, -strlen($vdomain));
//         }
//
//         return $userID;
//     }
// }

// Here is an example _username_hook_frombackend function. It converts the user
// name to all lower case. This might be necessary if an authentication backend
// is case insensitive to take into account that Horde's preference system is
// case sensitive.
//
// ex. $userID = 'MyName' returns: 'myname'

// if (!function_exists('_username_hook_frombackend')) {
//     function _username_hook_frombackend($userID)
//     {
//         return String::lower($userID);
//     }
// }

// Here is an example _perms_hook_denied function.  It is called if a user
// tries to make an action that is under permission control and that he
// doesn't have sufficient permissions for.  It can be used to show the user a
// custom message including HTML code (you have to take care about HTML
// escaping on your own), or to interrupt the code flow and send the user to a
// different page for example.

// if (!function_exists('_perms_hook_denied')) {
//     function _perms_hook_denied($permission)
//     {
//         if (($pos = strpos($permission, ':')) === false) {
//             $app = $permission;
//         } else {
//             $app = substr($permission, 0, $pos);
//         }
//
//         return sprintf('Permission denied. Click <a href="http://www.example.com/upgrade.php?app=%s">HERE</a> to upgrade %s.',
//                        $app, $GLOBALS['registry']->get('name'));
//     }
// }

// This is an example of a group hook.  To use it you must set the group
// driver to hooks in conf.php.  You can add users to groups as normal, and
// in addition this function will be called to dynamically include users in
// the group.  Note the group hook interface changed as of Horde 3.2.
// In this example we will look up whether or not this user is part of the
// "IT_department" group using an external database.

// if (!function_exists('_group_hook')) {
//     function _group_hook($groupName, $userName)
//     {
//         global $conf;
//
//         switch ($groupName) {
//         case 'IT_department':
//             $dept = 'IT';
//             include_once 'DB.php';
//             $_db = &DB::connect($conf['sql'], true);
//             $query = 'SELECT COUNT(*) FROM departments WHERE user_name = ? AND department = ?';
//             $values = array($userName, $dept);
//             $result = $_db->getOne($query, $values);
//             return (!is_a($result, 'PEAR_Error') && $result > 0);
//
//         default:
//             return false;
//         }
//     }
// }

// You can keep your existing Horde <= 3.1 group hook functions and use
// this group hook function to link them to the Horde 3.2 interface.

// if (!function_exists('_group_hook')) {
//     function _group_hook($groupName, $userName)
//     {
//         if (function_exists('_group_hook_' . str_replace(':', '__', $groupName))) {
//             return call_user_func('_group_hook_' . str_replace(':', '__', $groupName));
//         }
//     }
// }

// This is an example of a post-push hook; it is called right after an
// application is pushed successfully onto the app stack.

// if (!function_exists('_horde_hook_post_pushapp')) {
//     function _horde_hook_post_pushapp($app)
//     {
//         if ($app == 'imp') {
//             // Run some code if the app is switched to imp
//         }
//     }
// }

// IMSP share hooks.  These require at least Turba 2.2 and Horde 3.2
/*if (!empty($GLOBALS['conf']['imsp']['enabled'])) {
    require_once 'Net/IMSP/Utils.php';
    if (!function_exists('_horde_hook_share_init')) {
        function _horde_hook_share_init(&$share_obj, $app)
        {
            // cfgSources won't be defined here before Turba 2.2
            if (($app == 'turba') && (!empty($GLOBALS['cfgSources'])) &&
                (!empty($GLOBALS['cfgSources']['imsp']['use_shares']))) {

                // Only do this once per session or when this session variable
                // is purposely unset.
                if (!empty($_SESSION['imsp_synched'])) {
                    return;
                }
                $results = Net_IMSP_Utils::synchShares($share_obj, $GLOBALS['cfgSources']['imsp']);
                if (!is_a($results, 'PEAR_Error')) {
                    $_SESSION['imsp_synched'] = true;

                    // Now deal with adding or removing address books from prefs.
                    // FIXME: Updating prefs seems to hang the server. Narrowed
                    // down to the fact that prefs->setValue() also attempts to call
                    // a hook. (Commenting out the callHook call fixes). Can
                    // anyone verify this on their install?
                    $dirty = false;
                    $abooks = $GLOBALS['prefs']->getValue('addressbooks');
                    if (!empty($abooks)) {
                        $abooks = explode("\n", $GLOBALS['prefs']->getValue('addressbooks'));
                    } else {
                        $abooks = array();
                    }

                    if (count($results['removed'] > 0)) {
                        foreach ($results['removed'] as $sharename) {
                           $key = array_search($sharename, $abooks);
                           if ($key === true) {
                               unset($abooks[$key]);
                               $dirty = true;
                           }
                        }
                    }
                    if (count($results['added']) > 0) {
                        foreach ($results['added'] as $sharename) {
                            if (array_search($sharename, $abooks) === false) {
                                $abooks[] = $sharename;
                                $dirty = true;
                            }
                        }
                    }
                    if ($dirty) {
                        $result = $GLOBALS['prefs']->setValue('addressbooks', implode("\n", $abooks));
                    }

                    // We have to save the connection info for the imsp server since
                    // the share_modify hook will not occur from within turba's context.
                    $_SESSION['imsp_config'] = $GLOBALS['cfgSources']['imsp']['params'];
                }
            }
        }

        function _horde_hook_share_modify(&$share)
        {
            $params = unserialize($share->get('params'));
            if (is_array($params) && !empty($params['source']) &&
                $params['source'] = 'imsp' &&
                !empty($_SESSION['imsp_config'])) {

                // Ensure we don't try to change ownership.
                $params = @unserialize($share->get('params'));
                $bookName = $params['name'];
                if (strpos($bookName, $share->get('owner')) !== 0) {
                    $err = &PEAR::raiseError('Changing ownership of IMSP address books is not supported.');
                    $GLOBALS['notification']->push($err);
                    return $err;
                }


                //Update the ACLS
                $perms = $share->getPermission();
                $users = $perms->getUserPermissions();
                foreach ($users as $user => $perm) {
                    $acl = Net_IMSP_Utils::permsToACL($perm);
                    $result = Net_IMSP_Utils::setACL($_SESSION['imsp_config'],
                                           $bookName,
                                           $user, $acl);

                }
            }
        }
    }
}*/
