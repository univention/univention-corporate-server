<?php
/**
 * Functions required to start an IMP session.
 *
 * $Horde: imp/lib/Session.php,v 1.74.2.44 2009-05-29 22:36:50 slusarz Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jon Parise <jon@horde.org>
 * @package IMP
 */
class IMP_Session {

    /**
     * Take information posted from a login attempt and try setting up
     * an initial IMP session. Handle Horde authentication, if
     * required, and only do enough work to see if the user can log
     * in. This function should only be called once, when the user
     * first logs in. On success, logs a message to the Horde log.
     *
     * Creates the $imp session variable with the following entries:
     * '_logintasks'   -- Have the login tasks been completed?
     * 'acl'           -- See config/servers.php.
     * 'admin'         -- See config/servers.php.
     * 'base_protocol' -- Either 'imap' or 'pop3'.
     * 'cache'         -- Various IMP libraries can use this variable to cache
     *                    data.
     * 'default_view'  -- The default view (dimp, imp, or mimp).
     * 'file_upload'   -- If file uploads are allowed, the max size.
     * 'filteravail'   -- Can we apply filters manually?
     * 'imap_server'   -- IMAP server capabilities.
     * 'maildomain'    -- See config/servers.php.
     * 'mboxcache'     -- Used by the IMP_MailboxCache library.
     * 'namespace'     -- See config/servers.php.
     * 'notepadavail'  -- Is listing of notepads available?
     * 'pass'          -- The encrypted password.
     * 'port'          -- See config/servers.php.
     * 'protocol'      -- See config/servers.php.
     * 'quota'         -- See config/servers.php.
     * 'search'        -- Settings used by the IMP_Search library.
     * 'server'        -- The name of the server entry in config/servers.php.
     * 'smime'         -- Settings related to the S/MIME viewer.
     * 'smtphost'      -- The SMTP host to use instead of the Horde default.
     * 'smtpport'      -- The SMTP port to use instead of the Horde default.
     * 'showunsub'     -- Show unsusubscribed mailboxes on the folders screen.
     * 'tasklistavail' -- Is listing of tasklists available?
     * 'uniquser'      -- The unique user name.
     * 'user'          -- The IMAP username.
     * 'viewmode'      -- The imp view mode (currently dimp, imp, or mimp)
     *
     * @param string $imapuser  The username of the user.
     * @param string $password  The password of the user.
     * @param string $server    The server to use (see config/servers.php).
     * @param array $args       The necessary server information.
     *
     * @return boolean  True on success, false on failure.
     */
    function createSession($imapuser, $password, $server, $args = array())
    {
        global $conf, $registry;

        /* We need both a username and password. */
        if (!strlen($imapuser) || !strlen($password)) {
            return false;
        }

        /* Make sure all necessary parameters are set. */
        $default_args = array(
            'realm'        => '',
            'port'         => '',
            'protocol'     => '',
            'maildomain'   => '',
            'imap_server'  => array(),
        );

        /* Merge with the passed-in parameters. */
        $args = array_merge($default_args, $args);

        /* Create the $imp session variable. */
        $_SESSION['imp'] = array();
        $_SESSION['imp']['cache'] = array();
        $_SESSION['imp']['pass'] = Secret::write(Secret::getKey('imp'), $password);

        /* Set the logintasks flag. */
        IMP::loginTasksFlag(1);

        /* Run the username through virtualhost expansion functions if
         * necessary. */
        $_SESSION['imp']['user'] = $imapuser;
        if (!empty($conf['hooks']['vinfo'])) {
            $hook_user = Horde::callHook('_imp_hook_vinfo', array(), 'imp');
            if (!is_a($hook_user, 'PEAR_Error')) {
                $_SESSION['imp']['user'] = $hook_user;
            }
        }

        /* We might need to override some of the defaults with
         * environment-wide settings. Do NOT use the global $servers variable
         * as it may not exist. */
        if (is_callable(array('Horde', 'loadConfiguration'))) {
            $result = Horde::loadConfiguration('servers.php', array('servers'));
            if (!is_a($result, 'PEAR_Error')) {
                extract($result);
            }
        } else {
            require IMP_BASE . '/config/servers.php';
        }

        /* Determine the unique user name. */
        if (Auth::isAuthenticated()) {
            $_SESSION['imp']['uniquser'] = Auth::removeHook(Auth::getAuth());
        } else {
            $_SESSION['imp']['uniquser'] = $_SESSION['imp']['user'];

            if (($conf['server']['server_list'] != 'none') &&
                !empty($servers[$server]['realm'])) {
                $_SESSION['imp']['uniquser'] .= '@' . $servers[$server]['realm'];
            } elseif (!empty($args['realm'])) {
                $_SESSION['imp']['uniquser'] .= '@' . $args['realm'];
            }
        }

        if (($conf['server']['server_list'] != 'none') &&
            !empty($servers[$server]) &&
            is_array($servers[$server])) {
            $fields = array('server', 'protocol', 'port', 'maildomain',
                            'quota', 'acl');
            $fields_array = array('admin');
            $ptr = &$servers[$server];

            foreach ($fields as $val) {
                $_SESSION['imp'][$val] = isset($ptr[$val]) ? $ptr[$val] : null;
                /* 'admin' and 'quota' have password entries - encrypt these
                 * entries in the session if they exist. */
                if (isset($ptr[$val]['params']['password'])) {
                    $_SESSION['imp'][$val]['params']['password'] = Secret::write(Secret::getKey('imp'), $ptr[$val]['params']['password']);
                }
            }
            foreach ($fields_array as $val) {
                $_SESSION['imp'][$val] = isset($ptr[$val]) ? $ptr[$val] : array();
                /* 'admin' and 'quota' have password entries - encrypt these
                 * entries in the session if they exist. */
                if (isset($ptr[$val]['params']['password'])) {
                    $_SESSION['imp'][$val]['params']['password'] = Secret::write(Secret::getKey('imp'), $ptr[$val]['params']['password']);
                }
            }

            if ($conf['mailer']['type'] == 'smtp') {
                if (!empty($ptr['smtphost'])) {
                    $_SESSION['imp']['smtphost'] = $ptr['smtphost'];
                }
                if (!empty($ptr['smtpport'])) {
                    $_SESSION['imp']['smtpport'] = $ptr['smtpport'];
                }
            }
        } else {
            $server_key = IMP::getAutoLoginServer(true);
            $ptr = &$servers[$server_key];

            if (!empty($conf['server']['change_server'])) {
                $_SESSION['imp']['server'] = $server;
            } else {
                $_SESSION['imp']['server'] = $ptr['server'];

                foreach (array('acl', 'admin', 'quota') as $val) {
                    if (isset($ptr[$val])) {
                        $_SESSION['imp'][$val] = $ptr[$val];
                        /* 'admin' and 'quota' have password entries - encrypt
                         * these entries in the session if they exist. */
                        if (isset($ptr[$val]['params']['password'])) {
                            $_SESSION['imp'][$val]['params']['password'] = Secret::write(Secret::getKey('imp'), $ptr[$val]['params']['password']);
                        }
                    } else {
                        $_SESSION['imp'][$val] = false;
                    }
                }
            }

            foreach (array('port', 'protocol', 'smtphost', 'smtpport') as $param) {
                if (!empty($conf['server']['change_' . $param])) {
                    $_SESSION['imp'][$param] = isset($args[$param]) ? $args[$param] : null;
                } else {
                    $_SESSION['imp'][$param] = isset($ptr[$param]) ? $ptr[$param] : null;
                }
            }

            $_SESSION['imp']['maildomain'] = $args['maildomain'];
        }

        /* Determine the base protocol. */
        if (($pos = strpos($_SESSION['imp']['protocol'], '/'))) {
            $_SESSION['imp']['base_protocol'] = strtolower(substr($_SESSION['imp']['protocol'], 0, $pos));
        } else {
            $_SESSION['imp']['base_protocol'] = strtolower($_SESSION['imp']['protocol']);
        }

        /* Determine max login attempts. */
        if (empty($ptr['login_tries']) || ($ptr['login_tries'] < 1)) {
            $_SESSION['imp']['login_tries'] = 3;
        } else {
            $_SESSION['imp']['login_tries'] = $ptr['login_tries'];
        }

        /* Try to authenticate with the given information. */
        $auth_imp = &Auth::singleton(array('imp', 'imp'));
        if ($auth_imp->authenticate($_SESSION['imp']['uniquser'], array('password' => $password), true) !== true) {
            unset($_SESSION['imp']);
            return false;
        }

        /* Does the server allow file uploads? If yes, store the
         * value, in bytes, of the maximum file size. */
        $_SESSION['imp']['file_upload'] = Browser::allowFileUploads();

        /* Is the 'mail/canApplyFilters' API call available? */
        if ($registry->hasMethod('mail/canApplyFilters')) {
            $_SESSION['imp']['filteravail'] = $registry->call('mail/canApplyFilters');
        } else {
            $_SESSION['imp']['filteravail'] = false;
        }

        /* Is the 'tasks/listTasklists' call available? */
        $_SESSION['imp']['tasklistavail'] = ($conf['tasklist']['use_tasklist'] && $registry->hasMethod('tasks/listTasklists'));

        /* Is the 'notes/listNotepads' call available? */
        $_SESSION['imp']['notepadavail'] = ($conf['notepad']['use_notepad'] && $registry->hasMethod('notes/listNotepads'));

        /* IMAP specific variables. */
        if ($_SESSION['imp']['base_protocol'] != 'pop3') {
            /* Check for timeouts. */
            if (!empty($ptr['timeout'])) {
                $_SESSION['imp']['imap_server']['timeout'] = $ptr['timeout'];
            }

            /* Initialize the 'showunsub' value. */
            $_SESSION['imp']['showunsub'] = false;

            /* Check for manual configuration. */
            if (!empty($ptr['imap_config'])) {
                $_SESSION['imp']['namespace'] = $ptr['imap_config']['namespace'];
                $_SESSION['imp']['imap_server']['search_charset'] = $ptr['imap_config']['search_charset'];
            } else {
                require_once IMP_BASE . '/lib/IMAP/Client.php';
                $imapclient = new IMP_IMAPClient($_SESSION['imp']['server'], $_SESSION['imp']['port'], $_SESSION['imp']['protocol']);

                $_SESSION['imp']['namespace'] = array();

                $use_tls = $imapclient->useTLS();
                $user_namespace = (isset($ptr['namespace']) && is_array($ptr['namespace'])) ? $ptr['namespace'] : array();
                if (is_a($use_tls, 'PEAR_Error')) {
                    if (!empty($user_namespace)) {
                        $imp_imap = &IMP_IMAP::singleton();
                        $stream = $imp_imap->stream();
                        foreach ($ptr as $val) {
                            /* This is a correct TLS configuration - we only
                             * need to determine the delimiters for each
                             * namespace.  Get the default delimiter value
                             * (per RFC 3501 [6.3.8]). */
                            $box = @imap_getmailboxes($stream, IMP::serverString(), $val);
                            if (!empty($box[0]->delimiter)) {
                                $_SESSION['imp']['namespace'][$val] = array('name' => $val, 'delimiter' => $box[0]->delimiter);
                            }
                        }
                    } else {
                        $auth_imp->IMPsetAuthErrorMsg($use_tls->getMessage());
                        $auth_imp->clearAuth();
                        unset($_SESSION['imp']);
                        return false;
                    }
                } else {
                    /* Auto-detect namespace parameters from IMAP server. */
                    $res = $imapclient->login($_SESSION['imp']['uniquser'], $password);
                    if (is_a($res, 'PEAR_Error')) {
                        $auth_imp->IMPsetAuthErrorMsg($res->getMessage());
                        unset($_SESSION['imp']);
                        return false;
                    }
                    $_SESSION['imp']['namespace'] = $imapclient->getNamespace($user_namespace);
                    if (is_a($_SESSION['imp']['namespace'], 'PEAR_Error')) {
                        $auth_imp->IMPsetAuthErrorMsg(_("Could not retrieve namespace information from IMAP server."));
                        unset($_SESSION['imp']);
                        return false;
                    }

                    /* Determine if the search command supports the current
                     * browser's charset. */
                    $charset = NLS::getCharset();
                    $_SESSION['imp']['imap_server']['search_charset'] = array($charset => $imapclient->searchCharset($charset));
                }
            }
        } else {
            $_SESSION['imp']['namespace'] = null;
        }

        /* Set the maildomain. */
        if ($maildomain = $GLOBALS['prefs']->getValue('mail_domain')) {
            $_SESSION['imp']['maildomain'] = $maildomain;
        }

        /* Set up search information for the session. */
        $GLOBALS['imp_search']->sessionSetup();

        Horde::logMessage(IMP::loginLogMessage('login'), __FILE__, __LINE__, PEAR_LOG_NOTICE);

        return true;
    }

