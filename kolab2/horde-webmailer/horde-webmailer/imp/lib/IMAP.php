<?php

/** Open the mailbox in read-write mode. */
define('IMP_IMAP_READWRITE', 0);

/** Open the IMAP connection without opening a mailbox. */
define('IMP_IMAP_PEEK', 1);

/** Open the mailbox in read-only mode. */
define('IMP_IMAP_READONLY', 2);

/** Open the mailbox in read-only mode, if it hasn't been opened yet. */
define('IMP_IMAP_AUTO', 4);

/**
 * The IMP_IMAP:: class facilitates connections to the IMAP/POP3 server via
 * the c-client PHP extensions.
 *
 * $Horde: imp/lib/IMAP.php,v 1.11.10.25 2009-03-19 10:28:16 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package IMP
 */
class IMP_IMAP {

    /**
     * The username for the server.
     *
     * @var string
     */
    var $_user;

    /**
     * The password for the mail server.
     *
     * @var string
     */
    var $_pass;

    /**
     * The current IMAP resource string.
     *
     * @var resource
     */
    var $_stream;

    /**
     * The currently open mailbox.
     *
     * @var string
     */
    var $_openMbox = null;

    /**
     * The IMAP flags set in the currently open mailbox.
     *
     * @var integer
     */
    var $_mboxFlags = null;

    /**
     * Parameters used in the last imap_open() call.
     *
     * @var array
     */
    var $_openparams = array();

    /**
     * Has the shutdown function been registered?
     *
     * @var boolean
     */
    var $_registered = false;

    /**
     * Attempts to return a reference to a concrete IMP_IMAP instance.
     * It will only create a new instance if no IMP_IMAP instance currently
     * exists.
     *
     * This method must be invoked as:
     *   $imp_imap = &IMP_IMAP::singleton();
     *
     * @return IMP_IMAP  The concrete IMP_IMAP reference, or false on error.
     */
    function &singleton($user = null, $pass = null)
    {
        static $instance;

        if (!isset($instance)) {
            $instance = new IMP_IMAP($user, $pass);
        }

        return $instance;
    }

    /**
     * Constructor.
     */
    function IMP_IMAP($user = null, $pass = null)
    {
        if (!is_null($user)) {
            $this->_user = $user;
            $this->_pass = $pass;
        } elseif (isset($_SESSION['imp'])) {
            $this->_user = $_SESSION['imp']['user'];
            $this->_pass = Secret::read(Secret::getKey('imp'), $_SESSION['imp']['pass']);
        }
    }

    /**
     * Open an IMAP stream.
     *
     * @param string $mbox    A mailbox to open.
     * @param integer $flags  Any IMP_IMAP_* flags.
     *
     * @return resource  The return from the imap_open() call.
     */
    function openIMAPStream($mbox = null, $flags = IMP_IMAP_READWRITE)
    {
        $i = -1;
        $ret = false;
        $this->_openparams = array();

        if ($_SESSION['imp']['base_protocol'] == 'pop3') {
            $mbox = 'INBOX';
            $flags = 0;
        } elseif (empty($mbox)) {
            $flags |= IMP_IMAP_PEEK;
        }
        $imap_flags = $this->_toIMAPFlags($flags);

        if (version_compare(PHP_VERSION, '5.2.1') != -1) {
            $ret = @imap_open(IMP::serverString($mbox), $this->_user, $this->_pass, $imap_flags, $_SESSION['imp']['login_tries']);
        } else {
            while (($ret === false) &&
                   !strstr(strtolower(imap_last_error()), 'login failure') &&
                   (++$i < $_SESSION['imp']['login_tries'])) {
                if ($i != 0) {
                    sleep(1);
                }
                $ret = @imap_open(IMP::serverString($mbox), $this->_user, $this->_pass, $imap_flags);
            }
        }

        if ($ret) {
            $this->_openparams = array('f' => $flags, 'm' => $mbox);
        }

        /* Catch c-client errors. */
        if (!$this->_registered) {
            register_shutdown_function(array(&$this, '_onShutdown'));
            $this->_registered = true;
        }

        return $ret;
    }

    /**
     * Perform needed activities on shutdown.
     */
    function _onShutdown()
    {
        $alerts = imap_alerts();
        if (!empty($alerts)) {
            Horde::logMessage('IMAP alerts: ' . implode(' ', $alerts), __FILE__, __LINE__, PEAR_LOG_DEBUG);
        }

        $errors = imap_errors();
        if (!empty($errors)) {
            Horde::logMessage('IMAP errors: ' . implode(' ', $errors), __FILE__, __LINE__, PEAR_LOG_DEBUG);
        }
    }

