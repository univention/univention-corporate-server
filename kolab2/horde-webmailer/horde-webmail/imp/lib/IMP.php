<?php
// Compose encryption options
/**
 * Send Message w/no encryption.
 */
define('IMP_ENCRYPT_NONE', 1);

/**
 * Send Message - PGP Encrypt.
 */
define('IMP_PGP_ENCRYPT', 2);

/**
 * Send Message - PGP Sign.
 */
define('IMP_PGP_SIGN', 3);

/**
 * Send Message - PGP Sign/Encrypt.
 */
define('IMP_PGP_SIGNENC', 4);

/**
 * Send Message - S/MIME Encrypt.
 */
define('IMP_SMIME_ENCRYPT', 5);

/**
 * Send Message - S/MIME Sign.
 */
define('IMP_SMIME_SIGN', 6);

/**
 * Send Message - S/MIME Sign/Encrypt.
 */
define('IMP_SMIME_SIGNENC', 7);

/**
 * Send Message - PGP Encrypt with passphrase.
 */
define('IMP_PGP_SYM_ENCRYPT', 8);

/**
 * Send Message - PGP Sign/Encrypt with passphrase.
 */
define('IMP_PGP_SYM_SIGNENC', 9);

// IMAP Flags
/**
 * Match all IMAP flags.
 */
define('IMP_ALL', 0);

/**
 * \\UNSEEN flag
.*/
define('IMP_UNSEEN', 1);

/**
 * \\DELETED flag
.*/
define('IMP_DELETED', 2);

/**
 * \\ANSWERED flag.
 */
define('IMP_ANSWERED', 4);

/**
 * \\FLAGGED flag.
 */
define('IMP_FLAGGED', 8);

/**
 * \\DRAFT flag.
 */
define('IMP_DRAFT', 16);

/**
 * An email is personal.
 */
define('IMP_PERSONAL', 32);

// IMAP Sorting Constant
/**
 * Sort By Thread.
 */
@define('SORTTHREAD', 161);

// IMP Mailbox view constants
/**
 * Start on the page with the first unseen message.
 */
define('IMP_MAILBOXSTART_FIRSTUNSEEN', 1);

/**
 * Start on the page with the last unseen message.
 */
define('IMP_MAILBOXSTART_LASTUNSEEN', 2);

/**
 * Start on the first page.
 */
define('IMP_MAILBOXSTART_FIRSTPAGE', 3);

/**
 * Start on the last page.
 */
define('IMP_MAILBOXSTART_LASTPAGE', 4);

// IMP mailbox labels
/**
 * The mailbox name to use for search results.
 */
define('IMP_SEARCH_MBOX', '**search_');

// IMP internal indexing strings
/**
 * String used to separate messages.
 */
define('IMP_MSG_SEP', "\0");

/**
 * String used to separate indexes.
 */
define('IMP_IDX_SEP', "\1");

/**
 * IMP Base Class.
 *
 * $Horde: imp/lib/IMP.php,v 1.449.4.128 2009-10-12 22:36:33 slusarz Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jon Parise <jon@horde.org>
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package IMP
 */
class IMP {

    /**
     * Returns the AutoLogin server key.
     *
     * @param boolean $first  Return the first value?
     *
     * @return string  The server key.
     */
    function getAutoLoginServer($first = false)
    {
        if (is_callable(array('Horde', 'loadConfiguration'))) {
            $result = Horde::loadConfiguration('servers.php', array('servers'), 'imp');
            if (is_a($result, 'PEAR_Error')) {
                Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
                return false;
            }
            extract($result);
        } else {
            require IMP_BASE . '/config/servers.php';
        }

        $server_key = null;
        foreach ($servers as $key => $curServer) {
            if (is_null($server_key) && substr($key, 0, 1) != '_') {
                $server_key = $key;
            }
            if (IMP::isPreferredServer($curServer, ($first) ? $key : null)) {
                $server_key = $key;
                if ($first) {
                    break;
                }
            }
        }

        return $server_key;
    }

    /**
     * Returns whether we can log in without a login screen for $server_key.
     *
     * @param string $server_key  The server to check. Defaults to
     *                            IMP::getCurrentServer().
     * @param boolean $force      If true, check $server_key even if there is
     *                            more than one server available.
     *
     * @return boolean  True or false.
     */
    function canAutoLogin($server_key = null, $force = false)
    {
        if (is_callable(array('Horde', 'loadConfiguration'))) {
            $result = Horde::loadConfiguration('servers.php', array('servers'), 'imp');
            if (is_a($result, 'PEAR_Error')) {
                Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
                return false;
            }
            extract($result);
        } else {
            require IMP_BASE . '/config/servers.php';
        }

        $auto_server = IMP::getAutoLoginServer();
        if (is_null($server_key)) {
            $server_key = $auto_server;
        }

        return ((!empty($auto_server) || $force) &&
                Auth::getAuth() &&
                !empty($servers[$server_key]['hordeauth']));
    }

    /**
     * Makes sure the user has been authenticated to view the page.
     *
     * @param boolean $return     If this is true, return false instead of
     *                            exiting/redirecting if authentication fails.
     * @param boolean $hordeauth  Just check for Horde auth and don't bother
     *                            the IMAP server.
     *
     * @return boolean  True on success, false on error.
     */
    function checkAuthentication($return = false, $hordeauth = false)
    {
        if ($hordeauth) {
            $reason = Auth::isAuthenticated();
        } else {
            $auth_imp = &Auth::singleton(array('imp', 'imp'));
            $reason = $auth_imp->authenticate(null, array(), false);
        }

        if ($reason !== true) {
            if ($return) {
                return false;
            }

            if (Util::getFormData('popup')) {
                Util::closeWindowJS();
            } else {
                $url = Auth::addLogoutParameters(IMP::logoutUrl());
                $url = Util::addParameter($url, 'url', Horde::selfUrl(true));
                header('Location: ' . $url);
            }
            exit;
        }

        return true;
    }

    /**
     * Determines if the given mail server is the "preferred" mail server for
     * this web server.  This decision is based on the global 'SERVER_NAME'
     * and 'HTTP_HOST' server variables and the contents of the 'preferred'
     * either field in the server's definition.  The 'preferred' field may
     * take a single value or an array of multiple values.
     *
     * @param string $server  A complete server entry from the $servers hash.
     * @param TODO $key       TODO
     *
     * @return boolean  True if this entry is "preferred".
     */
    function isPreferredServer($server, $key = null)
    {
        static $urlServer;

        if (!isset($urlServer)) {
            $urlServer = Util::getFormData('server');
        }

        if (!empty($urlServer)) {
            return ($key == $urlServer);
        }

        if (!empty($server['preferred'])) {
            if (is_array($server['preferred'])) {
                if (in_array($_SERVER['SERVER_NAME'], $server['preferred']) ||
                    in_array($_SERVER['HTTP_HOST'], $server['preferred'])) {
                    return true;
                }
            } elseif (($server['preferred'] == $_SERVER['SERVER_NAME']) ||
                      ($server['preferred'] == $_SERVER['HTTP_HOST'])) {
                return true;
            }
        }

        return false;
    }

    /**
     * Generates a full c-client server specification string.
     *
     * @param string $mbox  The mailbox to append to end of the server string.
     *
     * @return string  The full spec string.
     */
    function serverString($mbox = null, $protocol = null)
    {
        if (substr($mbox, 0, 1) == '{') {
            return $mbox;
        }

        $srvstr = '{' . $_SESSION['imp']['server'];

        /* If port is not specified, don't include it in the string. */
        if (!empty($_SESSION['imp']['port'])) {
            $srvstr .= ':' . $_SESSION['imp']['port'];
        }

        return $srvstr . '/' . $_SESSION['imp']['protocol'] . '}' . $mbox;
    }

    /**
     * Get a token for protecting a form.
     *
     * @since IMP 4.2
     */
    function getRequestToken($slug)
    {
        require_once 'Horde/Token.php';
        $token = Horde_Token::generateId($slug);
        $_SESSION['horde_form_secrets'][$token] = time();
        return $token;
    }

    /**
     * Check if a token for a form is valid.
     *
     * @since IMP 4.2
     */
    function checkRequestToken($slug, $token)
    {
        if (empty($_SESSION['horde_form_secrets'][$token])) {
            return PEAR::raiseError(_("We cannot verify that this request was really sent by you. It could be a malicious request. If you intended to perform this action, you can retry it now."));
        }

        if ($_SESSION['horde_form_secrets'][$token] + $GLOBALS['conf']['server']['token_lifetime'] < time()) {
            return PEAR::raiseError(sprintf(_("This request cannot be completed because the link you followed or the form you submitted was only valid for %d minutes. Please try again now."), round($GLOBALS['conf']['server']['token_lifetime'] / 60)));
        }

        return true;
    }

    /**
     * Returns the plain text label that is displayed for the current mailbox,
     * replacing IMP_SEARCH_MBOX with an appropriate string and removing
     * namespace and folder prefix information from what is shown to the user.
     *
     * @param string $mbox  The mailbox to use for the label.
     *
     * @return string  The plain text label.
     */
    function getLabel($mbox)
    {
        return ($GLOBALS['imp_search']->isSearchMbox($mbox))
            ? $GLOBALS['imp_search']->getLabel($mbox)
            : IMP::displayFolder($mbox);
    }

