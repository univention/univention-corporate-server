<?php
/**
 * The IMAP_Admin:: class allow managing of mailboxes on IMAP servers.
 *
 * <pre>
 * Required parameters:
 * ====================
 *  'admin_user'      --  The name of a user with admin privileges.
 *  'admin_password'  --  The password of the adminstrator.
 *
 * Optional parameters:
 * ====================
 *  'hostspec'       --  The hostname or IP address of the server.
 *                       DEFAULT: 'localhost'
 *  'port'           --  The server port to which we will connect.
 *                       IMAP is generally 143, while IMAP-SSL is generally 993.
 *                       DEFAULT: 143
 *  'protocol'       --  The connection protocol (e.g. 'imap', 'pop3', 'nntp').
 *                       Protocol is one of 'imap/notls' (or only 'imap' if you
 *                       have a c-client version 2000c or older), 'imap/ssl',
 *                       or 'imap/ssl/novalidate-cert' (for a self-signed
 *                       certificate).
 *                       DEFAULT: 'imap'
 *  'userhierarchy'  --  The hierarchy where user mailboxes are stored.
 *                       DEFAULT: 'user.'
 *  'dsn'            --  The full IMAP connection string.
 *                       If not present, this is built from 'hostspec', 'port'
 *                       and 'protocol' parameters.
 * </pre>
 *
 * $Horde: framework/IMAP/IMAP/Admin.php,v 1.3 2004/04/17 14:24:13 jan Exp $
 *
 * Copyright 2004 Jan Schneider <jan@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_IMAP
 */
class IMAP_Admin {

    /**
     * Parameter hash.
     *
     * @var array $_params
     */
    var $_params;

    /**
     * IMAP resource.
     *
     * @var resource $_imap
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
            if (!empty($this->_params['folder'])) {
                $this->_params['dsn'] .= $this->_params['folder'];
            }
        } else {
            $this->_ref = substr($this->_params['dsn'], 0, strpos($this->_params['dsn'], '}') + 1);
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
                $this->_imap = PEAR::raiseError(imap_last_error(), 'horde.error');
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
        require_once dirname(__FILE__) . '/ACL.php';

        if (is_a($imap = $this->_connect(), 'PEAR_Error')) {
            return $imap;
        }
        if (!@imap_createmailbox($imap, $this->_ref . $this->_params['userhierarchy'] . $mailbox)) {
            return PEAR::raiseError(imap_last_error(), 'horde.warning');
        }

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
        if (!@imap_deletemailbox($imap, $this->_ref . $this->_params['userhierarchy'] . $mailbox)) {
            return PEAR::raiseError(imap_last_error(), 'horde.warning');
        }
        return true;
    }

    /**
     * List all mailboxes.
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
        $list = preg_replace('/.*' . $this->_params['userhierarchy'] . '(.*)/', '\\1', $list);
        return $list;
    }
}
