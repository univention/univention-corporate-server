<?php
/**
 * The description of Horde to use in the 'User-Agent:' header.
 */
define('HORDE_AGENT_HEADER', 'Horde Application Framework 3.2');

/**
 * The MIME_Headers:: class contains generic functions related to
 * handling the headers of mail messages.
 *
 * The default character set to use for headers should be defined in the
 * variable $GLOBALS['mime_headers']['default_charset'] (defaults to US-ASCII
 * per RFC 2045).
 *
 * $Horde: framework/MIME/MIME/Headers.php,v 1.29.10.30 2009-04-08 16:26:35 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package Horde_MIME
 */
class MIME_Headers {

    /**
     * The internal headers array.
     *
     * @var array
     */
    var $_headers = array();

    /**
     * Cached output of the MIME_Structure::parseMIMEHeaders() command.
     *
     * @var array
     */
    var $_allHeaders;

    /**
     * Cached output of the imap_fetchheader() command.
     *
     * @var string
     */
    var $_headerText;

    /**
     * The header object returned from imap_headerinfo().
     *
     * @var stdClass
     */
    var $_headerObject;

    /**
     * The User-Agent string to use.
     * THIS VALUE SHOULD BE OVERRIDEN BY ALL SUBCLASSES.
     *
     * @var string
     */
    var $_agent = HORDE_AGENT_HEADER;

    /**
     * The sequence to use as EOL for the headers.
     * The default is currently to output the EOL sequence internally as
     * just "\n" instead of the canonical "\r\n" required in RFC 822 & 2045.
     * To be RFC complaint, the full <CR><LF> EOL combination should be used
     * when sending a message.
     *
     * @var string
     */
    var $_eol = "\n";

    /**
     * The index of the message.
     *
     * @var integer
     */
    var $_index;

    /**
     * Constructor.
     *
     * @param integer $index  The message index to parse headers (DEPRECATED).
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
     * @return string  See imap_fetchheader().
     */
    function getHeaderText()
    {
        if (!is_null($this->_index) && empty($this->_headerText)) {
            $this->_headerText = @imap_fetchheader($this->_getStream(), $this->_index, FT_UID);
            require_once 'Horde/MIME.php';
            if (MIME::is8bit($this->_headerText)) {
                $this->_headerText = String::convertCharset($this->_headerText, !empty($GLOBALS['mime_headers']['default_charset']) ? $GLOBALS['mime_headers']['default_charset'] : 'US-ASCII');
            }
        }

        return $this->_headerText;
    }

    /**
     * Return the full list of headers.
     *
     * @param boolean $decode  Decode the headers?
     *
     * @return array  See MIME_Structure::parseMIMEHeaders().
     */
    function getAllHeaders($decode = true)
    {
        if (!is_null($this->_index) && empty($this->_allHeaders)) {
            require_once 'Horde/MIME/Structure.php';
            $this->_allHeaders = MIME_Structure::parseMIMEHeaders($this->getHeaderText(), $decode);
        }

        return $this->_allHeaders;
    }

    /**
     * Build the header array.
     *
     * @param boolean $decode  MIME decode the headers?
     */
    function buildHeaders($decode = true)
    {
        if (empty($this->_headers)) {
            foreach ($this->getAllHeaders($decode) as $key => $val) {
                $this->addHeader($key, $val);
            }
        }
    }

