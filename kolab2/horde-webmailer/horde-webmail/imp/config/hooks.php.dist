<?php
/**
 * IMP Hooks configuration file.
 *
 * THE HOOKS PROVIDED IN THIS FILE ARE EXAMPLES ONLY.  DO NOT ENABLE THEM
 * BLINDLY IF YOU DO NOT KNOW WHAT YOU ARE DOING.  YOU HAVE TO CUSTOMIZE THEM
 * TO MATCH YOUR SPECIFIC NEEDS AND SYSTEM ENVIRONMENT.
 *
 * For more information please see the horde/config/hooks.php.dist file.
 *
 * $Horde: imp/config/hooks.php.dist,v 1.3.2.13 2009-11-18 13:14:32 jan Exp $
 */

// Here is an example signature hook function to set the signature from the
// system taglines file; the string "%TAG%" (if present in a user's signature)
// will be replaced by the content of the file "/usr/share/tagline" (generated
// by the "TaRT" utility).
//
// Notice how we global in the $prefs array to get the user's current
// signature.

// if (!function_exists('_prefs_hook_signature')) {
//     function _prefs_hook_signature($username = null)
//     {
//         $sig = $GLOBALS['prefs']->getValue('signature');
//         if (preg_match('/%TAG%/', $sig)) {
//             $tag = `cat /usr/share/tagline`;
//             $sig = preg_replace('|%TAG%|', $tag, $sig);
//         }
//         return $sig;
//     }
// }

// Example hook to set the value of the add_source pref. Useful when using
// a turba source with shares enabled (i.e. the example localsql configuration)
// This requires Horde >= 3.3.5 to work correctly.

// if (!function_exists('_prefs_hook_add_source')) {
//     function _prefs_hook_add_source($username = null)
//     {
//         if (!$username) {
//             return;
//         }
//
//         /** If you have Turba >= 2.3.2 you can simply do this: **/
//         // return $GLOBALS['registry']->call('contacts/getDefaultShare');
//
//         /** Otherwise, need to be a bit more hackish **/
//         $shares = &Horde_Share::singleton('turba');
//         $sources = $shares->listShares(
//             Auth::getAuth(), PERMS_EDIT, Auth::getAuth());
//         foreach ($sources as $uid => $share) {
//             $params = @unserialize($share->get('params'));
//             if ($params['default']) {
//                 return $uid;
//             }
//         }
//     }
// }

// Example hook to set the value of the search_sources pref. Useful when using
// a turba source with shares enabled (i.e. the example localsql
// configuration)

// if (!function_exists('_prefs_hook_search_sources')) {
//     function _prefs_hook_search_sources($username = null)
//     {
//         if (!$username) {
//             return;
//         }
//
//         if ($GLOBALS['registry']->hasMethod('contacts/sources')) {
//            $sources = $GLOBALS['registry']->call('contacts/sources');
//            return implode("\t", array_keys($sources));
//         }
//     }
// }

// Here is an example _imp_hook_postlogin function to redirect to a
// custom server after login.

// if (!function_exists('_imp_hook_postlogin')) {
//     function _imp_hook_postlogin($actionID, $isLogin)
//     {
//         header('Location: http://mail' . mt_rand(1, 9) . '.example.com/horde/');
//         exit;
//     }
// }

// This is an example for a post-sending hook that automatically prints all
// messages that have been sent successfully.