    /**
     * Perform IMP login tasks.
     */
    function loginTasks()
    {
        if (!IMP::loginTasksFlag()) {
            return;
        }

        IMP::loginTasksFlag(2);

        $imp_imap = &IMP_IMAP::singleton();
        if (!$imp_imap->stream()) {
            IMP::checkAuthentication(true);
        }

        /* Do maintenance operations. */
        if ($GLOBALS['prefs']->getValue('do_maintenance')) {
            require_once 'Horde/Maintenance.php';
            $maint = &Maintenance::factory('imp', array('last_maintenance' => $GLOBALS['prefs']->getValue('last_maintenance')));
            if (!$maint) {
                $GLOBALS['notification']->push(_("Could not execute maintenance operations."), 'horde.warning');
            } else {
                $maint->runMaintenance();
            }
        }

        /* If the user wants to run filters on login, make sure they get
           run. */
        if ($GLOBALS['prefs']->getValue('filter_on_login')) {
            /* Open the INBOX read-write. */
            $imp_imap->changeMbox('INBOX');

            /* Run filters. */
            require_once IMP_BASE . '/lib/Filter.php';
            $imp_filter = new IMP_Filter();
            $imp_filter->filter('INBOX');
        }

        IMP::loginTasksFlag(0);
    }

    /**
     * Returns the initial URL.
     *
     * @param string $actionID  The action ID to perform on the initial page.
     * @param boolean $encode   If true the argument separator gets encoded.
     *
     * @return string  The initial URL.
     */
    function getInitialUrl($actionID = null, $encode = true)
    {
        $init_url = ($_SESSION['imp']['base_protocol'] == 'pop3') ? 'INBOX' : $GLOBALS['prefs']->getValue('initial_page');

        require_once IMP_BASE . '/lib/Search.php';
        $imp_search = new IMP_Search();

        if (!$GLOBALS['prefs']->getValue('use_vinbox') &&
            $imp_search->isVINBOXFolder($init_url)) {
            $init_url = 'folders.php';
        } elseif (($imp_search->createSearchID($init_url) == $init_url) &&
                  !$imp_search->isVFolder($init_url)) {
            $init_url = 'INBOX';
            if (!$GLOBALS['prefs']->isLocked('initial_page')) {
                $GLOBALS['prefs']->setValue('initial_page', $init_url);
            }
        }

        if ($init_url == 'folders.php') {
            $url = Util::addParameter(Horde::applicationUrl($init_url, !$encode), array_merge(array('folders_token' => IMP::getRequestToken('imp.folders')), IMP::getComposeArgs()), null, $encode);
        } else {
            $url = Util::addParameter(Horde::applicationUrl('mailbox.php', !$encode), array_merge(array('mailbox' => $init_url, 'mailbox_token' => IMP::getRequestToken('imp.mailbox')), IMP::getComposeArgs()), null, $encode);
        }

        if (!empty($actionID)) {
            $url = Util::addParameter($url, 'actionID', $actionID, $encode);
        }

        return $url;
    }

}