    /**
     * Returns the bare address.
     *
     * @param string $address    The address string.
     * @param boolean $multiple  Should we return multiple results?
     *
     * @return mixed  See {@link MIME::bareAddress}.
     */
    function bareAddress($address, $multiple = false)
    {
        static $addresses;

        if (!isset($addresses[(string)$multiple][$address])) {
            require_once 'Horde/MIME.php';
            $addresses[(string)$multiple][$address] = MIME::bareAddress($address, $_SESSION['imp']['maildomain'], $multiple);
        }

        return $addresses[(string)$multiple][$address];
    }

    /**
     * Adds a contact to the user defined address book.
     *
     * @param string $newAddress  The contact's email address.
     * @param string $newName     The contact's name.
     *
     * @return string  A link or message to show in the notification area.
     */
    function addAddress($newAddress, $newName)
    {
        global $registry, $prefs;

        if (empty($newName)) {
            $newName = $newAddress;
        }

        $result = $registry->call('contacts/import',
                                  array(array('name' => $newName, 'email' => $newAddress),
                                        'array', $prefs->getValue('add_source')));
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        } else {
            $contact_link = $registry->link('contacts/show', array('uid' => $result, 'source' => $prefs->getValue('add_source')));
            if (!empty($contact_link) && !is_a($contact_link, 'PEAR_Error')) {
                $contact_link = Horde::link(Horde::url($contact_link), sprintf(_("Go to address book entry of \"%s\""), $newName)) . @htmlspecialchars($newName, ENT_COMPAT, NLS::getCharset()) . '</a>';
            } else {
                $contact_link = @htmlspecialchars($newName, ENT_COMPAT, NLS::getCharset());
            }
            return $contact_link;
        }
    }

    /**
     * Parses an address or address list into the address components.
     *
     * @param string $address    An address or address list.
     * @param boolean $validate  Validate the addresses?
     * @param boolean $domain    Use the local default domain?
     *
     * @return array  A list of address objects or a PEAR_Error object.
     */
    function parseAddressList($address, $validate = false, $domain = false)
    {
        static $parser;

        /* Don't use imap_rfc822_parse_adrlist() since it always expects MIME
         * encoded data (not-useful if $validate is false), doesn't return
         * data easy to parse to create a PEAR_Error object, and doesn't
         * handle lists properly. */

        if (!isset($parser)) {
            require_once 'Mail/RFC822.php';
            $parser = new Mail_RFC822();
        }

        return $parser->parseAddressList($address, ($domain) ? $_SESSION['imp']['maildomain'] : '', null, $validate);
    }

    /**
     * Wrapper around IMP_Folder::flist() which generates the body of a
     * &lt;select&gt; form input from the generated folder list. The
     * &lt;select&gt; and &lt;/select&gt; tags are NOT included in the output
     * of this function.
     *
     * @param string $heading         The label for an empty-value option at
     *                                the top of the list.
     * @param boolean $abbrev         If true, abbreviate long mailbox names
     *                                by replacing the middle of the name with
     *                                '...'.
     * @param array $filter           An array of mailboxes to ignore.
     * @param string $selected        The mailbox to have selected by default.
     * @param boolean $new_folder     If true, display an option to create a
     *                                new folder.
     * @param boolean $inc_tasklists  Should the user's editable tasklists be
     *                                included in the list?
     * @param boolean $inc_vfolder    Should the user's virtual folders be
     *                                included in the list?
     * @param boolean $inc_tasklists  Should the user's editable notepads be
     *                                included in the list?
     *
     * @return string  A string containing <option> elements for each mailbox
     *                 in the list.
     */
    function flistSelect($heading = '', $abbrev = true, $filter = array(),
                         $selected = null, $new_folder = false,
                         $inc_tasklists = false, $inc_vfolder = false,
                         $inc_notepads = false)
    {
        require_once 'Horde/Text.php';
        require_once IMP_BASE . '/lib/Folder.php';

        $imp_folder = &IMP_Folder::singleton();

        /* Don't filter here - since we are going to parse through every
         * member of the folder list below anyway, we can filter at that time.
         * This allows us the have a single cached value for the folder list
         * rather than a cached value for each different mailbox we may
         * visit. */
        $mailboxes = $imp_folder->flist_IMP();
        $text = '';

        if (strlen($heading) > 0) {
            $text .= '<option value="">' . $heading . "</option>\n";
        }

        if ($new_folder &&
            (!empty($GLOBALS['conf']['hooks']['permsdenied']) ||
             (IMP::hasPermission('create_folders') &&
              IMP::hasPermission('max_folders')))) {
            $text .= '<option value="" disabled="disabled">- - - - - - - - -</option>' . "\n";
            $text .= '<option value="*new*">' . _("New Folder") . "</option>\n";
            $text .= '<option value="" disabled="disabled">- - - - - - - - -</option>' . "\n";
        }

        /* Add the list of mailboxes to the lists. */
        $filter = array_flip($filter);
        foreach ($mailboxes as $mbox) {
            if (isset($filter[$mbox['val']])) {
                continue;
            }

            $val = isset($filter[$mbox['val']]) ? '' : htmlspecialchars($mbox['val']);
            $sel = ($mbox['val'] && ($mbox['val'] === $selected)) ? ' selected="selected"' : '';
            $label = ($abbrev) ? $mbox['abbrev'] : $mbox['label'];
            $text .= sprintf('<option value="%s"%s>%s</option>%s', $val, $sel, Text::htmlSpaces($label), "\n");
        }

        /* Add the list of virtual folders to the list. */
        if ($inc_vfolder) {
            $vfolders = $GLOBALS['imp_search']->listQueries(true);
            if (!empty($vfolders)) {
                $vfolder_sel = $GLOBALS['imp_search']->searchMboxID();
                $text .= '<option value="" disabled="disabled">- - - - - - - - -</option>' . "\n";
                foreach ($vfolders as $id => $val) {
                    $text .= sprintf('<option value="%s"%s>%s</option>%s', $GLOBALS['imp_search']->createSearchID($id), ($vfolder_sel == $id) ? ' selected="selected"' : '', Text::htmlSpaces($val), "\n");
                }
            }
        }

        /* Add the list of editable tasklists to the list. */
        if ($inc_tasklists && $_SESSION['imp']['tasklistavail']) {
            $tasklists = $GLOBALS['registry']->call('tasks/listTasklists',
                                                    array(false, PERMS_EDIT));

            if (!is_a($tasklists, 'PEAR_Error') && count($tasklists)) {
                $text .= '<option value="" disabled="disabled">&nbsp;</option><option value="" disabled="disabled">- - ' . _("Task Lists") . ' - -</option>' . "\n";

                foreach ($tasklists as $id => $tasklist) {
                    $text .= sprintf('<option value="%s">%s</option>%s',
                                     '_tasklist_' . $id,
                                     Text::htmlSpaces($tasklist->get('name')),
                                     "\n");
                }
            }
        }

        /* Add the list of editable notepads to the list. */
        if ($inc_notepads && $_SESSION['imp']['notepadavail']) {
            $notepads = $GLOBALS['registry']->call('notes/listNotepads',
                                                    array(false, PERMS_EDIT));

            if (!is_a($notepads, 'PEAR_Error') && count($notepads)) {
                $text .= '<option value="" disabled="disabled">&nbsp;</option><option value="" disabled="disabled">- - ' . _("Notepads") . ' - -</option>' . "\n";

                foreach ($notepads as $id => $notepad) {
                    $text .= sprintf('<option value="%s">%s</option>%s',
                                     '_notepad_' . $id,
                                     Text::htmlSpaces($notepad->get('name')),
                                     "\n");
                }
            }
        }

        return $text;
    }

    /**
     * Checks for To:, Subject:, Cc:, and other compose window arguments and
     * pass back either a URI fragment or an associative array with any of
     * them which are present.
     *
     * @param string $format  Either 'uri' or 'array'.
     *
     * @return string  A URI fragment or an associative array with any compose
     *                 arguments present.
     */
    function getComposeArgs()
    {
        $args = array();
        $fields = array('to', 'cc', 'bcc', 'message', 'body', 'subject');

        foreach ($fields as $val) {
            if (($$val = Util::getFormData($val))) {
                $args[$val] = $$val;
            }
        }

        /* Decode mailto: URLs. */
        if (isset($args['to']) && (strpos($args['to'], 'mailto:') === 0)) {
            $mailto = @parse_url($args['to']);
            if (is_array($mailto)) {
                $args['to'] = isset($mailto['path']) ? $mailto['path'] : '';
                if (!empty($mailto['query'])) {
                    parse_str($mailto['query'], $vals);
                    foreach ($fields as $val) {
                        if (isset($vals[$val])) {
                            $args[$val] = $vals[$val];
                        }
                    }
                }
            }
        }

        return $args;
    }

    /**
     * Open a compose window.
     */
    function openComposeWin($options = array())
    {
        global $prefs;

        if ($prefs->getValue('compose_popup')) {
            return true;
        } else {
            $options += IMP::getComposeArgs();
            $url = Util::addParameter(Horde::applicationUrl('compose.php', true),
                                      $options, null, false);
            header('Location: ' . $url);
            return false;
        }
    }

    /**
     * Prepares the arguments to use for composeLink().
     *
     * @since IMP 4.2
     *
     * @param mixed $args   List of arguments to pass to compose.php. If this
     *                      is passed in as a string, it will be parsed as a
     *                      toaddress?subject=foo&cc=ccaddress (mailto-style)
     *                      string.
     * @param array $extra  Hash of extra, non-standard arguments to pass to
     *                      compose.php.
     *
     * @return array  The array of args to use for composeLink().
     */
    function composeLinkArgs($args = array(), $extra = array())
    {
        if (is_string($args)) {
            $string = $args;
            $args = array();
            if (($pos = strpos($string, '?')) !== false) {
                parse_str(substr($string, $pos + 1), $args);
                $args['to'] = substr($string, 0, $pos);
            } else {
                $args['to'] = $string;
            }
        }

        /* Merge the two argument arrays. */
        if (is_array($extra) && !empty($extra)) {
            $args = array_merge($args, $extra);
        }

        return $args;
    }

    /**
     * Returns the appropriate link to call the message composition screen.
     *
     * @param mixed $args   List of arguments to pass to compose.php. If this
     *                      is passed in as a string, it will be parsed as a
     *                      toaddress?subject=foo&cc=ccaddress (mailto-style)
     *                      string.
     * @param array $extra  Hash of extra, non-standard arguments to pass to
     *                      compose.php.
     *
     * @return string  The link to the message composition screen.
     */
    function composeLink($args = array(), $extra = array())
    {
        $args = IMP::composeLinkArgs($args, $extra);

        if ($GLOBALS['prefs']->getValue('compose_popup')
            && $GLOBALS['browser']->hasFeature('javascript')) {
            Horde::addScriptFile('prototype.js', 'imp', true);
            Horde::addScriptFile('popup.js', 'imp', true);
            if (isset($args['to'])) {
                $args['to'] = addcslashes($args['to'], '\\"');
            }
            return "javascript:" . IMP::popupIMPString('compose.php', $args);
        } else {
            return Util::addParameter(Horde::applicationUrl('compose.php'), $args);
        }
    }

    /**
     * Generates an URL to the logout screen that includes any known
     * information, such as username, server, etc., that can be filled in on
     * the login form.
     *
     * @return string  Logout URL with logout parameters added.
     */
    function logoutUrl()
    {
        $params = array(
            'imapuser' => isset($_SESSION['imp']['user']) ?
                          $_SESSION['imp']['user'] :
                          Util::getFormData('imapuser'),
            'server'   => isset($_SESSION['imp']['server']) ?
                          $_SESSION['imp']['server'] :
                          Util::getFormData('server'),
            'port'     => isset($_SESSION['imp']['port']) ?
                          $_SESSION['imp']['port'] :
                          Util::getFormData('port'),
            'protocol' => isset($_SESSION['imp']['protocol']) ?
                          $_SESSION['imp']['protocol'] :
                          Util::getFormData('protocol'),
            'language' => isset($_SESSION['imp']['language']) ?
                          $_SESSION['imp']['language'] :
                          Util::getFormData('language'),
            'smtphost' => isset($_SESSION['imp']['smtphost']) ?
                          $_SESSION['imp']['smtphost'] :
                          Util::getFormData('smtphost'),
            'smtpport' => isset($_SESSION['imp']['smtpport']) ?
                          $_SESSION['imp']['smtpport'] :
                          Util::getFormData('smtpport'),
        );

        return Util::addParameter($GLOBALS['registry']->get('webroot', 'imp') . '/login.php', array_diff($params, array('')), null, false);
    }

    /**
     * If there is information available to tell us about a prefix in front of
     * mailbox names that shouldn't be displayed to the user, then use it to
     * strip that prefix out.
     *
     * @param string $folder        The folder name to display.
     * @param boolean $notranslate  Do not translate the folder prefix.
     *
     * @return string  The folder, with any prefix gone.
     */
    function displayFolder($folder, $notranslate = false)
    {
        static $cache = array();

        if (isset($cache[$folder])) {
            return $cache[$folder];
        }

        if ($folder == 'INBOX') {
            $out = _("Inbox");
        } else {
            $namespace_info = IMP::getNamespace($folder);
            if (($namespace_info !== null) &&
                !empty($namespace_info['name']) &&
                ($namespace_info['type'] == 'personal') &&
                substr($folder, 0, strlen($namespace_info['name'])) == $namespace_info['name']) {
                $out = substr($folder, strlen($namespace_info['name']));
            } elseif (!$notranslate &&
                      !is_null($namespace_info) &&
                      (strpos($folder, 'INBOX' . $namespace_info['delimiter']) === 0)) {
                $out = _("Inbox") . substr($folder, 5);
            } else {
                $out = $folder;
            }

            $out = String::convertCharset($out, 'UTF7-IMAP');
        }

        if (!$notranslate) {
            $cache[$folder] = $out;
        }

        return $out;
    }

    /**
     * Filters a string, if requested.
     *
     * @param string $text  The text to filter.
     *
     * @return string  The filtered text (if requested).
     */
    function filterText($text)
    {
        global $conf, $prefs;

        if ($prefs->getValue('filtering') && strlen($text)) {
            require_once 'Horde/Text/Filter.php';
            $text = Text_Filter::filter($text, 'words', array('words_file' => $conf['msgsettings']['filtering']['words'], 'replacement' => $conf['msgsettings']['filtering']['replacement']));
        }

        return $text;
    }

    /**
     * Returns the specified permission for the current user.
     *
     * @since IMP 4.1
     *
     * @param string $permission  A permission.
     * @param boolean $value      If true, the method returns the value of a
     *                            scalar permission, otherwise whether the
     *                            permission limit has been hit already.
     *
     * @return mixed  The value of the specified permission.
     */
    function hasPermission($permission, $value = false)
    {
        global $perms;

        if (!$perms->exists('imp:' . $permission)) {
            return true;
        }

        $allowed = $perms->getPermissions('imp:' . $permission);
        if (is_array($allowed)) {
            switch ($permission) {
            case 'create_folders':
                $allowed = (bool)count(array_filter($allowed));
                break;

            case 'max_folders':
            case 'max_recipients':
            case 'max_timelimit':
                $allowed = max($allowed);
                break;
            }
        }
        if ($permission == 'max_folders' && !$value) {
            $folder = &IMP_Folder::singleton();
            $allowed = $allowed > count($folder->flist_IMP(array(), false));
        }

        return $allowed;
    }

    /**
     * Build IMP's list of menu items.
     *
     * @param string $returnType  Either 'object' or 'string'.
     *
     * @return mixed  Either a Horde_Menu object or the rendered menu text.
     */
    function getMenu($returnType = 'object')
    {
        global $conf, $prefs, $registry;

        require_once 'Horde/Menu.php';

        $menu_search_url = Horde::applicationUrl('search.php');
        $menu_mailbox_url = Horde::applicationUrl('mailbox.php');

        $spam_folder = IMP::folderPref($prefs->getValue('spam_folder'), true);

        $menu = new Menu(HORDE_MENU_MASK_ALL & ~HORDE_MENU_MASK_LOGIN);

        $menu->add(IMP::generateIMPUrl($menu_mailbox_url, 'INBOX'), _("_Inbox"), 'folders/inbox.png');

        if (($_SESSION['imp']['base_protocol'] != 'pop3') &&
            $prefs->getValue('use_trash') &&
            $prefs->getValue('empty_trash_menu')) {
            $mailbox = null;
            if ($prefs->getValue('use_vtrash')) {
                $mailbox = $GLOBALS['imp_search']->createSearchID($prefs->getValue('vtrash_id'));
            } else {
                $trash_folder = IMP::folderPref($prefs->getValue('trash_folder'), true);
                if (($trash_folder !== null)) {
                    $mailbox = $trash_folder;
                }
            }

            if (!empty($mailbox)) {
                $menu_trash_url = Util::addParameter(IMP::generateIMPUrl($menu_mailbox_url, $mailbox), array('actionID' => 'empty_mailbox', 'mailbox_token' => IMP::getRequestToken('imp.mailbox')));
                $menu->add($menu_trash_url, _("Empty _Trash"), 'empty_trash.png', null, null, "return window.confirm('" . addslashes(_("Are you sure you wish to empty your trash folder?")) . "');", '__noselection');
            }
        }

        if (($_SESSION['imp']['base_protocol'] != 'pop3') &&
            !empty($spam_folder) &&
            $prefs->getValue('empty_spam_menu')) {
            $menu_spam_url = Util::addParameter(IMP::generateIMPUrl($menu_mailbox_url, $spam_folder), array('actionID' => 'empty_mailbox', 'mailbox_token' => IMP::getRequestToken('imp.mailbox')));
            $menu->add($menu_spam_url, _("Empty _Spam"), 'empty_spam.png', null, null, "return window.confirm('" . addslashes(_("Are you sure you wish to empty your spam folder?")) . "');", '__noselection');
        }

        $menu->add(IMP::composeLink(array('mailbox' => $GLOBALS['imp_mbox']['mailbox'])), _("_New Message"), 'compose.png');

        if ($conf['user']['allow_folders']) {
            $menu->add(Util::nocacheUrl(Horde::applicationUrl('folders.php')), _("_Folders"), 'folders/folder.png');
        }
        $menu->add($menu_search_url, _("_Search"), 'search.png', $registry->getImageDir('horde'));
        if (($_SESSION['imp']['base_protocol'] != 'pop3') && $prefs->getValue('fetchmail_menu')) {
            if ($prefs->getValue('fetchmail_popup')) {
                $menu->add(Horde::applicationUrl('fetchmail.php'), _("F_etch Mail"), 'fetchmail.png', null, 'fetchmail', 'window.open(this.href, \'fetchmail\', \'toolbar=no,location=no,status=yes,scrollbars=yes,resizable=yes,width=300,height=450,left=100,top=100\'); return false;');
            } else {
                $menu->add(Horde::applicationUrl('fetchmail.php'), _("F_etch Mail"), 'fetchmail.png');
            }
        }
        if ($prefs->getValue('filter_menuitem')) {
            $menu->add(Horde::applicationUrl('filterprefs.php'), _("Fi_lters"), 'filters.png');
        }

        /* Logout. If IMP can auto login or IMP is providing authentication,
         * then we only show the logout link if the sidebar isn't shown or if
         * the configuration says to always show the current user a logout
         * link. */
        $impAuth = Auth::getProvider() == 'imp';
        $impAutoLogin = IMP::canAutoLogin();
        if (!($impAuth || $impAutoLogin) ||
            !$prefs->getValue('show_sidebar') ||
            Horde::showService('logout')) {

            /* If IMP provides authentication and the sidebar isn't always on,
             * target the main frame for logout to hide the sidebar while
             * logged out. */
            $logout_target = null;
            if ($impAuth || $impAutoLogin) {
                $logout_target = '_parent';
            }

            /* If IMP doesn't provide Horde authentication then we need to use
             * IMP's logout screen since logging out should *not* end a Horde
             * session. */
            $logout_url = IMP::getLogoutUrl();

            $id = $menu->add($logout_url, _("_Log out"), 'logout.png', $registry->getImageDir('horde'), $logout_target);
            $menu->setPosition($id, HORDE_MENU_POS_LAST);
        }

        if ($returnType == 'object') {
            return $menu;
        } else {
            return $menu->render();
        }
    }

    /**
     * Outputs IMP's menu to the current output stream.
     *
     * @since IMP 4.2
     */
    function menu()
    {
        require_once IMP_BASE . '/lib/Template.php';
        $t = new IMP_Template();
        $t->set('forminput', Util::formInput());
        $t->set('webkit', $GLOBALS['browser']->isBrowser('konqueror'));
        $t->set('use_folders', ($_SESSION['imp']['base_protocol'] != 'pop3') &&
                               $GLOBALS['conf']['user']['allow_folders'], true);
        if ($t->get('use_folders')) {
            $t->set('accesskey', $GLOBALS['prefs']->getValue('widget_accesskey') ? Horde::getAccessKey(_("Open Fo_lder")) : '', true);
            $t->set('flist', IMP::flistSelect('', true, array(), $GLOBALS['imp_mbox']['mailbox'], false, false, true));

            $menu_view = $GLOBALS['prefs']->getValue('menu_view');
            $link = Horde::link('#', '', '', '', 'folderSubmit(true); return false;');
            $t->set('flink', sprintf('<ul><li class="rightFloat">%s%s<br />%s</a></li></ul>', $link, ($menu_view != 'text') ? Horde::img('folders/folder_open.png', _("Open Folder"), ($menu_view == 'icon') ? array('title' => _("Open Folder")) : array()) : '', ($menu_view != 'icon') ? Horde::highlightAccessKey(_("Open Fo_lder"), $t->get('accesskey')) : ''));
        }
        $t->set('menu_string', IMP::getMenu('string'));

        echo $t->fetch(IMP_TEMPLATES . '/menu.html');
    }

    /**
     * Outputs IMP's status/notification bar.
     */
    function status()
    {
        global $notification;

        $imp_imap = &IMP_IMAP::singleton();

        if ($imp_imap->stream()) {
            $alerts = imap_alerts();
            if (is_array($alerts)) {
                $alerts = str_replace('[ALERT] ', '', $alerts);
                foreach ($alerts as $alert) {
                    $notification->push($alert, 'horde.warning');
                }
            }
        }

        /* BC check. */
        if (class_exists('Notification_Listener_audio')) {
            $notification->notify(array('listeners' => array('status', 'audio')));
        }
    }

    /**
     * Outputs IMP's quota information.
     */
    function quota()
    {
        $quotadata = IMP::quotaData(true);
        if (!empty($quotadata)) {
            require_once IMP_BASE . '/lib/Template.php';
            $t = new IMP_Template();
            $t->set('class', $quotadata['class']);
            $t->set('message', $quotadata['message']);
            echo $t->fetch(IMP_TEMPLATES . '/quota/quota.html');
        }
    }

    /**
     * Returns data needed to output quota.
     *
     * @since IMP 4.2
     *
     * @param boolean $long  Output long messages?
     *
     * @return array  Array with these keys: class, message, percent.
     */
    function quotaData($long = true)
    {
        if (!isset($_SESSION['imp']['quota']) ||
            !is_array($_SESSION['imp']['quota'])) {
            return false;
        }

        require_once IMP_BASE . '/lib/Quota.php';
        $quotaDriver = &IMP_Quota::singleton($_SESSION['imp']['quota']['driver'], $_SESSION['imp']['quota']['params']);
        if ($quotaDriver === false) {
            return false;
        }

        $quota = $quotaDriver->getQuota();
        if (is_a($quota, 'PEAR_Error')) {
            Horde::logMessage($quota, __FILE__, __LINE__, PEAR_LOG_ERR);
            return false;
        }

        $strings = $quotaDriver->getMessages();
        $ret = array('percent' => 0);

        if ($quota['limit'] != 0) {
            $quota['usage'] = $quota['usage'] / (1024 * 1024.0);
            $quota['limit'] = $quota['limit'] / (1024 * 1024.0);
            $ret['percent'] = ($quota['usage'] * 100) / $quota['limit'];
            if ($ret['percent'] >= 90) {
                $ret['class'] = 'quotaalert';
            } elseif ($ret['percent'] >= 75) {
                $ret['class'] = 'quotawarn';
            } else {
                $ret['class'] = 'control';
            }
            if ($long) {
                $ret['message'] = sprintf($strings['long'], $quota['usage'],
                                          $quota['limit'], $ret['percent']);
            } else {
                $ret['message'] = sprintf($strings['short'], $ret['percent'],
                                          $quota['limit']);
            }
        } else {
            // Hide unlimited quota message?
            if (!empty($_SESSION['imp']['quota']['params']['hide_quota_when_unlimited'])) {
                return false;
            }

            $ret['class'] = 'control';
            if ($quota['usage'] != 0) {
                $quota['usage'] = $quota['usage'] / (1024 * 1024.0);
                if ($long) {
                    $ret['message'] = sprintf($strings['nolimit_long'],
                                              $quota['usage']);
                } else {
                    $ret['message'] = sprintf($strings['nolimit_short'],
                                              $quota['usage']);
                }
            } else {
                if ($long) {
                    $ret['message'] = sprintf(_("Quota status: NO LIMIT"));
                } else {
                    $ret['message'] = _("No limit");
                }
            }
        }

        return $ret;
    }

    /**
     * Outputs the necessary javascript code to display the new mail
     * notification message.
     *
     * @param mixed $var  Either an associative array with mailbox names as
     *                    the keys and the message count as the values or
     *                    an integer indicating the number of new messages
     *                    in the current mailbox.
     *
     * @return string  The javascript for the popup message.
    */
    function getNewMessagePopup($var)
    {
        require_once IMP_BASE . '/lib/Template.php';
        $t = new IMP_Template();
        $t->setOption('gettext', true);
        if (is_array($var)) {
            if (empty($var)) {
                return;
            }
            $folders = array();
            foreach ($var as $mb => $nm) {
                $folders[] = array(
                    'url' => Util::addParameter(IMP::generateIMPUrl('mailbox.php', $mb), 'no_newmail_popup', 1),
                    'name' => htmlspecialchars(IMP::displayFolder($mb)),
                    'new' => (int)$nm,
                );
            }
            $t->set('folders', $folders);

            if ($_SESSION['imp']['base_protocol'] != 'pop3' &&
                $GLOBALS['prefs']->getValue('use_vinbox') &&
                ($vinbox_id = $GLOBALS['prefs']->getValue('vinbox_id'))) {
                $t->set('vinbox', Horde::link(Util::addParameter(IMP::generateIMPUrl('mailbox.php', $GLOBALS['imp_search']->createSearchID($vinbox_id)), 'no_newmail_popup', 1)));
            }
        } else {
            $t->set('msg', ($var == 1) ? _("You have 1 new message.") : sprintf(_("You have %s new messages."), $var));
        }
        $t_html = str_replace("\n", ' ', $t->fetch(IMP_TEMPLATES . '/newmsg/alert.html'));

        Horde::addScriptFile('prototype.js', 'imp', true);
        Horde::addScriptFile('effects.js', 'imp', true);
        Horde::addScriptFile('redbox.js', 'imp', true);
        return 'RedBox.overlay = false; RedBox.showHtml(\'' . addcslashes($t_html, "'/") . '\');';
    }

    /**
     * Generates the URL to the prefs page.
     *
     * @param boolean $full  Generate full URL?
     *
     * @return string  The URL to the IMP prefs page.
     */
    function prefsURL($full = false)
    {
        return Util::addParameter(Horde::url($GLOBALS['registry']->get('webroot', 'horde') . '/services/prefs.php', $full), array('app' => 'imp'));
    }

    /**
     * Are we currently in "print" mode?
     *
     * @param boolean $mode  True if in print mode, false if not.
     *
     * @return boolean  Returns true if in "print" mode.
     */
    function printMode($mode = null)
    {
        static $print = false;
        if (($mode !== null)) {
            $print = $mode;
        }
        return $print;
    }

    /**
     * Get message indices list.
     *
     * @param mixed $indices  The following inputs are allowed:
     * <pre>
     * 1. An array of messages indices in the following format:
     *    msg_id IMP_IDX_SEP msg_folder
     *      msg_id      = Message index of the message
     *      IMP_IDX_SEP = IMP constant used to separate index/folder
     *      msg_folder  = The full folder name containing the message index
     * 2. An array with the full folder name as keys and an array of message
     *    indices as the values.
     * 3. An IMP_Mailbox object, which will use the current index/folder
     *    as determined by the object. If an IMP_Mailbox object is used, it
     *    will be updated after the action is performed.
     * </pre>
     *
     * @return mixed  Returns an array with the folder as key and an array
     *                of message indices as the value (See #2 above).
     *                Else, returns false.
     */
    function parseIndicesList($indices)
    {
        $msgList = array();

        if (is_a($indices, 'IMP_Mailbox')) {
            $msgIdx = $indices->getIMAPIndex();
            if (empty($msgIdx)) {
                return false;
            }
            $msgList[$msgIdx['mailbox']][] = $msgIdx['index'];
            return $msgList;
        }

        if (!is_array($indices)) {
            return array();
        }
        if (!count($indices)) {
            return array();
        }

        reset($indices);
        if (!is_array(current($indices))) {
            /* Build the list of indices/mailboxes to delete if input
               is of format #1. */
            foreach ($indices as $msgIndex) {
                if (strpos($msgIndex, IMP_IDX_SEP) === false) {
                    return false;
                } else {
                    list($val, $key) = explode(IMP_IDX_SEP, $msgIndex);
                    $msgList[$key][] = $val;
                }
            }
        } else {
            /* We are dealing with format #2. */
            foreach ($indices as $key => $val) {
                if ($GLOBALS['imp_search']->isSearchMbox($key)) {
                    $msgList += IMP::parseIndicesList($val);
                } else {
                    /* Make sure we don't have any duplicate keys. */
                    $msgList[$key] = is_array($val) ? array_keys(array_flip($val)) : array($val);
                }
            }
        }

        return $msgList;
    }

    /**
     * Either sets or checks the value of the logintasks flag.
     *
     * @param integer $set  The value of the flag.
     *
     * @return integer  The value of the flag.
     *                  0 = No login tasks pending
     *                  1 = Login tasks pending
     *                  2 = Login tasks pending, previous tasks interrupted
     */
    function loginTasksFlag($set = null)
    {
        if (($set !== null)) {
            $_SESSION['imp']['_logintasks'] = $set;
        }

        return isset($_SESSION['imp']['_logintasks']) ? $_SESSION['imp']['_logintasks'] : 0;
    }

    /**
     * Get namespace info for a full folder path.
     *
     * @since IMP 4.1
     *
     * @param string $mailbox  The folder path. If empty, will return info
     *                         on the default namespace (i.e. the first
     *                         personal namespace).
     * @param boolean $empty   If true and no matching namespace is found,
     *                         return the empty namespace, if it exists.
     *
     * @return mixed  The namespace info for the folder path or null if the
     *                path doesn't exist.
     */
    function getNamespace($mailbox = null, $empty = true)
    {
        static $cache = array();

        if ($_SESSION['imp']['base_protocol'] == 'pop3') {
            return null;
        }

        if ($mailbox === null) {
            reset($_SESSION['imp']['namespace']);
            $mailbox = key($_SESSION['imp']['namespace']);
        }

        $key = (int)$empty;
        if (isset($cache[$key][$mailbox])) {
            return $cache[$key][$mailbox];
        }

        foreach ($_SESSION['imp']['namespace'] as $key => $val) {
            $mbx = $mailbox . $val['delimiter'];
            if (!empty($key) && (strpos($mbx, $key) === 0)) {
                $cache[$key][$mailbox] = $val;
                return $val;
            }
        }

        if ($empty && isset($_SESSION['imp']['namespace'][''])) {
            $cache[$key][$mailbox] = $_SESSION['imp']['namespace'][''];
        } else {
            $cache[$key][$mailbox] = null;
        }

        return $cache[$key][$mailbox];
    }

    /**
     * Get the default personal namespace.
     *
     * @since IMP 4.1
     *
     * @return mixed  The default personal namespace info.
     */
    function defaultNamespace()
    {
        static $default = null;

        if ($_SESSION['imp']['base_protocol'] == 'pop3') {
            return null;
        }

        if (!$default) {
            foreach ($_SESSION['imp']['namespace'] as $val) {
                if ($val['type'] == 'personal') {
                    $default = $val;
                    break;
                }
            }
        }

        return $default;
    }

    /**
     * Convert a preference value to/from the value stored in the preferences.
     *
     * Preferences that need to call this function before storing/retrieving:
     *   trash_folder, spam_folder, drafts_folder, sent_mail_folder
     * To allow folders from the personal namespace to be stored without this
     * prefix for portability, we strip the personal namespace. To tell apart
     * folders from the personal and any empty namespace, we prefix folders
     * from the empty namespace with the delimiter.
     *
     * @since IMP 4.1
     *
     * @param string $mailbox  The folder path.
     * @param boolean $append  True - convert from preference value.
     *                         False - convert to preference value.
     *
     * @return string  The folder name.
     */
    function folderPref($folder, $append)
    {
        $def_ns = IMP::defaultNamespace();
        $empty_ns = IMP::getNamespace('');
        if ($append) {
            /* Converting from preference value. */
            if (($empty_ns !== null) &&
                strpos($folder, $empty_ns['delimiter']) === 0) {
                /* Prefixed with delimiter => from empty namespace. */
                $folder = substr($folder, strlen($empty_ns['delimiter']));
            } elseif (($ns = IMP::getNamespace($folder, false)) == null) {
                /* No namespace prefix => from personal namespace. */
                $folder = $def_ns['name'] . $folder;
            }
        } elseif (!$append && (($ns = IMP::getNamespace($folder)) !== null)) {
            /* Converting to preference value. */
            if ($ns['name'] == $def_ns['name']) {
                /* From personal namespace => strip namespace. */
                $folder = substr($folder, strlen($def_ns['name']));
            } elseif ($ns['name'] == $empty_ns['name']) {
                /* From empty namespace => prefix with delimiter. */
                $folder = $empty_ns['delimiter'] . $folder;
            }
        }
        return $folder;
    }

    /**
     * Make sure a user-entered mailbox contains namespace information.
     *
     * @since IMP 4.1
     *
     * @param string $mbox  The user-entered mailbox string.
     *
     * @return string  The mailbox string with any necessary namespace info
     *                 added.
     */
    function appendNamespace($mbox)
    {
        $ns_info = IMP::getNamespace($mbox);
        if ($ns_info === null) {
            $ns_info = IMP::defaultNamespace();
        }
        return $ns_info['name'] . $mbox;
    }

    /**
     * Generates a URL with necessary mailbox/index information.
     *
     * @since IMP 4.2
     *
     * @param string $page      Page name to link to.
     * @param string $mailbox   The base mailbox to use on the linked page.
     * @param string $index     The index to use on the linked page.
     * @param string $tmailbox  The mailbox associated with $index.
     * @param boolean $encode   Encode the argument separator? (since 4.2.1)
     *
     * @return string  URL to $page with any necessary mailbox information
     *                 added to the parameter list of the URL.
     */
    function generateIMPUrl($page, $mailbox, $index = null, $tmailbox = null,
                            $encode = true)
    {
        return Util::addParameter(Horde::applicationUrl($page), IMP::getIMPMboxParameters($mailbox, $index, $tmailbox), null, $encode);
    }

    /**
     * Returns a list of parameters necessary to indicate current mailbox
     * status.
     *
     * @since IMP 4.2
     *
     * @param string $mailbox   The mailbox to use on the linked page.
     * @param string $index     The index to use on the linked page.
     * @param string $tmailbox  The mailbox associated with $index to use on
     *                          the linked page.
     *
     * @return array  The list of parameters needed to indicate the current
     *                mailbox status.
     */
    function getIMPMboxParameters($mailbox, $index = null, $tmailbox = null)
    {
        $params = array('mailbox' => $mailbox);
        if ($index !== null) {
            $params['index'] = $index;
            if ($mailbox != $tmailbox) {
                $params['thismailbox'] = $tmailbox;
            }
        }
        return $params;
    }

    /**
     * Determine whether we're hiding deleted messages.
     *
     * @since IMP 4.2
     *
     * @param boolean $force  Force a redetermination of the return value
     *                        (return value is normally cached after the first
     *                        call).
     *
     * @return boolean  True if deleted messages should be hidden.
     */
    function hideDeletedMsgs($force = false)
    {
        static $delhide;

        if (!isset($delhide) || $force) {
            if ($GLOBALS['prefs']->getValue('use_vtrash')) {
                $delhide = !$GLOBALS['imp_search']->isVTrashFolder();
            } else {
                $sortpref = IMP::getSort();
                $delhide = ($GLOBALS['prefs']->getValue('delhide') &&
                            !$GLOBALS['prefs']->getValue('use_trash') &&
                            ($GLOBALS['imp_search']->isSearchMbox() ||
                             ($sortpref['by'] != SORTTHREAD)));
            }
        }

        return $delhide;
    }

    /**
     * Return a list of valid encrypt HTML option tags.
     *
     * @since IMP 4.2
     *
     * @param string $default      The default encrypt option.
     * @param boolean $returnList  Whether to return a hash with options
     *                             instead of the options tag.
     *
     * @return string  The list of option tags.
     */
    function encryptList($default = null, $returnList = false)
    {
        if (empty($default)) {
            $default = $GLOBALS['prefs']->getValue('default_encrypt');
        }
        $enc_options = array(IMP_ENCRYPT_NONE => _("No Encryption"));
        if (!empty($GLOBALS['conf']['utils']['gnupg']) &&
            $GLOBALS['prefs']->getValue('use_pgp')) {
            $enc_options[IMP_PGP_ENCRYPT] = _("PGP Encrypt Message");
            $enc_options[IMP_PGP_SIGN] = _("PGP Sign Message");
            $enc_options[IMP_PGP_SIGNENC] = _("PGP Sign/Encrypt Message");
            require_once 'Horde/Crypt/pgp.php';
            if (is_callable(array('Horde_Crypt_pgp', 'encryptedSymmetrically'))) {
                $enc_options[IMP_PGP_SYM_ENCRYPT] = _("PGP Encrypt Message with passphrase");
                $enc_options[IMP_PGP_SYM_SIGNENC] = _("PGP Sign/Encrypt Message with passphrase");
            }
        }
        if ($GLOBALS['prefs']->getValue('use_smime')) {
            $enc_options[IMP_SMIME_ENCRYPT] = _("S/MIME Encrypt Message");
            $enc_options[IMP_SMIME_SIGN] = _("S/MIME Sign Message");
            $enc_options[IMP_SMIME_SIGNENC] = _("S/MIME Sign/Encrypt Message");
        }

        if ($returnList) {
            return $enc_options;
        }

        $output = '';
        foreach ($enc_options as $key => $val) {
             $output .= '<option value="' . $key . '"' . (($default == $key) ? ' selected="selected"' : '') . '>' . $val . '</option>' . "\n";
        }

        return $output;
    }

    /**
     * Returns true if we are doing a login for recomposition purposes.
     *
     * @since IMP 4.2
     *
     * @return boolean  True if current pageload is for purposes of logging in
     *                  to resume composing a message.
     */
    function recomposeLogin()
    {
        return strstr($_SERVER['PHP_SELF'], 'redirect.php') && Util::getFormData('recompose');
    }

    /**
     * Return the sorting preference for the current mailbox.
     *
     * @since IMP 4.2
     *
     * @param string $mbox  The mailbox to use (defaults to current mailbox
     *                      in the session).
     *
     * @return array  An array with the following keys:
     *                'by'  - Sort type
     *                'dir' - Sort direction
     *                'limit' - Was the sort limit reached?
     */
    function getSort($mbox = null)
    {
        if ($mbox === null) {
            $mbox = $GLOBALS['imp_mbox']['mailbox'];
        }

        $prefmbox = ($GLOBALS['imp_search']->isSearchMbox($mbox)) ? $mbox : IMP::folderPref($mbox, false);

        $sortpref = @unserialize($GLOBALS['prefs']->getValue('sortpref'));
        $entry = (isset($sortpref[$prefmbox])) ? $sortpref[$prefmbox] : array();

        $ob = array(
            'by' => isset($entry['b']) ? $entry['b'] : $GLOBALS['prefs']->getValue('sortby'),
            'dir' => isset($entry['d']) ? $entry['d'] : $GLOBALS['prefs']->getValue('sortdir'),
            'limit' => false
        );

        /* Can't do threaded searches in search mailboxes. */
        if (!IMP::threadSortAvailable($mbox)) {
            if ($ob['by'] == SORTTHREAD) {
                $ob['by'] = SORTDATE;
            }
        }

        if (!empty($GLOBALS['conf']['server']['sort_limit'])) {
            require_once IMP_BASE . '/lib/IMAP/Cache.php';
            $imap_cache = &IMP_IMAP_Cache::singleton();
            $status = $imap_cache->getStatus(null, $mbox);
            if (!empty($status) &&
                $status->messages > $GLOBALS['conf']['server']['sort_limit']) {
                $ob['limit'] = true;
                $ob['by'] = SORTARRIVAL;
            }
        }

        if (!$ob['limit'] &&
            (($ob['by'] == SORTTO) || ($ob['by'] == SORTFROM))) {
            if (IMP::isSpecialFolder($mbox)) {
                /* If the preference is to sort by From Address, when we are
                   in the Drafts or Sent folders, sort by To Address. */
                if ($ob['by'] == SORTFROM) {
                    $ob['by'] = SORTTO;
                }
            } elseif ($ob['by'] == SORTTO) {
                $ob['by'] = SORTFROM;
            }
        }

        return $ob;
    }

    /**
     * Determines if thread sorting is available.
     *
     * @since IMP 4.2.1
     *
     * @param string $mbox  The mailbox to check.
     *
     * @return boolean  True if thread sort is available for this mailbox.
     */
    function threadSortAvailable($mbox)
    {
        return !$GLOBALS['imp_search']->isSearchMbox($mbox) &&
               (!$GLOBALS['prefs']->getValue('use_trash') ||
                !$GLOBALS['prefs']->getValue('use_vtrash') ||
                $GLOBALS['imp_search']->isVTrashFolder($mbox));
    }

    /**
     * Set the sorting preference for the current mailbox.
     * TODO: Purge non-existant search sorts (i.e. non VFolder entries).
     *
     * @since IMP 4.2
     *
     * @param integer $by      The sort type.
     * @param integer $dir     The sort direction.
     * @param string $mbox     The mailbox to use (defaults to current mailbox
     *                         in the session).
     * @param boolean $delete  Delete the entry?
     */
    function setSort($by = null, $dir = null, $mbox = null, $delete = false)
    {
        $entry = array();
        $sortpref = @unserialize($GLOBALS['prefs']->getValue('sortpref'));

        if ($mbox === null) {
            $mbox = $GLOBALS['imp_mbox']['mailbox'];
        }

        $prefmbox = ($GLOBALS['imp_search']->isSearchMbox()) ? $mbox : IMP::folderPref($mbox, false);

        if ($delete) {
            unset($sortpref[$prefmbox]);
        } else {
            if ($by !== null) {
                $entry['b'] = $by;
            }
            if ($dir !== null) {
                $entry['d'] = $dir;
            }

            if (!empty($entry)) {
                if (isset($sortpref[$prefmbox])) {
                    $sortpref[$prefmbox] = array_merge($sortpref[$prefmbox], $entry);
                } else {
                    $sortpref[$prefmbox] = $entry;
                }
            }
        }

        if ($delete || !empty($entry)) {
            $GLOBALS['prefs']->setValue('sortpref', @serialize($sortpref));
        }
    }

    /**
     * Add inline javascript to the output buffer.
     *
     * @since IMP 4.2
     *
     * @param mixed $script    The script text to add (can be stored in an
     *                         array also).
     * @param string $onload   Load the script after the page has loaded?
     *                         Either 'dom' (on dom:loaded), 'load'.
     */
    function addInlineScript($script, $onload = false)
    {
        if (is_array($script)) {
            $script = implode(';', $script);
        }

        $script = trim($script);
        if (empty($script)) {
            return;
        }

        switch ($onload) {
        case 'dom':
            $script = 'document.observe("dom:loaded", function() {' . $script . '});';
            break;

        case 'load':
            $script = 'Event.observe(window, "load", function() {' . $script . '});';
            break;
        }

        if (!isset($GLOBALS['__imp_inline_script'])) {
            $GLOBALS['__imp_inline_script'] = array();
        }
        $GLOBALS['__imp_inline_script'][] = $script;

        // If headers have already been sent, we need to output a
        // <script> tag directly.
        if (ob_get_length() || headers_sent()) {
            IMP::outputInlineScript();
        }
    }

    /**
     * Print pending inline javascript to the output buffer.
     *
     * @since IMP 4.2
     */
    function outputInlineScript()
    {
        if (!empty($GLOBALS['__imp_inline_script'])) {
            echo IMP::wrapInlineScript($GLOBALS['__imp_inline_script']);
        }

        $GLOBALS['__imp_inline_script'] = array();
    }

    /**
     * Print inline javascript to output buffer after wrapping with necessary
     * javascript tags.
     *
     * @since IMP 4.2
     *
     * @param array $script  The script to output.
     *
     * @return string  The script with the necessary HTML javascript tags
     *                 appended.
     */
    function wrapInlineScript($script)
    {
        return '<script type="text/javascript">//<![CDATA[' . "\n" . implode("\n", $script) . "\n//]]></script>\n";
    }

    /**
     * Is $mbox a 'special' folder (e.g. 'drafts' or 'sent-mail' folder)?
     *
     * @since IMP 4.2
     *
     * @param string $mbox  The mailbox to query.
     *
     * @return boolean  Is $mbox a 'special' folder?
     */
    function isSpecialFolder($mbox)
    {
        /* Get the identities. */
        require_once 'Horde/Identity.php';
        $identity = &Identity::singleton(array('imp', 'imp'));

        return (($mbox == IMP::folderPref($GLOBALS['prefs']->getValue('drafts_folder'), true)) || (in_array($mbox, $identity->getAllSentmailFolders())));
    }

    /**
     * Remove "bare newlines" from a string.
     *
     * @since IMP 4.2
     *
     * @param string $str  The original string.
     *
     * @return string  The string with all bare newlines removed.
     */
    function removeBareNewlines($str)
    {
        $str = preg_replace("|([^\r])\n|", "\\1\r\n", $str);
        return str_replace("\n\n", "\n\r\n", $str);
    }

    /**
     * Process mailbox/index information for current page load.
     *
     * @since IMP 4.2
     *
     * @return array  Array with the following elements:
     * <pre>
     * 'mailbox' - The current active mailbox (may be search mailbox).
     * 'thismailbox' - The real IMAP mailbox of the current index.
     * 'index' - The IMAP message index.
     * </pre>
     */
    function getCurrentMailboxInfo()
    {
        $ret = array();
        $ret['mailbox'] = Util::getFormData('mailbox', 'INBOX');
        $ret['thismailbox'] = Util::getFormData('thismailbox', $ret['mailbox']);
        $ret['index'] = Util::getFormData('index');
        return $ret;
    }

    /**
     * Returns the proper logout URL for logging out of IMP.
     *
     * @since IMP 4.2
     *
     * @return string  The logout URL.
     */
    function getLogoutUrl()
    {
        if ((Auth::getProvider() == 'imp') || IMP::canAutoLogin()) {
            return Horde::getServiceLink('logout', 'horde', true);
        } else {
            return Auth::addLogoutParameters($GLOBALS['registry']->get('webroot', 'imp') . '/login.php', AUTH_REASON_LOGOUT);
        }
    }

    /**
     * Output the javascript needed to call the popup_imp JS function.
     *
     * @since IMP 4.2
     *
     * @param string $url      The IMP page to load.
     * @param array $params    An array of paramters to pass to the URL.
     * @param integer $width   The width of the popup window.
     * @param integer $height  The height of the popup window.
     *
     * @return string  The javascript needed to call the popup code.
     */
    function popupIMPString($url, $params = array(), $width = 700,
                            $height = 650)
    {
        return "popup_imp('" . Horde::applicationUrl($url) . "'," . $width . "," . $height . ",'" . $GLOBALS['browser']->escapeJSCode(str_replace('+', '%20', substr(Util::addParameter('', $params, null, false), 1))) . "');";
    }

    /**
     * Output login message to use for Horde log.
     *
     * @since IMP 4.2
     *
     * @param string $status  Either 'login', 'logout', or 'failed'.
     *
     * @return string  The message string to use in the log.
     */
    function loginLogMessage($status)
    {
        $data = array();
        foreach (array('server', 'port', 'protocol', 'user') as $val) {
            $data[$val] = empty($_SESSION['imp'][$val]) ? '' : $_SESSION['imp'][$val];
        }

        switch ($status) {
        case 'login':
            $status_msg = 'Login success';
            break;

        case 'logout':
            $status_msg = 'Logout';
            break;

        case 'failed':
            $status_msg = 'FAILED LOGIN';
        }

        return sprintf($status_msg . ' for %s [%s]%s to {%s:%s [%s]}',
                       $data['user'],
                       $_SERVER['REMOTE_ADDR'],
                       (empty($_SERVER['HTTP_X_FORWARDED_FOR'])) ? '' : ' (forwarded for [' . $_SERVER['HTTP_X_FORWARDED_FOR'] . '])',
                       $data['server'],
                       $data['port'],
                       $data['protocol']);
    }

    /**
     * Determines if the tidy extension is available and is the correct
     * version.  Returns the config array.
     *
     * @since IMP 4.2
     *
     * @param integer $size  Size of the HTML data, in bytes.
     *
     * @return mixed  The config array, or false if tidy is not available.
     */
    function getTidyConfig($size)
    {
        if (Util::extensionExists('tidy') &&
            !function_exists('tidy_load_config') &&
            ($size < 250000)) {
            return array(
                'wrap' => 0,
                'indent' => true,
                'indent-spaces' => 4,
                'tab-size' => 4,
                'output-xhtml' => true,
                'enclose-block-text' => true,
                'hide-comments' => true,
                'numeric-entities' => true
            );
        }

        return false;
    }

    /**
     * Send response data to browser.
     *
     * @since IMP 4.2
     *
     * @param mixed $data  The data to serialize and send to the browser.
     * @param string $ct   The content-type to send the data with.  Either
     *                     'json', 'js-json', 'html', 'plain', and 'xml'.
     */
    function sendHTTPResponse($data, $ct)
    {
        // Output headers and encoded response.
        $charset = '; charset=' . NLS::getCharset();
        switch ($ct) {
        case 'json':
        case 'js-json':
            // JSON responses are a structured object which always
            // includes the response in a member named 'response', and an
            // additional array of messages in 'msgs' which may be updates
            // for the server or notification messages.
            require_once IMP_BASE . '/lib/JSON.php';
            $s_data = IMP_Serialize_JSON::encode($data);

            // Make sure no null bytes sneak into the JSON output stream.
            // Null bytes cause IE to stop reading from the input stream,
            // causing malformed JSON data and a failed request.  These
            // bytes don't seem to break any other browser, but might as
            // well remove them anyway.
            $s_data = str_replace("\00", '', $s_data);

            if ($ct == 'json') {
                header('Content-Type: text/x-json' . $charset);
                // Add prototype security delimiters to returned JSON.
                echo '/*-secure-' . $s_data . '*/';
            } else {
                header('Content-Type: text/html' . $charset);
                echo htmlspecialchars($s_data);
            }
            break;

        case 'html':
        case 'plain':
        case 'xml':
            header('Content-Type: text/' . $ct . $charset);
            echo $data;
            break;

        default:
            echo $data;
        }

        exit;
    }

    /**
     * Outputs the necessary script tags, honoring local configuration
     * choices as to script caching.
     *
     * @since IMP 4.2
     */
    function includeScriptFiles()
    {
        global $conf;

        $cache_type = @$conf['server']['cachejs'];

        if (empty($cache_type) ||
            $cache_type == 'none' ||
            ($cache_type == 'horde_cache' &&
             $conf['cache']['driver'] == 'none') ||
            !method_exists('Horde', 'listScriptFiles')) {
            Horde::includeScriptFiles();
            return;
        }

        $js_tocache = $js_force = array();
        $mtime = array(0);

        $s_list = Horde::listScriptFiles();
        foreach ($s_list as $app => $files) {
            foreach ($files as $file) {
                if ($file['d'] && ($file['f'][0] != '/')) {
                    $js_tocache[$file['p'] . $file['f']] = false;
                    $mtime[] = filemtime($file['p'] . $file['f']);
                } else {
                    if (!$file['d'] &&
                        ($app == 'dimp') &&
                        ($file['f'] == 'mailbox.js')) {
                        // Special dimp case: we keep mailbox.js in templates
                        // not for purposes of running PHP scripts in the
                        // file, but for ease of templating.  Thus, this file
                        // is OK to include inline.
                        $js_tocache[$file['p'] . $file['f']] = true;
                        $mtime[] = filemtime($file['p'] . $file['f']);
                    } else {
                        $js_force[] = $file['u'];
                    }
                }
            }
        }

        require_once IMP_BASE . '/lib/version.php';
        $sig = md5(serialize($s_list) . max($mtime) . IMP_VERSION);

        switch ($cache_type) {
        case 'filesystem':
            $js_filename = '/' . $sig . '.js';
            $js_path = $conf['server']['cachejsparams']['file_location'] . $js_filename;
            $js_url = $conf['server']['cachejsparams']['file_url'] . $js_filename;
            $exists = file_exists($js_path);
            break;

        case 'horde_cache':
            require_once 'Horde/Cache.php';
            $cache = &Horde_Cache::singleton($conf['cache']['driver'], Horde::getDriverConfig('cache', $conf['cache']['driver']));
            $exists = $cache->exists($sig, empty($conf['server']['cachejsparams']['lifetime']) ? 0 : $conf['server']['cachejsparams']['lifetime']);
            $js_url = IMP::getCacheURL('js', $sig);
            break;
        }

        if (!$exists) {
            $out = '';
            foreach ($js_tocache as $key => $val) {
                // Separate JS files with a newline since some compressors may
                // strip trailing terminators.
                if ($val) {
                    // Minify these files a bit by removing newlines and
                    // comments.
                    $out .= preg_replace(array('/\n+/', '/\/\*.*?\*\//'), array('', ''), file_get_contents($key)) . "\n";
                } else {
                    $out .= file_get_contents($key) . "\n";
                }
            }

            switch ($cache_type) {
            case 'filesystem':
                register_shutdown_function(array('IMP', '_filesystemGC'), 'js');
                IMP::filePutContents($js_path, $out);
                break;

            case 'horde_cache':
                $cache->set($sig, $out);
                break;
            }
        }

        foreach (array_merge(array($js_url), $js_force) as $val) {
            echo '<script type="text/javascript" src="' . $val . '"></script>' . "\n";
        }
    }

    /**
     * Creates a URL for cached DIMP data.
     *
     * @since IMP 4.2
     *
     * @param string $type  The cache type.
     * @param string $cid   The cache id.
     *
     * @return string  The URL to the cache page.
     */
    function getCacheURL($type, $cid)
    {
        $parts = array(
            $GLOBALS['registry']->get('webroot', 'imp'),
            'cache.php',
            $type,
            $cid
        );
        return Horde::url(implode('/', $parts));
    }

    /**
     * Outputs the necessary style tags, honoring local configuration
     * choices as to stylesheet caching.
     *
     * @since IMP 4.2
     *
     * @param boolean $print  Include print CSS?
     * @param string $app     The application to load ('dimp' or 'imp').
     */
    function includeStylesheetFiles($print = false, $app = 'imp')
    {
        global $conf, $prefs, $registry;

        $theme = $prefs->getValue('theme');
        $themesfs = $registry->get('themesfs', $app);
        $themesuri = $registry->get('themesuri', $app);
        $css = IMP::getStylesheets($app, $theme);
        $css_out = array();

        // Add print specific stylesheets.
        if ($print) {
            // Add Horde print stylesheet
            $tmp = array('u' => $registry->get('themesuri', 'horde') . '/print/screen.css',
                         'f' => $registry->get('themesfs', 'horde') . '/print/screen.css');
            if ($app == 'dimp') {
                $tmp['m'] = 'print';
                $css_out[] = $tmp;
                $css_out[] = array('u' => $themesuri . '/print.css',
                                   'f' => $themesfs . '/print.css',
                                   'm' => 'print');
            } else {
                $css_out[] = $tmp;
            }
            if (file_exists($themesfs . '/' . $theme . '/print.css')) {
                $tmp = array('u' => $themesuri . '/' . $theme . '/print.css',
                             'f' => $themesfs . '/' . $theme . '/print.css');
                if ($app == 'dimp') {
                    $tmp['m'] = 'print';
                }
                $css_out[] = $tmp;
            }
        }

        if ($app == 'dimp') {
            // Load custom stylesheets.
            if (!empty($conf['css_files'])) {
                foreach ($conf['css_files'] as $css_file) {
                    $css[] = array('u' => $themesuri . '/' . $css_file,
                                   'f' => $themesfs .  '/' . $css_file);
                }
            }
        }

        $cache_type = @$conf['server']['cachecss'];

        if (empty($cache_type) ||
            $cache_type == 'none' ||
            ($cache_type == 'horde_cache' &&
             $conf['cache']['driver'] == 'none')) {
            $css_out = array_merge($css, $css_out);
        } else {
            $mtime = array(0);
            $out = '';

            foreach ($css as $file) {
                $mtime[] = filemtime($file['f']);
            }

            require_once IMP_BASE . '/lib/version.php';
            $sig = md5(serialize($css) . max($mtime) . IMP_VERSION);

            switch ($cache_type) {
            case 'filesystem':
                $css_filename = '/' . $sig . '.css';
                $css_path = $conf['server']['cachecssparams']['file_location'] . $css_filename;
                $css_url = $conf['server']['cachecssparams']['file_url'] . $css_filename;
                $exists = file_exists($css_path);
                break;

            case 'horde_cache':
                require_once 'Horde/Cache.php';
                $cache = &Horde_Cache::singleton($GLOBALS['conf']['cache']['driver'], Horde::getDriverConfig('cache', $GLOBALS['conf']['cache']['driver']));
                $exists = $cache->exists($sig, empty($GLOBALS['conf']['server']['cachecssparams']['lifetime']) ? 0 : $GLOBALS['conf']['server']['cachecssparams']['lifetime']);
                $css_url = IMP::getCacheURL('css', $sig);
                break;
            }

            if (!$exists) {
                $flags = defined('FILE_IGNORE_NEW_LINES') ? (FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) : 0;
                foreach ($css as $file) {
                    $path = substr($file['u'], 0, strrpos($file['u'], '/') + 1);
                    // Fix relative URLs, remove multiple whitespaces, and
                    // strip comments.
                    $out .= preg_replace(array('/(url\(["\']?)([^\/])/i', '/\s+/', '/\/\*.*?\*\//'), array('$1' . $path . '$2', ' ', ''), implode('', file($file['f'], $flags)));
                }

                switch ($cache_type) {
                case 'filesystem':
                    register_shutdown_function(array('IMP', '_filesystemGC'), 'css');
                    IMP::filePutContents($css_path, $out);
                    break;

                case 'horde_cache':
                    $cache->set($sig, $out);
                    break;
                }
            }

            $css_out = array_merge(array(array('u' => $css_url)), $css_out);
        }

        foreach ($css_out as $file) {
            echo '<link href="' . $file['u'] . '" rel="stylesheet" type="text/css"' . (isset($file['m']) ? ' media="' . $file['m'] . '"' : '') . ' />' . "\n";
        }
    }

    /**
     * Return the list of base stylesheets to display.
     * TODO: Copied from Horde 3.2 for BC purposes.
     *
     * @since IMP 4.2
     *
     * @param string|array $app  The Horde application(s).
     * @param mixed $theme       The theme to use; specify an empty value to
     *                           retrieve the theme from user preferences, and
     *                           false for no theme.
     * @param boolean $inherit   Inherit Horde-wide CSS?
     *
     * @return array
     */
    function getStylesheets($apps = null, $theme = '', $inherit = true)
    {
        if ($theme === '' && isset($GLOBALS['prefs'])) {
            $theme = $GLOBALS['prefs']->getValue('theme');
        }

        $css = array();
        $rtl = isset($GLOBALS['nls']['rtl'][$GLOBALS['language']]);

        if (!is_array($apps)) {
            $apps = array($apps);
        }
        if ($inherit) {
            $key = array_search('horde', $apps);
            if ($key !== false) {
                unset($apps[$key]);
            }
            array_unshift($apps, 'horde');
        }

        /* Collect browser specific stylesheets if needed. */
        $browser_css = array();
        if ($GLOBALS['browser']->isBrowser('msie')) {
            $ie_major = $GLOBALS['browser']->getMajor();
            if ($ie_major >= 7) {
                if (($ie_major == 7) ||
                    // IE 8 uses IE 7 compatibility mode for dimp
                    in_array('dimp', $apps)) {
                    $browser_css[] = 'ie7.css';
                }
            } elseif ($ie_major < 7) {
                $browser_css[] = 'ie6_or_less.css';
                if ($GLOBALS['browser']->getPlatform() == 'mac') {
                    $browser_css[] = 'ie5mac.css';
                }
            }
        }
        if ($GLOBALS['browser']->isBrowser('opera')) {
            $browser_css[] = 'opera.css';
        }
        if ($GLOBALS['browser']->isBrowser('mozilla') &&
            $GLOBALS['browser']->getMajor() >= 5 &&
            preg_match('/rv:(.*)\)/', $GLOBALS['browser']->getAgentString(), $revision) &&
            $revision[1] <= 1.4) {
            $browser_css[] = 'moz14.css';
        }
        if (strpos(strtolower($GLOBALS['browser']->getAgentString()), 'safari') !== false) {
            $browser_css[] = 'safari.css';
        }

        foreach ($apps as $app) {
            $themes_fs = $GLOBALS['registry']->get('themesfs', $app);
            $themes_uri = Horde::url($GLOBALS['registry']->get('themesuri', $app), false, -1);
            $css[] = array('u' => $themes_uri . '/screen.css', 'f' => $themes_fs . '/screen.css');
            if (!empty($theme) &&
                file_exists($themes_fs . '/' . $theme . '/screen.css')) {
                $css[] = array('u' => $themes_uri . '/' . $theme . '/screen.css', 'f' => $themes_fs . '/' . $theme . '/screen.css');
            }

            if ($rtl) {
                $css[] = array('u' => $themes_uri . '/rtl.css', 'f' => $themes_fs . '/rtl.css');
                if (!empty($theme) &&
                    file_exists($themes_fs . '/' . $theme . '/rtl.css')) {
                    $css[] = array('u' => $themes_uri . '/' . $theme . '/rtl.css', 'f' => $themes_fs . '/' . $theme . '/rtl.css');
                }
            }
            foreach ($browser_css as $browser) {
                if (file_exists($themes_fs . '/' . $browser)) {
                    $css[] = array('u' => $themes_uri . '/' . $browser, 'f' => $themes_fs . '/' . $browser);
                }
                if (!empty($theme) &&
                    file_exists($themes_fs . '/' . $theme . '/' . $browser)) {
                    $css[] = array('u' => $themes_uri . '/' . $theme . '/' . $browser, 'f' => $themes_fs . '/' . $theme . '/' . $browser);
                }
            }
        }

        return $css;
    }

    /**
     * Wrapper to allow file_put_contents() use for PHP < 5.
     * TODO: Remove once PHP 5 is required.
     */
    function filePutContents($file, $data)
    {
        if (function_exists('file_put_contents')) {
            if (file_put_contents($file, $data) === false) {
                return false;
            }
        } elseif ($fd = fopen($file, 'w')) {
            $res = fwrite($fd, $data);
            fclose($fd);
            if ($res < strlen($data)) {
                return false;
            }
        } else {
            return false;
        }

        return true;
    }

    /**
     * Do garbage collection in the statically served file directory.
     *
     * @access private
     *
     * @param string $type  Either 'css' or 'js'.
     */
    function _filesystemGC($type)
    {
        static $dir_list = array();

        $ptr = $GLOBALS['conf']['server'][(($type == 'css') ? 'cachecssparams' : 'cachejsparams')];
        $dir = $ptr['file_location'];
        if (in_array($dir, $dir_list)) {
            return;
        }

        $c_time = time() - $ptr['lifetime'];
        $d = dir($dir);
        $dir_list[] = $dir;

        while (($entry = $d->read()) !== false) {
            $path = $dir . '/' . $entry;
            if (in_array($entry, array('.', '..'))) {
                continue;
            }

            if ($c_time > filemtime($path)) {
                $old_error = error_reporting(0);
                unlink($path);
                error_reporting($old_error);
            }
        }
        $d->close();
    }

    /**
     * Utility function to obtain PATH_INFO information.
     *
     * @since IMP 4.2
     * @todo Remove for Horde 4
     *
     * @return string  The PATH_INFO string.
     */
    function getPathInfo()
    {
        if (isset($_SERVER['PATH_INFO'])) {
            return $_SERVER['PATH_INFO'];
        } elseif (isset($_SERVER['REQUEST_URI']) &&
                  isset($_SERVER['SCRIPT_NAME'])) {
            $search = array($_SERVER['SCRIPT_NAME']);
            $replace = array('');
            if (!empty($_SERVER['QUERY_STRING'])) {
                $search[] = '?' . $_SERVER['QUERY_STRING'];
                $replace[] = '';
            }
            return str_replace($search, $replace, $_SERVER['REQUEST_URI']);
        }

        return '';
    }

    /**
     * Utility function to send redirect headers to browser, handling any
     * browser quirks.
     *
     * @since IMP 4.2
     * @todo Move to framework (Browser::?) for Horde 4
     *
     * @param string $url  The URL to redirect to.
     */
    function redirect($url)
    {
        if ($GLOBALS['browser']->isBrowser('msie') &&
            ($GLOBALS['conf']['use_ssl'] == 3) &&
            (strlen($url) < 160)) {
            header('Refresh: 0; URL=' . $url);
        } else {
            header('Location: ' . $url);
        }
        exit;
    }

}