// if (!function_exists('_imp_hook_postsent')) {
//     function _imp_hook_postsent($message, $headers)
//     {
//         require_once IMP_BASE . '/lib/MIME/Contents.php';
//         require_once IMP_BASE . '/lib/UI/Message.php';
//
//         IMP::printMode(true);
//         $contents = new IMP_Contents($message);
//         $contents->showSummaryLinks(false);
//         $contents->buildMessage();
//         $attachments = $contents->getAttachments();
//         $msgText = $contents->getMessage();
//
//         $imp_ui = new IMP_UI_Message();
//         $basic_headers = $imp_ui->basicHeaders();
//         $headers->setValueByFunction('date', array('nl2br', array($headers, 'addLocalTime'), 'htmlspecialchars'));
//         if (($subject = $headers->getValue('subject'))) {
//             $subject = IMP::filterText($subject);
//             require_once 'Horde/Text.php';
//             $headers->setValue('subject', Text::htmlSpaces($subject));
//         } else {
//             $headers->addHeader('Subject', _("[No Subject]"));
//         }
//         $headers->buildAddressLinks('from', null, true, false);
//         foreach (array('to', 'cc', 'bcc') as $val) {
//             $headers->buildAddressLinks($val, null, true, false);
//         }
//         if ($reply_to = $headers->buildAddressLinks('reply-to', null, false, false)) {
//             if (!($from = $headers->getValue('from')) || ($from != $reply_to)) {
//                 $headers->setValue('Reply-to', $reply_to);
//             } else {
//                 $headers->removeHeader('reply-to');
//             }
//         }
//         $hdrs = array();
//         foreach ($basic_headers as $head => $str) {
//             if ($val = $headers->getValue($head)) {
//                 $hdrs[] = array('name' => $str, 'val' => $val, 'i' => 0);
//             }
//         }
//         if ($val = $headers->getValue('priority')) {
//             $hdrs[] = array('name' => _("Priority"), 'val' => $val, 'i' => 0);
//         }
//         if (!empty($attachments)) {
//             $hdrs[] = array('name' => _("Part(s)"), 'val' => '<table cellspacing="2">' . $attachments . '</table>', 'i' => 0);
//         }
//
//         require_once IMP_BASE . '/lib/Template.php';
//         $template = new IMP_Template();
//         $template->set('headers', $hdrs);
//         $template->set('msgtext', $msgText);
//         $printer_friendly = true;
//         require IMP_TEMPLATES . '/common-header.inc';
//         echo $template->fetch(IMP_TEMPLATES . '/message/message.html');
//         require $GLOBALS['registry']->get('templates', 'horde') . '/javascript/print.js';
//         require $GLOBALS['registry']->get('templates', 'horde') . '/common-footer.inc';
//         exit;
//     }
// }

// Here is an example _imp_hook_trailer function to set the trailer from the
// system taglines file; the string "@@TAG@@" (if present in a trailer) will be
// replaced by the content of the file "/usr/share/tagline" (generated by the
// "TaRT" utility).

// if (!function_exists('_imp_hook_trailer')) {
//     function _imp_hook_trailer($trailer)
//     {
//         if (preg_match('/@@TAG@@/', $trailer)) {
//             $tag = `cat /usr/share/tagline`;
//             $trailer = preg_replace('|@@TAG@@|', $tag, $trailer);
//         }
//         return $trailer;
//     }
// }

// Here is an another example _imp_hook_trailer function to set the trailer
// from the LDAP directory for each domain. This function replaces the current
// trailer with the data it gets from ispmanDomainSignature.

// if (!function_exists('_imp_hook_trailer')) {
//     function _imp_hook_trailer($trailer)
//     {
//         $vdomain = getenv('HTTP_HOST');
//         $vdomain = preg_replace('|^.*?\.|i', '', $vdomain);
//         $vdomain = String::lower($vdomain);
//         $ldapServer = 'localhost';
//         $ldapPort = '389';
//         $searchBase = 'ispmanDomain=' . $vdomain  . ",o=ispman";
//
//         $ds = @ldap_connect($ldapServer, $ldapPort);
//         $searchResult = @ldap_search($ds, $searchBase, 'uid=' . $vdomain);
//         $information = @ldap_get_entries($ds, $searchResult);
//         $trailer= $information[0]['ispmandomainsignature'][0];
//         ldap_close($ds);
//
//         return $trailer;
//     }
// }

// Here is an example _imp_hook_vinfo function. If $type == 'vdomain', this
// function returns the HTTP_HOST variable after removing the 'mail.'
// subdomain.
//
// If $type == 'username', this function returns a unique username composed of
// $_SESSION['imp']['user'] + vdomain.
//
// ex. $HTTP_HOST = 'mail.mydomain.com', $_SESSION['imp']['user'] = 'myname':
//   $vdomain  = 'mydomain.com'
//   $username = 'myname_mydomain_com'

