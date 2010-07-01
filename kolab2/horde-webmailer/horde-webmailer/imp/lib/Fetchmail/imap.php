<?php
/**
 * The IMP_Fetchmail_imap driver implements the IMAP_Fetchmail class for use
 * with IMAP/POP3 servers.
 *
 * $Horde: imp/lib/Fetchmail/imap.php,v 1.5.10.14 2009-01-06 15:24:05 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Nuno Loureiro <nuno@co.sapo.pt>
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package IMP
 */
class IMP_Fetchmail_imap extends IMP_Fetchmail {

    /**
     * The internal protocols list.
     *
     * @var array
     */
    var $_protocols;

    /**
     * The current protocol being used.
     *
     * @var string
     */
    var $_currprotocol;

    /**
     * The server string to use to connect to the remote mail server.
     *
     * @var string
     */
    var $_serverstring;

    /**
     * Returns a description of the driver.
     *
     * @see IMP_Fetchmail::description()
     */
    function description()
    {
        return _("IMAP/POP3 Mail Servers");
    }

    /**
     * Constructor.
     *
     * @param array $params  The configuration parameter array.
     */
    function IMP_Fetchmail_imap($params)
    {
        /* Set up the protocols array. */
        $this->_protocols = $this->_protocolList();

        parent::IMP_Fetchmail($params);
    }

    /**
     * Return a list of protocols supported by this driver.
     *
     * @see IMP_Fetchmail::getProtocolList()
     */
    function getProtocolList()
    {
        $output = array();
        foreach ($this->_protocols as $key => $val) {
            $output[$key] = $val['name'];
        }
        return $output;
    }

    /**
     * Returns the list of IMAP/POP3 protocols that this driver supports, and
     * associated configuration options.
     * This needs to be in a separate function because PHP will not allow
     * gettext strings to appear in member variables.
     *
     * @access private
     *
     * @return array  The protocol configuration list.
     */
    function _protocolList()
    {
        return array_merge(
            IMP_IMAP::protocolList(),
            array('pop3auto' => array(
                'name' => _("POP3 (Auto Detect Protocols)"),
                'auto' => array('pop3', 'pop3tls', 'pop3notls', 'pop3sslvalid', 'pop3ssl'),
                'base' => 'POP3')
            ),
            array('imapauto' => array(
                'name' => _("IMAP (Auto Detect Protocols)"),
                'auto' => array('imap', 'imaptls', 'imapnotls', 'imapsslvalid', 'imapssl'),
                'base' => 'IMAP')
            )
        );
    }

    /**
     * Checks if the remote mailbox exists.
     *
     * @access private
     *
     * @param resource $stream  A valid IMAP resource stream.
     *
     * @return boolean  Does the remote mailbox exist?
     */
    function _remoteMboxExists($stream)
    {
        if (empty($this->_params['rmailbox'])) {
            return false;
        }

        if ($this->_params['rmailbox'] == 'INBOX') {
            /* INBOX always exists and is a special case. */
            return true;
        }

        return (bool)@imap_list($stream, $this->_serverstring, $this->_params['rmailbox']);
    }

    /**
     * Attempts to connect to the mail server
     *
     * @access private
     *
     * @return mixed  Returns an IMAP Stream or PEAR_Error on failure.
     */
    function _connect()
    {
        /* Create the server string now. */
        $this->_serverstring = '{' . $this->_params['server'] . ':' . $this->_protocols[$this->_currprotocol]['port'] . '/'. $this->_protocols[$this->_currprotocol]['string'] . '}';
        $server_string = $this->_serverstring;

        if ($this->_protocols[$this->_currprotocol]['base'] == 'IMAP') {
            $server_string .= $this->_params['rmailbox'];
        }

        $stream = @imap_open($server_string, $this->_params['username'], $this->_params['password']);

        if ($stream === false) {
            $errstr = imap_last_error();
            if ($errstr) {
                return PEAR::raiseError(_("Cannot connect to the remote mail server: ") . $errstr);
            } else {
                return PEAR::raiseError(_("Cannot connect to the remote mail server."));
            }
        }

        return $stream;
    }

    /**
     * Gets the mailbody and calls the custom filter function.
     * Remove bare newlines and sets message color.
     *
     * @access private
     *
     * @param resource $stream  IMAP connection stream.
     * @param integer $uid      UID of message to fetch.
     *
     * @return string  Corrected mail content.
     */
    function _getMailMessage($stream, $uid)
    {
        /* Get the message headers. */
        $header = @imap_fetchheader($stream, $uid, FT_UID);

        /* Get the message body. */
        $body = @imap_body($stream, $uid, FT_UID | FT_PEEK);

        return parent::_processMailMessage($header, $body);
    }

    /**
     * Gets the mail using the data in this object.
     *
     * @see IMP_Fetchmail::getMail()
     */
    function getMail()
    {
        if (isset($this->_protocols[$this->_params['protocol']]['auto'])) {
            $protocols = $this->_protocols[$this->_params['protocol']]['auto'];
        } else {
            $protocols = array($this->_params['protocol']);
        }

        foreach ($protocols as $val) {
            $this->_currprotocol = $val;
            $ret = $this->_getMail();
            if (!is_a($ret, 'PEAR_Error')) {
                break;
            }
        }

        return $ret;
    }

    /**
     * Internal function used to get mail from a single server.
     *
     * @return mixed  Returns PEAR_Error on error, the number of messages
     *                fetched on success.
     */
    function _getMail()
    {
        $numMsgs = 0;
        $protocols = array();

        $stream = $this->_connect();
        if (is_a($stream, 'PEAR_Error')) {
            return $stream;
        }

        /* Check to see if remote mailbox exists. */
        $useimap = ($this->_protocols[$this->_currprotocol]['base'] == 'IMAP');
        if ($useimap) {
            if (!$this->_remoteMboxExists($stream)) {
                @imap_close($stream);
                return PEAR::raiseError(_("Invalid Remote Mailbox"));
            }
        }

        $msg_count = @imap_num_msg($stream);
        if (!$msg_count) {
            @imap_close($stream);
            return 0;
        }

        $overview = @imap_fetch_overview($stream, '1:' . $msg_count);
        foreach ($overview as $h) {
            if (($this->_params['onlynew'] &&
                 ($h->recent || !$h->seen) &&
                 !$h->deleted) ||
                (!$this->_params['onlynew'] && !$h->deleted)) {
                /* Check message size. */
                if (!$this->_checkMessageSize($h->size, isset($h->subject) ? $h->subject : '', $h->from)) {
                    continue;
                }

                /* Get the complete message. */
                $mail_source = $this->_getMailMessage($stream, $h->uid);

                /* Append to the server. */
                if ($this->_addMessage($mail_source)) {
                    $flags = array();
                    $numMsgs++;

                    /* Remove the mail if 'del' is set. */
                    if ($this->_params['del']) {
                        $flags[] = "\\Deleted";
                    }

                    /* Mark message seen if 'markseen' is set. */
                    if ($useimap && $this->_params['markseen']) {
                        $flags[] = "\\Seen";
                    }

                    if (!empty($flags)) {
                        @imap_setflag_full($stream, $h->uid, implode(' ', $flags), ST_UID);
                    }
                }
            }
        }

        /* Expunge all deleted messages now. */
        if ($this->_params['del']) {
            @imap_close($stream, CL_EXPUNGE);
        } else {
            @imap_close($stream);
        }

        return $numMsgs;
    }

}
