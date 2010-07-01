<?php

require_once dirname(__FILE__) . '/Part.php';

/**
 * The MIME_Message:: class provides methods for creating and manipulating
 * MIME email messages.
 *
 * $Horde: framework/MIME/MIME/Message.php,v 1.76.10.19 2009-01-06 15:23:20 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package Horde_MIME
 */
class MIME_Message extends MIME_Part {

    /**
     * Has the message been parsed via buildMessage()?
     *
     * @var boolean
     */
    var $_build = false;

    /**
     * The server to default unqualified addresses to.
     *
     * @var string
     */
    var $_defaultServer = null;

    /**
     * Constructor - creates a new MIME email message.
     *
     * @param string $defaultServer  The server to default unqualified
     *                               addresses to.
     */
    function MIME_Message($defaultServer = null)
    {
        if (is_null($defaultServer)) {
            $this->_defaultServer = $_SERVER['SERVER_NAME'];
        } else {
            $this->_defaultServer = $defaultServer;
        }
    }

    /**
     * Create a MIME_Message object from a MIME_Part object.
     * This function can be called statically via:
     *    MIME_Message::convertMIMEPart();
     *
     * @param MIME_Part &$mime_part  The MIME_Part object.
     * @param string $server         The server to default unqualified
     *                               addresses to.
     *
     * @return MIME_Message  The new MIME_Message object.
     */
    function &convertMIMEPart(&$mime_part, $server = null)
    {
        if (!$mime_part->getMIMEId()) {
            $mime_part->setMIMEId(1);
        }

        $mime_message = &new MIME_Message($server);
        $mime_message->addPart($mime_part);
        $mime_message->buildMessage();

        return $mime_message;
    }

    /**
     * Sends this message.
     *
     * @param string $email    The address list to send to.
     * @param mixed &$headers  The MIME_Headers object holding this message's
     *                         headers, or a hash with header->value mappings.
     * @param string $driver   The Mail driver to use (since Horde 3.0.4).
     * @param array $params    Any parameters necessary for the Mail driver
     *                         (since Horde 3.0.4).
     *
     * @return mixed  True on success, PEAR_Error on error.
     */
    function send($email, &$headers, $driver = null, $params = array())
    {
        global $conf;
        static $mailer;

        if (!isset($driver)) {
            $driver = $conf['mailer']['type'];
            $params = $conf['mailer']['params'];
        }
        if (!isset($mailer)) {
            require_once 'Mail.php';
            $mailer = Mail::factory($driver, $params);
        }

        $msg = $this->toString();
        if (is_object($headers)) {
            $headerArray = $this->encode($headers->toArray(), $this->getCharset());
        } else {
            $headerArray = $this->encode($headers, $this->getCharset());
        }

        /* Make sure the message has a trailing newline. */
        if (substr($msg, -1) != "\n") {
            $msg .= "\n";
        }

        $result = $mailer->send(MIME::encodeAddress($email), $headerArray, $msg);

        if (is_a($result, 'PEAR_Error') && $driver == 'sendmail') {
            $userinfo = $result->toString();
            // Interpret return values as defined in /usr/include/sysexits.h
            switch ($result->getCode()) {
            case 64: // EX_USAGE
                $error = 'sendmail: ' . _("command line usage error") . ' (64)';
                break;

            case 65: // EX_DATAERR
                $error = 'sendmail: ' . _("data format error") . ' (65)';
                break;

            case 66: // EX_NOINPUT
                $error = 'sendmail: ' . _("cannot open input") . ' (66)';
                break;

            case 67: // EX_NOUSER
                $error = 'sendmail: ' . _("addressee unknown") . ' (67)';
                break;

            case 68: // EX_NOHOST
                $error = 'sendmail: ' . _("host name unknown") . ' (68)';
                break;

            case 69: // EX_UNAVAILABLE
                $error = 'sendmail: ' . _("service unavailable") . ' (69)';
                break;

            case 70: // EX_SOFTWARE
                $error = 'sendmail: ' . _("internal software error") . ' (70)';
                break;

            case 71: // EX_OSERR
                $error = 'sendmail: ' . _("system error") . ' (71)';
                break;

            case 72: // EX_OSFILE
                $error = 'sendmail: ' . _("critical system file missing") . ' (72)';
                break;

            case 73: // EX_CANTCREAT
                $error = 'sendmail: ' . _("cannot create output file") . ' (73)';
                break;

            case 74: // EX_IOERR
                $error = 'sendmail: ' . _("input/output error") . ' (74)';
                break;

            case 75: // EX_TEMPFAIL
                $error = 'sendmail: ' . _("temporary failure") . ' (75)';
                break;

            case 76: // EX_PROTOCOL
                $error = 'sendmail: ' . _("remote error in protocol") . ' (76)';
                break;

            case 77: // EX_NOPERM
                $error = 'sendmail: ' . _("permission denied") . ' (77)';
                break;

            case 78: // EX_CONFIG
                $error = 'sendmail: ' . _("configuration error") . ' (78)';
                break;

            case 79: // EX_NOTFOUND
                $error = 'sendmail: ' . _("entry not found") . ' (79)';
                break;

            default:
                $error = $result;
                $userinfo = null;
            }
            return PEAR::raiseError($error, null, null, null, $userinfo);
        }

        return $result;
    }