// if (!function_exists('_imp_hook_vinfo')) {
//     function _imp_hook_vinfo($type = 'username')
//     {
//         $vdomain = getenv('HTTP_HOST');
//         $vdomain = preg_replace('|^mail\.|i', '', $vdomain);
//         $vdomain = String::lower($vdomain);
//
//         if ($type == 'username') {
//             return preg_replace('|\.|', '_', $_SESSION['imp']['user'] . '_' . $vdomain);
//         } elseif ($type == 'vdomain') {
//             return $vdomain;
//         } else {
//             return PEAR::raiseError('invalid type: ' . $type);
//         }
//     }
// }

// Here is an example of the _imp_hook_fetchmail_filter function to run
// SpamAssassin on email before it is written to the mailbox.
// Note: to use the spamassassin instead of spamd, change 'spamc' to
// 'spamassassin -P' and add any other important arguments, but realize spamc
// is MUCH faster than spamassassin.
// WARNING: Make sure to use the --noadd-from filter on spamd or spamassassin

// if (!function_exists('_imp_hook_fetchmail_filter')) {
//     function _imp_hook_fetchmail_filter($message)
//     {
//         // Where does SpamAssassin live, and what username should we use
//         // for preferences?
//         $cmd = '/usr/local/bin/spamc';
//         $username = Auth::getAuth();
//         // If you use the _sam_hook_username() hook, uncomment the next line
//         //$username = _sam_hook_username($username);
//         $username = escapeshellarg($username);
//
//         // Also, we remove the file ourselves; this hook may be called
//         // hundreds of times per run depending on how many messages we fetch
//         $file = Horde::getTempFile('horde', false);
//
//         // Call SpamAssassin; pipe the new message to our tempfile
//         $fp = popen("$cmd -u $username > $file", 'w');
//         fwrite($fp, $message);
//         pclose($fp);
//
//         // Read the new message from the temporary file
//         $message = file_get_contents($file);
//         unlink($file);
//         return $message;
//     }
// }

// Here is an example signature hook function to set the signature from the
// system taglines file; the string "%TAG%" (if present in a user's signature)
// will be replaced by the content of the file "/usr/share/tagline" (generated
// by the "TaRT" utility).

// if (!function_exists('_imp_hook_signature')) {
//     function _imp_hook_signature($sig)
//     {
//         if (preg_match('/%TAG%/', $sig)) {
//             $tag = `cat /usr/share/tagline`;
//             $sig = preg_replace('/%TAG%/', $tag, $sig);
//         }
//
//         return $sig;
//     }
// }

// This is an example hook function for displaying additional message
// information in the message listing screen for a mailbox.  This example hook
// will add a icon if the message contains attachments and will change the
// display of the message entry based on the X-Priority header.

// if (!function_exists('_imp_hook_msglist_format')) {
//     function _imp_hook_msglist_format($mailbox, $uid)
//     {
//         // Required return (array):
//         //   'class' - An array of CSS classnames that will be added to
//         //             the row.
//         //   'flagbits' - An integer value which will be OR'd with the
//         //                current flags set for the row.  The IMAP flag
//         //                constants used in IMP can be found at the top
//         //                of lib/IMP.php.
//         //   'status' - HTML code to add to the status column for the row.
//         $ret = array('class' => array(), 'flagbits' => 0, 'status' => '');
//
//         require_once IMP_BASE . '/lib/IMAP/MessageCache.php';
//         $cache = &IMP_MessageCache::singleton();
//         $cache_entry = $cache->retrieve($mailbox, array($uid), 8 | 32);
//         $ob = reset($cache_entry);
//
//         // Add attachment information
//         require_once IMP_BASE . '/lib/UI/Mailbox.php';
//         $imp_ui = new IMP_UI_Mailbox();
//         if (($attachment = $imp_ui->getAttachmentType($ob->structure))) {
//             $ret['status'] = Horde::img($attachment . '.png', $imp_ui->getAttachmentAlt($attachment), array('title' => $imp_ui->getAttachmentAlt($attachment)));
//         }
//
//         // Add xpriority information
//         switch ($ob->header->getXpriority()) {
//         case 'high':
//             $ret['flagbits'] = IMP_FLAGGED;
//             $ret['status'] .= Horde::img('mail_priority_high.png', _("High Priority"), array('title' => _("High Priority")));
//             $ret['class'][] = 'important';
//             break;
//
//         case 'low':
//             $ret['status'] .= Horde::img('mail_priority_low.png', _("Low Priority"), array('title' => _("Low Priority")));
//             $ret['class'][] = 'unimportant';
//             break;
//         }
//
//         return $ret;
//     }
// }

