<?php

require_once HORDE_BASE . '/lib/version.php';

/** @constant HORDE_AGENT_HEADER The description of Horde to use in the 'User-Agent:' header. */
define('HORDE_AGENT_HEADER', 'Horde Application Framework ' . HORDE_VERSION);

/**
 * The MIME_Headers:: class contains generic functions related to
 * handling the headers of mail messages.
 *
 * $Horde: framework/MIME/MIME/Headers.php,v 1.20 2004/04/14 16:59:33 slusarz Exp $
 *
 * Copyright 2002-2004 Michael Slusarz <slusarz@bigworm.colorado.edu>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Slusarz <slusarz@bigworm.colorado.edu>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_MIME
 */
class MIME_Headers {

    /**
     * The internal headers array.
     *
     * @var array $_headers
     */
    var $_headers = array();

    /**
     * Cached output of the MIME_Structure::parseMIMEHeaders() command.
     *
     * @var array $_allHeaders
     */
    var $_allHeaders;

    /**
     * Cached output of the imap_fetchheader() command.
     *
     * @var string $_headerText
     */
    var $_headerText;

    /**
     * The header object returned from imap_headerinfo().
     *
     * @var stdClass $_headerObject
     */
    var $_headerObject;

    /**
     * The internal flags array.
     *
     * @var array $_flags
     */
    var $_flags = array();

    /**
     * The User-Agent string to use.
     * THIS VALUE SHOULD BE OVERRIDEN BY ALL SUBCLASSES.
     *
     * @var string $_agent
     */
    var $_agent = HORDE_AGENT_HEADER;

    /**
     * The sequence to use as EOL for the headers.
     * The default is currently to output the EOL sequence internally as
     * just "\n" instead of the canonical "\r\n" required in RFC 822 & 2045.
     * To be RFC complaint, the full <CR><LF> EOL combination should be used
     * when sending a message.
     *
     * @var string $_eol
     */
    var $_eol = "\n";

    /**
     * The index of the message.
     *
     * @var integer $_index
     */
    var $_index;

    /**
     * Constructor.
     *
     * @access public
     *
     * @param optional integer $index  The message index to parse headers.
     */
    function MIME_Headers($index = null)
    {
        $this->_index = $index;
    }

    /**
     * Returns a reference to a currently open IMAP stream.
     * THIS VALUE SHOULD BE OVERRIDEN BY ALL SUBCLASSES.
     *
     * @return resource  An IMAP resource stream.
     */
    function &_getStream()
    {
        return false;
    }

    /**
     * Return the full list of headers from the imap_fetchheader() function.
     *
     * @access public
     *
     * @return string  See imap_fetchheader().
     */
    function getHeaderText()
    {
        if (!is_null($this->_index) && empty($this->_headerText)) {
            $this->_headerText = @imap_fetchheader($this->_getStream(), $this->_index, FT_UID);
        }

        return $this->_headerText;
    }

    /**
     * Return the full list of headers.
     *
     * @access public
     *
     * @param optional boolean $decode  Decode the headers?
     *
     * @return array  See MIME_Structure::parseMIMEHeaders().
     */
    function getAllHeaders($decode = true)
    {
        require_once 'Horde/MIME/Structure.php';

        if (!is_null($this->_index) && empty($this->_allHeaders)) {
            $this->_allHeaders = MIME_Structure::parseMIMEHeaders($this->getHeaderText(), $decode);
        }

        return $this->_allHeaders;
    }

    /**
     * Return the header object from imap_headerinfo().
     *
     * @access public
     *
     * @return object stdClass  See imap_headerinfo().
     */
    function getHeaderObject()
    {
        if (!is_null($this->_index) && empty($this->_headerObject)) {
            $stream = &$this->_getStream();
            $this->_headerObject = @imap_headerinfo($stream, @imap_msgno($stream, $this->_index));
        }

        return $this->_headerObject;
    }