    /**
     * Change the currently active IMP IMAP stream to a new mailbox (if
     * necessary).
     *
     * @param string $mbox    The new mailbox.
     * @param integer $flags  Any IMP_IMAP_* flags.
     *
     * @return boolean  True on success, false on error.
     */
    function changeMbox($mbox, $flags = IMP_IMAP_READWRITE)
    {
        /* Open a connection if none exists. */
        if (empty($this->_stream)) {
            if (($this->_stream = $this->openIMAPStream($mbox, $flags))) {
                $this->_mboxFlags = $this->_openparams['f'];
                $this->_openMbox = $this->_openparams['m'];
                if (!empty($_SESSION['imp']['imap_server']['timeout'])) {
                    foreach ($_SESSION['imp']['imap_server']['timeout'] as $key => $val) {
                        imap_timeout($key, $val);
                    }
                }
                return true;
            } else {
                return false;
            }
        }

        if ($_SESSION['imp']['base_protocol'] == 'pop3') {
            return true;
        }

        /* Only reopen mailbox if we need to - either we are changing
         * mailboxes or the flags for the current mailbox have changed to an
         * incompatible value. */
        $flags_changed = false;
        if ($this->_mboxFlags != $flags) {
            if ($flags == IMP_IMAP_READWRITE &&
                ($this->_mboxFlags & OP_READONLY ||
                 $this->_mboxFlags & OP_HALFOPEN)) {
                $flags_changed = true;
                $flags = 0;
            } elseif ($flags & IMP_IMAP_READONLY &&
                      !($this->_mboxFlags & OP_READONLY)) {
                $flags_changed = true;
                $flags = OP_READONLY;
            } elseif ($flags & IMP_IMAP_AUTO &&
                      $this->_mboxFlags & OP_HALFOPEN) {
                $flags_changed = true;
                $flags = OP_READONLY;
            }
        }

        if (!$flags_changed) {
            $flags = $this->_toIMAPFlags($flags);
        }

        if ($this->_openMbox != $mbox || $flags_changed) {
            if (version_compare(PHP_VERSION, '5.2.1') != -1) {
                $result = @imap_reopen($this->_stream, IMP::serverString($mbox), $flags, $_SESSION['imp']['login_tries']);
            } else {
                $result = @imap_reopen($this->_stream, IMP::serverString($mbox), $flags);
            }

            if ($result) {
                $this->_openMbox = $mbox;
                $this->_mboxFlags = $flags;
                return true;
            } else {
                return false;
            }
        }

        return true;
    }

    /**
     * Returns the active IMAP resource string.
     *
     * @since IMP 4.2
     *
     * @return resource  The IMAP resource string.
     */
    function stream()
    {
        if (!$this->_stream) {
            $this->_stream = $this->openIMAPStream();
        }
        return $this->_stream;
    }

    /**
     * Returns the list of default IMAP/POP3 protocol connection information.
     * This function can be called statically.
     *
     * @return array  The protocol configuration list.
     */
    function protocolList()
    {
        return array(
            'pop3' => array(
                'name' => _("POP3"),
                'string' => 'pop3',
                'port' => 110,
                'base' => 'POP3'
            ),
            'pop3tls' => array(
                'name' => _("POP3 (self-signed certificate)"),
                'string' => 'pop3/novalidate-cert',
                'port' => 110,
                'base' => 'POP3'
            ),
            'pop3notls' => array(
                'name' => _("POP3, no TLS"),
                'string' => 'pop3/notls',
                'port' => 110,
                'base' => 'POP3'
            ),
            'pop3sslvalid' => array(
                'name' => _("POP3 over SSL"),
                'string' => 'pop3/ssl',
                'port' => 995,
                'base' => 'POP3'
            ),
            'pop3ssl' => array(
                'name' => _("POP3 over SSL (self-signed certificate)"),
                'string' => 'pop3/ssl/novalidate-cert',
                'port' => 995,
                'base' => 'POP3'
            ),
            'imap' => array(
                'name' => _("IMAP"),
                'string' => 'imap',
                'port' => 143,
                'base' => 'IMAP'
            ),
            'imaptls' => array(
                'name' => _("IMAP (self-signed certificate)"),
                'string' => 'imap/novalidate-cert',
                'port' => 143,
                'base' => 'IMAP'
            ),
            'imapnotls' => array(
                'name' => _("IMAP, no TLS"),
                'string' => 'imap/notls',
                'port' => 143,
                'base' => 'IMAP'
            ),
            'imapsslvalid' => array(
                'name' => _("IMAP over SSL"),
                'string' => 'imap/ssl',
                'port' => 993,
                'base' => 'IMAP'
            ),
            'imapssl' => array(
                'name' => _("IMAP over SSL (self-signed certificate)"),
                'string' => 'imap/ssl/novalidate-cert',
                'port' => 993,
                'base' => 'IMAP'
            )
        );
    }

    /**
     * Converts IMP_IMAP_* flags to imap_open() flags.
     *
     * @param integer $flags  Any IMP_IMAP_* flags.
     *
     * @return integer  A flag bitmask suitable for imap_open() and
     *                  imap_reopen().
     */
    function _toIMAPFlags($flags)
    {
        $imap_flags = 0;
        if ($flags & IMP_IMAP_PEEK) {
            $imap_flags |= OP_HALFOPEN;
        }
        if ($flags & IMP_IMAP_READONLY ||
            $flags & IMP_IMAP_AUTO) {
            $imap_flags |= OP_READONLY;
        }
        return $imap_flags;
    }

    /**
     * Reopens the IMAP connection.
     *
     * @since IMP 4.3.4
     */
    function reopen()
    {
        if (!empty($this->_stream)) {
            imap_reopen($this->_stream, IMP::serverString($this->_openMbox), $this->_mboxFlags);
        }
    }

}