    /**
     * Take a set of headers and make sure they are encoded properly.
     *
     * @param array $headers   The headers to encode.
     * @param string $charset  The character set to use.
     *
     * @return array  The array of encoded headers.
     */
    function encode($headers, $charset)
    {
        require_once 'Horde/MIME.php';

        $addressKeys = array('To', 'Cc', 'Bcc', 'From');
        $asciikeys = array('MIME-Version', 'Received', 'Message-ID', 'Date', 'Content-Disposition', 'Content-Transfer-Encoding', 'Content-ID', 'Content-Type', 'Content-Description');
        foreach ($headers as $key => $val) {
            if (is_array($val)) {
                foreach ($val as $key2 => $val2) {
                    $headers[$key][$key2] = MIME::wrapHeaders($key, $val2, $this->getEOL());
                }
            } else {
                if (in_array($key, $addressKeys)) {
                    $text = MIME::encodeAddress($val, $charset, $this->_defaultServer);
                    if (is_a($text, 'PEAR_Error')) {
                        $text = $val;
                    }
                } else {
                    $text = MIME::encode($val, in_array($key, $asciikeys) ? 'US-ASCII' : $charset);
                }
                $headers[$key] = MIME::wrapHeaders($key, $text, $this->getEOL());
            }
        }

        return $headers;
    }

    /**
     * Add the proper set of MIME headers for this message to an array.
     *
     * @param array $headers  The headers to add the MIME headers to.
     *
     * @return array  The full set of headers including MIME headers.
     */
    function header($headers = array())
    {
        /* Per RFC 2045 [4], this MUST appear in the message headers. */
        $headers['MIME-Version'] = '1.0';

        if ($this->_build) {
            return parent::header($headers);
        } else {
            $this->buildMessage();
            return $this->encode($this->header($headers), $this->getCharset());
        }
    }

    /**
     * Return the entire message contents, including headers, as a string.
     *
     * @return string  The encoded, generated message.
     */
    function toString()
    {
        if ($this->_build) {
            return parent::toString(false);
        } else {
            $this->buildMessage();
            return $this->toString();
        }
    }

    /**
     * Build message from current contents.
     */
    function buildMessage()
    {
        if ($this->_build) {
            return;
        }

        if (empty($this->_flags['setType'])) {
            if (count($this->_parts) > 1) {
                $this->setType('multipart/mixed');
            } else {
                /* Copy the information from the single part to the current
                   base part. */
                if (($obVars = get_object_vars(reset($this->_parts)))) {
                    foreach ($obVars as $key => $val) {
                        $this->$key = $val;
                    }
                }
            }
        }

        /* Set the build flag now. */
        $this->_build = true;
    }

    /**
     * Get a list of all MIME subparts.
     *
     * @return array  An array of the MIME_Part subparts.
     */
    function getParts()
    {
        if ($this->_build) {
            return parent::getParts();
        } else {
            $this->buildMessage();
            return $this->getParts();
        }
    }

    /**
     * Return the base part of the message. This function does NOT
     * return a reference to make sure that the whole MIME_Message
     * object isn't accidentally modified.
     *
     * @return MIME_Message  The base MIME_Part of the message.
     */
    function getBasePart()
    {
        $this->buildMessage();
        return $this;
    }

    /**
     * Retrieve a specific MIME part.
     *
     * @param string $id  The MIME_Part ID string.
     *
     * @return MIME_Part  The MIME_Part requested, or false if the part
     *                    doesn't exist.
     */
    function &getPart($id)
    {
        if ($this->_build) {
            $part = parent::getPart($id);
        } else {
            $this->buildMessage();
            $part = $this->getPart($id);
        }
        if (is_a($part, 'MIME_Message')) {
            $newpart = &new MIME_Part();
            $skip = array('_build', '_defaultServer');
            foreach (array_keys(get_object_vars($part)) as $key) {
                /* Ignore local variables that aren't a part of the original
                 * class. */
                if (!in_array($key, $skip)) {
                    $newpart->$key = &$part->$key;
                }
            }
            return $newpart;
        } else {
            return $part;
        }
    }

}