    /**
     * Build the header array. The headers are MIME decoded.
     *
     * @access public
     */
    function buildHeaders()
    {
        if (!empty($this->_headers)) {
            return;
        }

        /* Parse through the list of all headers. */
        foreach ($this->getAllHeaders() as $key => $val) {
            $this->addHeader($key, $val);
        }
    }

    /**
     * Build the flags array.
     *
     * @access public
     */
    function buildFlags()
    {
        if (!empty($this->_flags)) {
            return;
        }

        /* Get the IMAP header object. */
        $ob = $this->getHeaderObject();
        if (!isset($ob)) {
            return;
        }

        /* Unseen flag */
        if (($ob->Unseen == 'U') || ($ob->Recent == 'N')) {
            $this->_flags['unseen'] = true;
        }

        /* Recent flag */
        if (($ob->Recent == 'N') || ($ob->Recent == 'R')) {
            $this->_flags['recent'] = true;
        }

        /* Answered flag */
        if ($ob->Answered == 'A') {
            $this->_flags['answered'] = true;
        }

        /* Draft flag */
        if (isset($ob->Draft) && ($ob->Draft == 'X')) {
            $this->_flags['draft'] = true;
        }

        /* Important flag */
        if ($ob->Flagged == 'F') {
            $this->_flags['important'] = true;
        }

        /* Deleted flag */
        if ($ob->Deleted == 'D') {
            $this->_flags['deleted'] = true;
        }
    }

    /**
     * Returns the internal header array in array format.
     *
     * @access public
     *
     * @return array  The headers in array format.
     */
    function toArray()
    {
        $return_array = array();

        foreach ($this->_headers as $ob) {
            $eol = $this->getEOL();
            $header = $ob['header'];
            if (is_array($ob['value'])) {
                require_once dirname(__FILE__) . '/../MIME.php';
                $return_array[$header] = MIME::wrapHeaders($header, reset($ob['value']));
                next($ob['value']);
                while (list(,$val) = each($ob['value'])) {
                    $return_array[$header] .= $eol . $header . ': ' . MIME::wrapHeaders($header, $val, $eol);
                }
            } else {
                $return_array[$header] = $ob['value'];
            }
        }

        return $return_array;
    }

    /**
     * Returns the internal header array in string format.
     *
     * @access public
     *
     * @return string  The headers in string format.
     */
    function toString()
    {
        $eol = $this->getEOL();
        $text = '';

        foreach ($this->_headers as $ob) {
            if (!is_array($ob['value'])) {
                $ob['value'] = array($ob['value']);
            }
            foreach ($ob['value'] as $entry) {
                $text .= $ob['header'] . ': ' . $entry . $eol;
            }
        }

        return $text . $eol;
    }

    /**
     * Generate the 'Received' header for the Web browser->Horde hop
     * (attempts to conform to guidelines in RFC 2821).
     *
     * @access public
     */
    function addReceivedHeader()
    {
        if (isset($_SERVER['HTTP_X_FORWARDED_FOR'])) {
            /* This indicates the user is connecting through a proxy. */
            $remote_path = explode(',', $_SERVER['HTTP_X_FORWARDED_FOR']);
            $remote_addr = $remote_path[0];
            $remote = gethostbyaddr($remote_addr);
        } else {
            $remote_addr = $_SERVER['REMOTE_ADDR'];
            if (empty($_SERVER['REMOTE_HOST'])) {
                $remote = gethostbyaddr($remote_addr);
            } else {
                $remote = $_SERVER['REMOTE_HOST'];
            }
        }
        $received = 'from ' . $remote . ' (';

        if (!empty($_SERVER['REMOTE_IDENT'])) {
            $received .= $_SERVER['REMOTE_IDENT'] . '@' . $remote . ' ';
        } elseif ($remote != $_SERVER['REMOTE_ADDR']) {
            $received .= $remote . ' ';
        }
        $received .= '[' . $remote_addr . ']) ';
        $received .= 'by ' . $GLOBALS['conf']['server']['name'] . ' (Horde) with HTTP ';

        $user = Auth::getAuth();
        if (strpos($user, '@') === false) {
            $user .= '@' . $GLOBALS['conf']['server']['name'];
        }
        $received .= 'for <' . $user . '>; ' . date('r');

        $this->addHeader('Received', $received);
    }