// This is an example hook function for the IMP redirection scheme. This
// function is called when the user opens a mailbox in IMP, and allows the
// client to be redirected based on the mailbox name. The return value of this
// function should be a valid page within a horde application which will be
// placed in a "Location" header to redirect the client.  The only parameter
// is the name of the mailbox which the user has opened.  If an empty string
// is returned the user is not redirected.

// if (!function_exists('_imp_hook_mbox_redirect')) {
//     function _imp_hook_mbox_redirect($mailbox)
//     {
//         require_once 'Horde/Kolab.php';
//
//         if (strpos($mailbox, "INBOX/Calendar") !== false
//             || preg_match("!^user/[^/]+/Calendar!", $mailbox)) {
//             return $GLOBALS['registry']->get('webroot', 'kronolith');
//         } elseif (strpos($mailbox, "INBOX/Tasks") !== false
//             || preg_match("!^user/[^/]+/Tasks!", $mailbox)) {
//             return $GLOBALS['registry']->get('webroot', 'nag');
//         } elseif (strpos($mailbox, "INBOX/Notes") !== false
//             || preg_match("!^user/[^/]+/Notes!", $mailbox)) {
//             return $GLOBALS['registry']->get('webroot', 'mnemo');
//         } elseif (strpos($mailbox, "INBOX/Contacts") !== false
//             || preg_match("!^user/[^/]+/Contacts!", $mailbox)) {
//             return $GLOBALS['registry']->get('webroot', 'turba');
//         }
//
//         return '';
//     }
// }

// This is an example hook function for the IMP mailbox icon scheme. This
// function is called when the folder list is created and a "standard" folder
// is to be displayed - it allows custom folder icons to be specified.
// ("Standard" means all folders except the INBOX, sent-mail folders and
// trash folders.)
// If a mailbox name doesn't appear in the below list, the default mailbox
// icon is displayed.
// Note that in IMP 4.2.x, the expected return value from this hook has
// changed. See the below examples for more information.

// if (!function_exists('_imp_hook_mbox_icons')) {
//     function _imp_hook_mbox_icons()
//     {
//         static $newmailboxes;
//
//         if (!empty($newmailboxes)) {
//             return $newmailboxes;
//         }
//
//         require_once 'Horde/Kolab.php';
//
//         $kc = new Kolab_Cyrus($GLOBALS['conf']['kolab']['server']);
//         $mailboxes = $kc->listMailBoxes();
//         $newmailboxes = array();
//
//         foreach ($mailboxes as $box) {
//             $box = preg_replace("/^{[^}]+}/", "", $box);
//             if (strpos($box, "INBOX/Calendar") !== false
//                 || preg_match("!^user/[^/]+/Calendar!", $box)) {
//                 $newmailboxes[$box] = Horde::img(
//                     $GLOBALS['registry']->get('icon', 'kronolith'),
//                     _("Calendar"),
//                     'width="16" height="16" style="vertical-align:middle"',
//                     ''
//                 );
//                 // Use this example for IMP 4.2.x+.
//                 // $newmailboxes[$box] = array(
//                 //     'icon' => 'kronolith.png',
//                 //     'icondir' => $GLOBALS['registry']->getImageDir('kronolith')
//                 //     'alt' => _("Calendar")
//                 // );
//             } elseif (strpos($box, "INBOX/Tasks") !== false
//                 || preg_match("!^user/[^/]+/Tasks!", $box)) {
//                 $newmailboxes[$box] = Horde::img(
//                     $GLOBALS['registry']->get('icon', 'nag'),
//                     _("Tasks"),
//                     'width="16" height="16" style="vertical-align:middle"',
//                     ''
//                 );
//                 // Use this example for IMP 4.2.x+.
//                 // $newmailboxes[$box] = array(
//                 //     'icon' => 'nag.png',
//                 //     'icondir' => $GLOBALS['registry']->getImageDir('nag')
//                 //     'alt' => _("Tasks")
//                 // );
//             } elseif (strpos($box, "INBOX/Notes") !== false
//                 || preg_match("!^user/[^/]+/Notes!", $box)) {
//                 $newmailboxes[$box] = Horde::img(
//                     $GLOBALS['registry']->get('icon', 'mnemo'),
//                     _("Notes"),
//                     'width="16" height="16" style="vertical-align:middle"',
//                     ''
//                 );
//                 // Use this example for IMP 4.2.x+.
//                 // $newmailboxes[$box] = array(
//                 //     'icon' => 'mnemo.png',
//                 //     'icondir' => $GLOBALS['registry']->getImageDir('mnemo')
//                 //     'alt' => _("Notes")
//                 // );
//             } elseif (strpos($box, "INBOX/Contacts") !== false
//                 || preg_match("!^user/[^/]+/Contacts!", $box)) {
//                 $newmailboxes[$box] = Horde::img(
//                     $GLOBALS['registry']->get('icon', 'turba'),
//                     _("Contacts"),
//                     'width="16" height="16" style="vertical-align:middle"',
//                     ''
//                 );
//                 // Use this example for IMP 4.2.x+.
//                 // $newmailboxes[$box] = array(
//                 //     'icon' => 'turba.png',
//                 //     'icondir' => $GLOBALS['registry']->getImageDir('turba')
//                 //     'alt' => _("Contacts")
//                 // );
//             }
//         }
//
//         return $newmailboxes;
//     }
// }

