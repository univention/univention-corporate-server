<?php

/**
 * The Kolab implementation of the Horde authentication system. Derives from the
 * Auth_imap IMAP authentication object, and provides parameters to it based on
 * the global Kolab configuration.
 *
 * $Horde: framework/Auth/Auth/kolab.php,v 1.1.10.21 2009-01-06 15:22:49 jan Exp $
 *
 * Copyright 2004-2007 Stuart Binge <s.binge@codefusion.co.za>
 * Copyright 2008-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://opensource.org/licenses/lgpl-license.php.
 *
 * @author  Stuart Binge <s.binge@codefusion.co.za>
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @since   Horde 1.3
 * @package Horde_Auth
 */
class Auth_kolab extends Auth {

    /**
     * An array of capabilities, so that the driver can report which
     * operations it supports and which it doesn't.
     *
     * @var array
     */
    var $capabilities = array('add'           => true,
                              'update'        => false,
                              'resetpassword' => false,
                              'remove'        => false,
                              'list'          => true,
                              'transparent'   => false);
    /**
     * Find out if a set of login credentials are valid.
     *
     * For Kolab this requires to identify the IMAP server the user should
     * be authenticated against before the credentials can be checked using
     * this server. The Kolab_Server module handles identification of the
     * correct IMAP server.
     *
     * @access private
     *
     * @param string $userId      The userId to check.
     * @param array $credentials  An array of login credentials. For Kolab,
     *                            this must contain a "password" entry.
     *
     * @return boolean  Whether or not the credentials are valid.
     */
    function _authenticate($userId, $credentials)
    {
        global $conf;

        $params = array();

        @include_once 'Horde/Kolab/Session.php';

        if (class_exists('Horde_Kolab_Session')) {
            $session = &Horde_Kolab_Session::singleton($userId, $credentials, true);
            if (is_a($session->auth, 'PEAR_Error')) {
                $this->_setAuthError(AUTH_REASON_MESSAGE, $session->auth->getMessage());
            }
        } else {
            $this->_setAuthError(AUTH_REASON_MESSAGE,
                                 'The class Horde_Kolab_Session is required for the Kolab auth driver but it is missing!');
            return false;
        }

        if (!isset($conf['auth']['params']) || $conf['auth']['params']['login_block'] != 1) {
            // Return if feature is disabled.
            return $session->auth;
        }

        @include_once 'Horde/History.php';

        if ($session->auth !== true && class_exists('Horde_History')) {
            $history = &Horde_History::singleton();

            $history_identifier = "$userId@logins.kolab";
            $history_log = $history->getHistory($history_identifier);
            $history_list = array();

            // Extract history list from log.
            if ($history_log && !is_a($history_log, 'PEAR_Error')) {
                $data = $history_log->getData();
                if (!empty($data)) {
                    $entry = array_shift($data);
                    $history_list = $entry['history_list'];
                }
            }

            // Calculate the time range.
            $start_time = (time() - $conf['auth']['params']['login_block_time'] * 60);

            $new_history_list = array();
            $count = 0;

            // Copy and count all relevant timestamps.
            foreach ($history_list as $entry) {
                $timestamp = $entry[ 'timestamp' ];

                if ($timestamp > $start_time) {
                    $new_history_list[] = $entry;
                    $count++;
                }
            }

            $max_count = $conf['auth']['params']['login_block_count'];

            if ($count > $max_count) {
                // Add entry for current failed login.
                $entry = array();
                $entry[ 'timestamp' ] = time();
                $new_history_list[] = $entry;

                // Write back history.
                $history->log($history_identifier,
                              array('action' => 'add', 'who' => $userId,
                                    'history_list' => $new_history_list), true);

                if ($count > $max_count) {
                    $this->_setAuthError(AUTH_REASON_MESSAGE,
                                         _("Too many invalid logins during the last minutes."));
                } else {
                    $this->_setAuthError(AUTH_REASON_BADLOGIN);
                }

                return false;
            }
        }

        return $session->auth === true;
    }

    /**
     * Sets a variable in the session saying that authorization has succeeded,
     * note which userId was authorized, and note when the login took place.
     *
     * The kolab driver rewrites UIDs into the correct mail addresses that
     * need to be used to log into the IMAP server.
     *
     * @param string $userId            The userId who has been authorized.
     * @param array $credentials        The credentials of the user.
     * @param string $realm             The authentication realm to use.
     * @param boolean $changeRequested  Whether to request that the user change
     *                                  their password.
     */
    function setAuth($userId, $credentials, $realm = null, $changeRequested = false)
    {
        @include_once 'Horde/Kolab/Session.php';

        if (class_exists('Horde_Kolab_Session')) {
            $session = &Horde_Kolab_Session::singleton($userId);
            $userId = $session->user_mail;
        }

        return parent::setAuth($userId, $credentials, $realm, $changeRequested);
    }

    /**
     * List Users
     *
     * @return array  List of Users
     */
    function listUsers()
    {
        @include_once 'Horde/Kolab/Session.php';

        if (class_exists('Horde_Kolab_Session')) {
            $session = &Horde_Kolab_Session::singleton();
            $server = $session->getServer();
            if (is_a($server, 'PEAR_Error')) {
                return $server;
            }
            $users = $server->listObjects(KOLAB_OBJECT_USER);
            $mails = array();
            foreach ($users as $user) {
                $mails[] = $user->get(KOLAB_ATTR_MAIL);
            }
            return $mails;
        } else {
            return PEAR::raiseError("The class \"Horde_Kolab_Session\" is not available.");
        }
    }

    /**
     * Add a set of authentication credentials.
     *
     * @param string $userId      The userId to add.
     * @param array $credentials  The credentials to be set.
     *
     * @return boolean|PEAR_Error  True on success.
     */
    function addUser($userId, $credentials)
    {
        @include_once 'Horde/Kolab/Session.php';

        if (class_exists('Horde_Kolab_Session')) {
            $session = &Horde_Kolab_Session::singleton();
            $server = $session->getServer();
            if (is_a($server, 'PEAR_Error')) {
                return $server;
            }
            $result = $server->store(KOLAB_OBJECT_USER, $userId, $credentials);
            if (is_a($result, KOLAB_OBJECT_USER)) {
                return true;
            } else if (is_a($result, 'PEAR_Error')) {
                return $result;
            } else {
                return PEAR::raiseError(sprintf('The new Kolab object is a %s rather than a ' . KOLAB_OBJECT_USER,
                                                get_class($result)));
            }
        } else {
            return PEAR::raiseError("The class \"Horde_Kolab_Session\" is not available.");
        }
    }
}