    /**
     * Generate the 'Message-ID' header.
     *
     * @access public
     */
    function addMessageIdHeader()
    {
        require_once dirname(__FILE__) . '/../MIME.php';
        $this->addHeader('Message-ID', MIME::generateMessageID());
    }

    /**
     * Generate the 'Resent' headers (conforms to guidelines in
     * RFC 2822 [3.6.6]).
     *
     * @access public
     *
     * @param string $from  The address to use for 'Resent-From'.
     * @param string $to    The address to use for 'Resent-To'.
     */
    function addResentHeaders($from, $to)
    {
        require_once dirname(__FILE__) . '/../MIME.php';

        /* We don't set Resent-Sender, Resent-Cc, or Resent-Bcc. */
        $this->addHeader('Resent-Date', date('r'));
        $this->addHeader('Resent-From', $from);
        $this->addHeader('Resent-To', $to);
        $this->addHeader('Resent-Message-ID', MIME::generateMessageID());
    }

    /**
     * Generate read receipt headers.
     *
     * @access public
     *
     * @param string $to  The address the receipt should be mailed to.
     */
    function addReadReceiptHeaders($to)
    {
        /* This is the RFC 2298 way of requesting a receipt. */
        $this->addHeader('Disposition-Notification-To', $to);

        /* For certain Pegasus mail installations. */
        $this->addHeader('X-Confirm-Reading-To', $to);
        $this->addHeader('X-PMRQC', 1);
    }

    /**
     * Generate delivery receipt headers.
     *
     * @access public
     *
     * @param string $to  The address the receipt should be mailed to.
     */
    function addDeliveryReceiptHeaders($to)
    {
        /* This is old sendmail (pre-8.7) behavior. */
        $this->addHeader('Return-Receipt-To', $to);
    }

    /**
     * Generate the user agent description header.
     *
     * @access public
     */
    function addAgentHeader()
    {
        $this->addHeader('User-Agent', $this->_agent);
    }

    /**
     * Add a header to the header array.
     *
     * @access public
     *
     * @param string $header  The header name.
     * @param string $value   The header value.
     */
    function addHeader($header, $value)
    {
        $header = trim($header);
        $lcHeader = String::lower($header);

        if (!isset($this->_headers[$lcHeader])) {
            $this->_headers[$lcHeader] = array();
        }
        $this->_headers[$lcHeader]['header'] = $header;
        $this->_headers[$lcHeader]['value'] = $value;
        $this->_headers[$lcHeader]['_alter'] = false;
    }

    /**
     * Remove a header from the header array.
     *
     * @access public
     *
     * @param string $header  The header name.
     */
    function removeHeader($header)
    {
        $header = trim($header);
        $lcHeader = String::lower($header);
        unset($this->_headers[$lcHeader]);
    }

    /**
     * Set a value for a particular header ONLY if that header is set.
     *
     * @access public
     *
     * @param string $header  The header name.
     * @param string $value   The original header value.
     *
     * @return boolean  True if string was set, false if not.
     */
    function setString($header, $value)
    {
        $header = trim($header);
        $lcHeader = String::lower($header);
        if (isset($this->_headers[$lcHeader])) {
            $this->_headers[$lcHeader]['header'] = $value;
            $this->_headers[$lcHeader]['_alter'] = true;
            return true;
        } else {
            return false;
        }
    }

    /**
     * Set a value for a particular header ONLY if that header is set.
     *
     * @access public
     *
     * @param string $header  The header name.
     * @param string $value   The header value.
     *
     * @return boolean  True if value was set, false if not.
     */
    function setValue($header, $value)
    {
        $lcHeader = String::lower($header);
        if (isset($this->_headers[$lcHeader])) {
            $this->_headers[$lcHeader]['value'] = $value;
            $this->_headers[$lcHeader]['_alter'] = true;
            return true;
        } else {
            return false;
        }
    }