// This is an example hook function for the IMP spam reporting bounce option.
// This function is called when the message is about to be bounced - it
// will return the email address to bounce to.  This is handy for spam
// reporting software (e.g. DSPAM) which has different e-mail aliases for
// spam reporting for each user.

// if (!function_exists('_imp_hook_spam_bounce')) {
//     function _imp_hook_spam_bounce($action)
//     {
//         $prefix = ($action == 'spam') ? 'spam-' : 'fp-';
//         return $prefix . Auth::getBareAuth() . '@example.com';
//     }
// }

// This is an example hook function to hide specified IMAP mailboxes in
// folder listings. If the hook returns false, the mailbox will not be
// displayed.

// if (!function_exists('_imp_hook_display_folder')) {
//     function _imp_hook_display_folder($mailbox) {
//         return ($mailbox == 'DONOTDISPLAY');
//     }
// }

// Sample function for returning the quota. Uses the PECL ssh2
// extension.
//
// @param array $params Parameters for the function, set in servers.php
//
// @return array Tuple with two members:
//               first: disk space used (in bytes)
//               second: maximum disk space (in bytes)
//               In case of an error, return PEAR::raiseError()

// if (!function_exists('_imp_hook_quota')) {
//     function _imp_hook_quota($params = null)
//     {
//         $host = $_SESSION['imp']['server'];
//         $user = $_SESSION['imp']['user'];
//         $pass = Auth::getCredential('password');
//         $command = $params[0];
// 
//         $session = ssh2_connect($host);
//         if (!$session) {
//             return PEAR::raiseError(_("Connection to server failed."), 'horde.error');
//         }
// 
//         if (!ssh2_auth_password($session, $user, $pass)) {
//             return PEAR::raiseError(_("Authentication failed."), 'horde.error');
//         }
// 
//         $stream = ssh2_exec($session, $command, false);
//         stream_set_blocking($stream, true);
// 
//         $quota = preg_split('/\s+/', trim(stream_get_contents($stream)), 2);
//         return array($quota[1] * 1024, $quota[2] * 1024);
//     }
// }

// This is an example hook for retrieving public S/MIME keys of message
// recipients. The hook will be called first when searching for the keys, and
// further lookup techniques will only be used if the hook returns a
// PEAR_Error or an empty result.

// if (!function_exists('_imp_hook_smime_key')) {
//     function _imp_hook_smime_key($address)
//     {
//         $ldapServer = 'localhost';
//         $ldapPort = 389;
//         $searchBase = 'ou=users,dc=example,dc=com';
//         $binddn = 'uid=admin,dc=example,dc=com';
//         $bindpw = 'secret';
//         $attribute = 'simepublickey';
// 
//         if (!@ldap_connect($ldapServer, $ldapPort)) {
//             return;
//         }
//         if (!@ldap_set_option($ds, LDAP_OPT_PROTOCOL_VERSION, 3)) {
//             return;
//         }
//         if (!@ldap_bind($ds, $binddn, $bindpw)) {
//             return;
//         }
// 
//         $searchResult = @ldap_search($ds, $searchBase, 'mail=' . $address);
//         $information = @ldap_get_entries($ds, $searchResult);
//         ldap_close($ds);
// 
//         if ($information === false || $information['count'] == 0) {
//             return;
//         }
// 
//         return $information[0][$attribute][0];
//     }
// }