    /**
     * Returns the internal header array in array format.
     *
     * @return array  The headers in array format.
     */
    function toArray()
    {
        $return_array = array();

        foreach ($this->_headers as $ob) {
            $header = $ob['header'];
            if (is_array($ob['value'])) {
                if (String::lower($header) == 'received') {
                    $return_array[$header] = $ob['value'];
                } else {
                    $return_array[$header] = reset($ob['value']);
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
     * @return string  The headers in string format.
     */
    function toString()
    {
        $text = '';

        foreach ($this->_headers as $ob) {
            if (!is_array($ob['value'])) {
                $ob['value'] = array($ob['value']);
            }
            foreach ($ob['value'] as $entry) {
                $text .= $ob['header'] . ': ' . $entry . $this->_eol;
            }
        }

        return $text . $this->_eol;
    }

    /**
     * Generate the 'Received' header for the Web browser->Horde hop
     * (attempts to conform to guidelines in RFC 2821).
     */
    function addReceivedHeader()
    {
        $have_netdns = @include_once 'Net/DNS.php';
        if ($have_netdns) {
            $resolver = new Net_DNS_Resolver();
            $resolver->retry = isset($GLOBALS['conf']['dns']['retry']) ? $GLOBALS['conf']['dns']['retry'] : 1;
            $resolver->retrans = isset($GLOBALS['conf']['dns']['retrans']) ? $GLOBALS['conf']['dns']['retrans'] : 1;
        }

        if (isset($_SERVER['HTTP_X_FORWARDED_FOR'])) {
            /* This indicates the user is connecting through a proxy. */
            $remote_path = explode(',', $_SERVER['HTTP_X_FORWARDED_FOR']);
            $remote_addr = $remote_path[0];
            if ($have_netdns) {
                $response = $resolver->query($remote_addr, 'PTR');
                $remote = $response ? $response->answer[0]->ptrdname : $remote_addr;
            } else {
                $remote = @gethostbyaddr($remote_addr);
            }
        } else {
            $remote_addr = $_SERVER['REMOTE_ADDR'];
            if (empty($_SERVER['REMOTE_HOST'])) {
                if ($have_netdns) {
                    $response = $resolver->query($remote_addr, 'PTR');
                    $remote = $response ? $response->answer[0]->ptrdname : $remote_addr;
                } else {
                    $remote = @gethostbyaddr($remote_addr);
                }
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

        if (!empty($GLOBALS['conf']['server']['name'])) {
            $server_name = $GLOBALS['conf']['server']['name'];
        } elseif (!empty($_SERVER['SERVER_NAME'])) {
            $server_name = $_SERVER['SERVER_NAME'];
        } elseif (!empty($_SERVER['HTTP_HOST'])) {
            $server_name = $_SERVER['HTTP_HOST'];
        } else {
            $server_name = 'unknown';
        }
        $received .= 'by ' . $server_name . ' (Horde Framework) with HTTP; ';

        $received .= date('r');

        $this->addHeader('Received', $received);
    }

    /**
     * Generate the 'Message-ID' header.
     */
    function addMessageIdHeader()
    {
        require_once 'Horde/MIME.php';
        $this->addHeader('Message-ID', MIME::generateMessageID());
    }

    /**
     * Generate the 'Resent' headers (conforms to guidelines in
     * RFC 2822 [3.6.6]).
     *
     * @param string $from  The address to use for 'Resent-From'.
     * @param string $to    The address to use for 'Resent-To'.
     */
    function addResentHeaders($from, $to)
    {
        require_once 'Horde/MIME.php';

        /* We don't set Resent-Sender, Resent-Cc, or Resent-Bcc. */
        $this->addHeader('Resent-Date', date('r'));
        $this->addHeader('Resent-From', $from);
        $this->addHeader('Resent-To', $to);
        $this->addHeader('Resent-Message-ID', MIME::generateMessageID());
    }

    /**
     * Generate the user agent description header.
     */
    function addAgentHeader()
    {
        $this->addHeader('User-Agent', $this->_agent);
    }

    /**
     * Returns the user agent description header.
     *
     * @return string  The user agent header.
     */
    function getAgentHeader()
    {
        return $this->_agent;
    }

    /**
     * Add a header to the header array.
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
     * entries exist, the first value will be used:
     *   * To, From, Cc, Bcc, Date, Sender, Reply-to, Message-ID, In-Reply-To,
     *     References, Subject (RFC 2822 [3.6])
     *   * All List Headers (RFC 2369 [3])
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
            $single = array_merge($single, array_keys($this->listHeaders()));
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
     * @param MIME_Part &$mime_part  The MIME_Part object.
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
     * @param array $obs  An array of header objects (See imap_headerinfo()
     *                    for the object structure).
     *
     * @return array  An array of objects.
     * <pre>
     * Object elements:
     * 'address'   -  Full address
     * 'display'   -  A displayable version of the address (Horde 3.2.1+)
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
             $ob->personal = (isset($ob->personal)) ? stripslashes(trim(MIME::decode($ob->personal), '"')) : '';

            if (isset($ob->mailbox)) {
                /* Don't process invalid addresses. */
                if (strpos($ob->mailbox, 'UNEXPECTED_DATA_AFTER_ADDRESS') !== false ||
                    strpos($ob->mailbox, 'INVALID_ADDRESS') !== false) {
                    continue;
                }
            } else {
                $ob->mailbox = '';
            }

            if (!isset($ob->host)) {
                $ob->host = '';
            }

            $inner = MIME::trimEmailAddress(MIME::rfc822WriteAddress($ob->mailbox, $ob->host, ''));

            /* Generate the new object. */
            $newOb = &new stdClass;
            $newOb->address = MIME::addrObject2String($ob, array('undisclosed-recipients@', 'Undisclosed recipients@'));
            $newOb->display = (empty($ob->personal) ? '' : $ob->personal . ' <') . $inner . (empty($ob->personal) ? '' : '>');
            $newOb->host = $ob->host;
            $newOb->inner = $inner;
            $newOb->personal = $ob->personal;

            $retArray[] = &$newOb;
        }

        return $retArray;
    }

    /**
     * Returns the list of valid mailing list headers.
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
     * @return boolean  True if any mailing list headers exist.
     */
    function listHeadersExist()
    {
        return (bool) count(array_intersect(array_keys($this->listHeaders()), array_keys($this->_headers)));
    }

    /**
     * Sets a new string to use for EOLs.
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
     * @return string  The string to use for EOLs.
     */
    function getEOL()
    {
        return $this->_eol;
    }

    /**
     * Get the primary from address (first address in the From: header).
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
     * @todo Replace with getOb() from IMP's IMP_Headers for Horde 4.0.
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
                require_once 'Horde/MIME.php';
                if (MIME::is8bit($this->_headerText)) {
                    $data = String::convertCharset($data, !empty($GLOBALS['mime_headers']['default_charset']) ? $GLOBALS['mime_headers']['default_charset'] : 'US-ASCII');
                }
                $data = MIME::decode($data);
            }
        }

        return (is_string($data)) ? strtr($data, "\t", ' ') : $data;
    }

    /* Deprecated functions. */

    /**
     * The internal flags array.
     *
     * @deprecated since Horde 3.2
     * @var array
     */
    var $_flags = array();

    /**
     * Build the flags array.
     *
     * @deprecated since Horde 3.2
     */
    function buildFlags()
    {
        if (!empty($this->_flags)) {
            return;
        }

        /* Get the IMAP header object. */
        $ob = $this->getHeaderObject();
        if (!is_object($ob)) {
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

        /* Flagged flag */
        if ($ob->Flagged == 'F') {
            $this->_flags['flagged'] = true;
        }

        /* Deleted flag */
        if ($ob->Deleted == 'D') {
            $this->_flags['deleted'] = true;
        }
    }

    /**
     * Returns the flag status.
     *
     * @deprecated since Horde 3.2
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
     * Return the header object from imap_headerinfo().
     *
     * @deprecated since Horde 3.2
     *
     * @return stdClass  See imap_headerinfo().
     */
    function getHeaderObject()
    {
        if (!is_null($this->_index) && empty($this->_headerObject)) {
            $stream = $this->_getStream();
            $this->_headerObject = @imap_headerinfo($stream, @imap_msgno($stream, $this->_index));
        }

        return $this->_headerObject;
    }

    /**
     * Generate delivery receipt headers.
     *
     * @deprecated since Horde 3.2
     *
     * @param string $to  The address the receipt should be mailed to.
     */
    function addDeliveryReceiptHeaders($to)
    {
        /* This is old sendmail (pre-8.7) behavior. */
        $this->addHeader('Return-Receipt-To', $to);
    }

}