    /**
     * Attempts to return the header in the correct case.
     *
     * @access public
     *
     * @param string $header  The header to search for.
     *
     * @return string  The value for the given header.
     *                 If the header is not found, returns null.
     */
    function getString($header)
    {
        $lcHeader = String::lower($header);
        return (isset($this->_headers[$lcHeader])) ? $this->_headers[$lcHeader]['header'] : null;
    }

    /**
     * Attempt to return the value for a given header.
     * The following header fields can only have 1 entry, so if duplicate
     * entries exist, the first value will be used (RFC 2822 [3.6]):
     *   To, From, Cc, Bcc, Date, Sender, Reply-to, Message-ID, In-Reply-To,
     *   References, Subject
     *
     * @access public
     *
     * @param string $header  The header to search for.
     *
     * @return mixed  The value for the given header.
     *                If the header is not found, returns null.
     */
    function getValue($header)
    {
        $header = String::lower($header);

        if (isset($this->_headers[$header])) {
            $single = array('to', 'from', 'cc', 'bcc', 'date', 'sender', 
                            'reply-to', 'message-id', 'in-reply-to',
                            'references', 'subject', 'x-priority');
            if (is_array($this->_headers[$header]['value']) &&
                in_array($header, $single)) {
                return $this->_headers[$header]['value'][0];
            } else {
                return $this->_headers[$header]['value'];
            }
        } else {
            return null;
        }
    }

    /**
     * Has the header been altered from the original?
     *
     * @access public
     *
     * @param string $header  The header to analyze.
     *
     * @return boolean  True if the header has been altered.
     */
    function alteredHeader($header)
    {
        $lcHeader = String::lower($header);
        return (isset($this->_headers[$lcHeader])) ? $this->_headers[$lcHeader]['_alter'] : false;
    }

    /**
     * Transforms a Header value using the list of functions provided.
     *
     * @access public
     *
     * @param string $header  The header to alter.
     * @param mixed $funcs    A function, or an array of functions.
     *                        The functions will be performed from right to
     *                        left.
     */
    function setValueByFunction($header, $funcs)
    {
        $header = String::lower($header);

        if (is_array($funcs)) {
            $funcs = array_reverse($funcs);
        } else {
            $funcs = array($funcs);
        }

        if (isset($this->_headers[$header])) {
            $val = $this->getValue($header);
            if (is_array($val)) {
                $val = implode("\n", $val);
            }
            foreach ($funcs as $func) {
                $val = call_user_func($func, $val);
            }
            $this->setValue($header, $val);
        }
    }

    /**
     * Add any MIME headers required for the MIME_Part.
     *
     * @access public
     *
     * @param object MIME_Part &$mime_part  The MIME_Part object.
     */
    function addMIMEHeaders(&$mime_part)
    {
        foreach ($mime_part->header(array()) as $head => $val) {
            $this->addHeader($head, $val);
        }
    }