// This is an example hook for retrieving public PGP keys of message
// recipients. The hook will be called first when searching for the keys, and
// further lookup techniques will only be used if the hook returns a
// PEAR_Error or an empty result.

// if (!function_exists('_imp_hook_pgp_key')) {
//     function _imp_hook_pgp_key($address, $fingerprint)
//     {
//         $ldapServer = 'localhost';
//         $ldapPort = 389;
//         $searchBase = 'ou=users,dc=example,dc=com';
//         $binddn = 'uid=admin,dc=example,dc=com';
//         $bindpw = 'secret';
//         $attribute = 'pgppublickey';
// 
//         if (!@ldap_connect($ldapServer, $ldapPort)) {
//             return;
//         }
//         if (!@ldap_set_option($ds, LDAP_OPT_PROTOCOL_VERSION, 3)) {
//             return;
//         }
//         if (!@ldap_bind($ds, $binddn, $bindpw)) {
//             return;
//         }
// 
//         $searchResult = @ldap_search($ds, $searchBase, 'mail=' . $address);
//         $information = @ldap_get_entries($ds, $searchResult);
//         ldap_close($ds);
// 
//         if ($information === false || $information['count'] == 0) {
//             return;
//         }
// 
//         return $information[0][$attribute][0];
//     }
// }

// Default Kolab hooks:
if (!empty($GLOBALS['conf']['kolab']['enabled'])) {
    require_once 'Horde/Kolab.php';
    if (!function_exists('_imp_hook_mbox_redirect')) {
        function _imp_hook_mbox_redirect($mailbox)
        {
            switch (Kolab::getMailboxType($mailbox)) {
            case 'event':
                return $GLOBALS['registry']->get('webroot', 'kronolith');

            case 'task':
                return $GLOBALS['registry']->get('webroot', 'nag');

            case 'note':
                return $GLOBALS['registry']->get('webroot', 'mnemo');

            case 'contact':
                return $GLOBALS['registry']->get('webroot', 'turba');

            case 'h-prefs':
                return $GLOBALS['registry']->get('webroot', 'horde') . '/services/prefs.php?app=horde';

            default:
                return '';
            }
        }

        function _imp_hook_mbox_icons()
        {
            static $icons;

            if (!empty($icons)) {
                return $icons;
            }

            $folders = Kolab::listFolders();
            $icons = array();
            foreach ($folders as $folder) {
                $name = preg_replace('/^{[^}]+}/', '', $folder[0]);

                switch ($folder[1]) {
                case 'event':
                    $icons[$name] = array(
                        'icon' => 'kronolith.png',
                        'icondir' => $GLOBALS['registry']->getImageDir('kronolith'),
                        'alt' => _("Calendar")
                    );
                    break;

                case 'task':
                    $icons[$name] = array(
                        'icon' => 'nag.png',
                        'icondir' => $GLOBALS['registry']->getImageDir('nag'),
                        'alt' => _("Tasks")
                    );
                    break;

                case 'note':
                    $icons[$name] = array(
                        'icon' => 'mnemo.png',
                        'icondir' => $GLOBALS['registry']->getImageDir('mnemo'),
                        'alt' => _("Notes")
                    );
                    break;

                case 'contact':
                    $icons[$name] = array(
                        'icon' => 'turba.png',
                        'icondir' => $GLOBALS['registry']->getImageDir('turba'),
                        'alt' => _("Contacts")
                    );
                    break;

                case 'h-prefs':
                    $icons[$name] = array(
                        'icon' => 'prefs.png',
                        'icondir' => $GLOBALS['registry']->getImageDir('horde'),
                        'alt' => _("Preferences")
                    );
                    break;
                }
            }

            return $icons;
        }
    }

    if (!function_exists('_imp_hook_display_folder')) {
        function _imp_hook_display_folder($mailbox) {
            $type = Kolab::getMailboxType($mailbox);
            return empty($type) || ($type == 'mail');
        }
    }
}
