<?php
/**
 * The IMAP_Admin:: class allow managing of mailboxes on IMAP servers.
 *
 * Required parameters:<pre>
 *   'admin_user'      The name of a user with admin privileges.
 *   'admin_password'  The password of the adminstrator.</pre>
 *
 * Optional parameters:<pre>
 *   'hostspec'       The hostname or IP address of the server.
 *                    DEFAULT: 'localhost'
 *   'port'           The server port to which we will connect.
 *                    IMAP is generally 143, while IMAP-SSL is generally 993.
 *                    DEFAULT: 143
 *   'protocol'       The connection protocol (e.g. 'imap', 'pop3', 'nntp').
 *                    Protocol is one of 'imap/notls' (or only 'imap' if you
 *                    have a c-client version 2000c or older), 'imap/ssl',
 *                    or 'imap/ssl/novalidate-cert' (for a self-signed
 *                    certificate).
 *                    DEFAULT: 'imap'
 *   'userhierarchy'  The hierarchy where user mailboxes are stored.
 *                    DEFAULT: 'user.'
 *   'dsn'            The full IMAP connection string.
 *                    If not present, this is built from 'hostspec', 'port'
 *                    and 'protocol' parameters.</pre>
 *
 * $Horde: framework/IMAP/IMAP/Admin.php,v 1.5.6.13 2009-01-06 15:23:11 jan Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 3.0
 * @package Horde_IMAP
 */
class IMAP_Admin {

    /**
     * Parameter hash.
     *
     * @var array
     */
    var $_params;

    /**
     * IMAP resource.
     *
     * @var resource
     */
    var $_imap;

    /**
     * Constructor.
     *
     * @param array $params  A hash with all necessary parameters
     */
    function IMAP_Admin($params)
    {
        $default_params = array(
            'hostspec' => 'localhost',
            'port' => '143',
            'protocol' => 'imap',
            'userhierarchy' => 'user.'
        );
        $this->_params = array_merge($default_params, $params);

        /* Create DSN string. */
        if (!isset($this->_params['dsn'])) {
            $this->_params['dsn'] = sprintf('{%s:%d/%s}',
                                            $this->_params['hostspec'],
                                            $this->_params['port'],
                                            $this->_params['protocol']);
            $this->_ref = $this->_params['dsn'];
        } else {
            if (preg_match('/^{([^:]+):(\d+)\/([^}]+)}/', $this->_params['dsn'], $matches)) {
                $this->_params['hostspec'] = $matches[1];
                $this->_params['port'] = $matches[2];
                $this->_params['protocol'] = $matches[3];
                $this->_ref = sprintf('{%s:%d/%s}',
                                      $this->_params['hostspec'],
                                      $this->_params['port'],
                                      $this->_params['protocol']);
            }
        }
    }

    /**
     * Connects to the IMAP server with the parameters passed to the
     * constructor.
     *
     * @return resource|object  An IMAP resource or a PEAR_Error on failure
     */
    function _connect()
    {
        if (!isset($this->_imap)) {
            $this->_imap = @imap_open($this->_ref,
                                      $this->_params['admin_user'],
                                      $this->_params['admin_password'],
                                      OP_HALFOPEN);
            if (!$this->_imap) {
                $this->_imap = PEAR::raiseError(_("Authentication at IMAP server failed."), 'horde.error');
            }
        }
        return $this->_imap;
    }

    /**
     * Adds a mailbox.
     *
     * @param string $mailbox      The mailbox name to add.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function addMailbox($mailbox)
    {
        if (is_a($imap = $this->_connect(), 'PEAR_Error')) {
            return $imap;
        }
        if (!@imap_createmailbox($imap, $this->_ref . $this->_params['userhierarchy'] . $mailbox)) {
            return PEAR::raiseError(imap_last_error(), 'horde.warning');
        }

        return $this->_grantAdminPerms($mailbox);
    }

    /**
     * Grant the admin user all rights on the mailbox.
     *
     * @access private
     *
     * @param string $mailbox       the name of the mailbox on which we will
     *                              grant the permission
     * @return mixed True if successful, or PEAR_Error on failure
     */
    function _grantAdminPerms($mailbox)
    {
        require_once dirname(__FILE__) . '/ACL.php';

        $params = array('username' => $this->_params['admin_user'],
                        'password' => $this->_params['admin_password'],
                        'hostspec' => $this->_params['hostspec'],
                        'port' => $this->_params['port'],
                        'protocol' => $this->_params['protocol']);
        $acl = &IMAP_ACL::factory('rfc2086', $params);
        $result = $acl->createACL($this->_params['userhierarchy'] . $mailbox,
                                  $this->_params['admin_user'],
                                  array('l' => true,
                                        'r' => true,
                                        's' => true,
                                        'w' => true,
                                        'i' => true,
                                        'p' => true,
                                        'c' => true,
                                        'd' => true,
                                        'a' => true));
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        return true;
    }

    /**
     * Deletes a mailbox.
     *
     * @param string $mailbox  The mailbox to delete.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function removeMailbox($mailbox)
    {
        if (is_a($imap = $this->_connect(), 'PEAR_Error')) {
            return $imap;
        }

        $this->_grantAdminPerms($mailbox);
        if (!@imap_deletemailbox($imap, $this->_ref . $this->_params['userhierarchy'] . $mailbox)) {
            return PEAR::raiseError(imap_last_error(), 'horde.warning');
        }
        return true;
    }

    /**
     * List all mailboxes.
     *
     * Note that this does not work on a virtual-domain enabled Cyrus (it will
     * only return mailboxes in the default domain).
     *
     * @return mixed  The array of mailboxes, or a PEAR_Error object on failure.
     */
    function listMailboxes()
    {
        if (is_a($imap = $this->_connect(), 'PEAR_Error')) {
            return $imap;
        }

        $list = @imap_list($imap, $this->_ref, $this->_params['userhierarchy'] . '%');
        if (!$list) {
            return array();
        }
        return preg_replace('/.*' . preg_quote($this->_params['userhierarchy'], '/') . '(.*)/', '\\1', $list);
    }

    /**
     * Check whether a mailbox exists.
     *
     * @param string $mailbox   The mailbox to check.
     * @return mixed  True if mailbox exists, false if not, or a PEAR_Error.
     */
    function mailboxExists($mailbox)
    {
        if (is_a($imap = $this->_connect(), 'PEAR_Error')) {
            return $imap;
        }

        $list = @imap_list($imap, $this->_ref, $this->_params['userhierarchy'] . $mailbox);
        if ($list === false) {
            return false;
        }
        return count($list) > 0;
    }

}