    /**
     * Return the list of addresses for a header object.
     *
     * @access public
     *
     * @param array $obs  An array of header objects (See imap_headerinfo()
     *                    for the object structure).
     *
     * @return array  An array of objects.
     * <pre>
     * Object elements:
     * 'address'   -  Full address
     * 'host'      -  Host name
     * 'inner'     -  Trimmed, bare address
     * 'personal'  -  Personal string
     * </pre>
     */
    function getAddressesFromObject($obs)
    {
        $retArray = array();

        if (!is_array($obs) || empty($obs)) {
            return $retArray;
        }

        foreach ($obs as $ob) {
            /* Ensure we're working with initialized values. */
            $ob->personal = isset($ob->personal) ? trim(MIME::decode($ob->personal), '"') : '';

            if (isset($ob->mailbox)) {
                /* Don't process invalid addresses. */
                if (strstr($ob->mailbox, 'UNEXPECTED_DATA_AFTER_ADDRESS') ||
                    strstr($ob->mailbox, 'INVALID_ADDRESS')) {
                    continue;
                }
            } else {
                $ob->mailbox = '';
            }

            if (!isset($ob->host)) {
                $ob->host = '';
            }

            /* Generate the new object. */
            $newOb = &new stdClass;
            $newOb->address = MIME::addrObject2String($ob, array('undisclosed-recipients@', 'Undisclosed recipients@'));
            $newOb->host = $ob->host;
            $newOb->inner = MIME::trimEmailAddress(MIME::rfc822WriteAddress($ob->mailbox, $ob->host, ''));
            $newOb->personal = $ob->personal;

            $retArray[] = &$newOb;
        }

        return $retArray;
    }

    /**
     * Returns the list of valid mailing list headers.
     *
     * @access public
     *
     * @return array  The list of valid mailing list headers.
     */
    function listHeaders()
    {
        return array(
            /* RFC 2369 */
            'list-help'         =>  _("List-Help"),
            'list-unsubscribe'  =>  _("List-Unsubscribe"),
            'list-subscribe'    =>  _("List-Subscribe"),
            'list-owner'        =>  _("List-Owner"),
            'list-post'         =>  _("List-Post"),
            'list-archive'      =>  _("List-Archive"),
            /* RFC 2919 */
            'list-id'           =>  _("List-Id")
        );
    }

    /**
     * Do any mailing list headers exist?
     *
     * @access public
     *
     * @return boolean  True if any mailing list headers exist.
     */
    function listHeadersExist()
    {
        foreach ($this->listHeaders() as $val => $str) {
            if (isset($this->_headers[$val])) {
                return true;
            }
        }

        return false;
    }

    /**
     * Sets a new string to use for EOLs.
     *
     * @access public
     *
     * @param string $eol  The string to use for EOLs.
     */
    function setEOL($eol)
    {
        $this->_eol = $eol;
    }

    /**
     * Get the string to use for EOLs.
     *
     * @access public
     *
     * @return string  The string to use for EOLs.
     */
    function getEOL()
    {
        return $this->_eol;
    }

    /**
     * Returns the flag status.
     *
     * @access public
     *
     * @param string $flag  Is this flag set?
     *                      Flags: recent, unseen, answered, draft, important,
     *                             deleted
     *
     * @return boolean  True if the flag has been set, false if not.
     */
    function getFlag($flag)
    {
        if (!empty($this->_flags[String::lower($flag)])) {
            return true;
        } else {
            return false;
        }
    }

    /**
     * Get the primary from address (first address in the From: header).
     *
     * @access public
     *
     * @return string  The from address (user@host).
     */
    function getFromAddress()
    {
        if (!($ob = $this->getOb('from'))) {
            return null;
        }

        require_once 'Horde/MIME.php';

        return trim(MIME::trimEmailAddress(MIME::rfc822WriteAddress($ob[0]->mailbox, (isset($ob[0]->host)) ? $ob[0]->host : '', '')));
    }

    /**
     * Get a header from the header object.
     *
     * @access public
     *
     * @param string $field    The object field to retrieve (see
     *                         imap_headerinfo() for the list of fields).
     * @param boolean $decode  Should the return value be MIME decoded?
     *                         It will only be decoded if it is not an object
     *                         itself.
     *
     * @return mixed  The field requested.
     */
    function getOb($field, $decode = false)
    {
        $data = array();

        $ob = $this->getHeaderObject();
        if (!is_object($ob)) {
            return $data;
        }

        if (isset($ob->$field)) {
            $data = $ob->$field;
            if (!empty($decode) && !is_object($data) && !is_array($data)) {
                include_once 'Horde/MIME.php';
                $data = MIME::decode($data);
            }
        }

        return (is_string($data)) ? strtr($data, "\t", " ") : $data;
    }

}
