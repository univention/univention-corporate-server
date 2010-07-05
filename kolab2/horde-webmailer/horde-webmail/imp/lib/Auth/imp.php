<?php
/**
 * The Auth_imp:: class provides an IMP implementation of the Horde
 * authentication system.
 *
 * Required parameters:<pre>
 *   None.</pre>
 *
 * Optional parameters:<pre>
 *   None.</pre>
 *
 * $Horde: imp/lib/Auth/imp.php,v 1.16.6.21 2009-01-06 15:24:05 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @since   Horde 3.0
 * @package Horde_Auth
 */
class Auth_imp extends Auth {

    /**
     * Constructs a new IMP authentication object.
     *
     * @param array $params  A hash containing connection parameters.
     */
    function Auth_imp($params = array())
    {
        if (!Util::extensionExists('imap')) {
            Horde::fatal(PEAR::raiseError(_("Auth_imp: Required IMAP extension not found.")), __FILE__, __LINE__);
        }
    }

    /**
     * Find out if a set of login credentials are valid, and if
     * requested, mark the user as logged in in the current session.
     *
     * @param string $userID      The userID to check.
     * @param array $credentials  The credentials to check.
     * @param boolean $login      Whether to log the user in. If false, we'll
     *                            only test the credentials and won't modify
     *                            the current session.
     *
     * @return boolean  Whether or not the credentials are valid.
     */
    function authenticate($userID = null, $credentials = array(),
                          $login = false)
    {
        // Check for for hordeauth.
        if (empty($_SESSION['imp']['uniquser']) &&
            IMP::canAutoLogin()) {
            $server_key = IMP::getAutoLoginServer();

            if (is_callable(array('Horde', 'loadConfiguration'))) {
                $result = Horde::loadConfiguration('servers.php', array('servers'));
                if (!is_a($result, 'PEAR_Error')) {
                    extract($result);
                }
            } else {
                require IMP_BASE . '/config/servers.php';
            }

            $ptr = &$servers[$server_key];
            if (isset($ptr['hordeauth'])) {
                $imapuser = (strcasecmp($ptr['hordeauth'], 'full') == 0)
                    ? Auth::getAuth()
                    : Auth::getBareAuth();
                    $pass = Auth::getCredential('password');

                // Need to make sure we are in the IMP scope if trying to do
                // hordeauth (we can reach this method from MIMP or DIMP).
                if ($GLOBALS['registry']->call('mail/authenticate', array($imapuser, array('password' => $pass), $ptr))) {
                    return true;
                }
            }
        }

        if (empty($userID)) {
            if (empty($_SESSION['imp']['uniquser'])) {
                return false;
            }
            $userID = $_SESSION['imp']['uniquser'];
        }

        if (empty($credentials)) {
            if (empty($_SESSION['imp']['pass'])) {
                return false;
            }
            $credentials = array('password' => Secret::read(Secret::getKey('imp'), $_SESSION['imp']['pass']));
        }

        $login = ($login &&
                  (($this->getProvider() == 'imp') || IMP::recomposeLogin()));

        return parent::authenticate($userID, $credentials, $login);
    }

    /**
     * Find out if a set of login credentials are valid.
     *
     * @access private
     *
     * @param string $userID      The userID to check.
     * @param array $credentials  An array of login credentials.
     *
     * @return boolean  Whether or not the credentials are valid.
     */
    function _authenticate($userID, $credentials)
    {
        global $prefs;

        if (!(isset($_SESSION['imp']) && is_array($_SESSION['imp']))) {
            if (isset($prefs)) {
                $prefs->cleanup(true);
            }
            $this->_setAuthError(AUTH_REASON_SESSION);
            return false;
        }

        switch ($_SESSION['imp']['base_protocol']) {
        case 'pop3':
            /* Turn some options off if we are working with POP3. */
            $GLOBALS['conf']['user']['allow_folders'] = false;
            $prefs->setValue('save_sent_mail', false);
            $prefs->setLocked('save_sent_mail', true);
            $prefs->setLocked('sent_mail_folder', true);
            $prefs->setLocked('drafts_folder', true);
            $prefs->setLocked('trash_folder', true);
            break;
        }

        /* Open an IMAP stream. */
        require_once IMP_BASE . '/lib/IMAP.php';
        $imp_imap = &IMP_IMAP::singleton($_SESSION['imp']['uniquser'], $credentials['password']);
        if (!$imp_imap->changeMbox(null, IMP_IMAP_PEEK)) {
            Horde::logMessage(IMP::loginLogMessage('failed'), __FILE__, __LINE__, PEAR_LOG_ERR);

            unset($_SESSION['imp']);
            if (isset($prefs)) {
                $prefs->cleanup(true);
            }
            $this->_setAuthError(AUTH_REASON_BADLOGIN);
            return false;
        }

        return true;
    }

    /**
     * Somewhat of a hack to allow IMP to set an authentication error message
     * that may occur outside of this file.
     *
     * @param string $msg  The error message to set.
     */
    function IMPsetAuthErrorMsg($msg)
    {
        $this->_setAuthError(AUTH_REASON_MESSAGE, $msg);
    }

}
