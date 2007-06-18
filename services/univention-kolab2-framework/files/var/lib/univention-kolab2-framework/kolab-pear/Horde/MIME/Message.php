<?php

require_once dirname(__FILE__) . '/Part.php';

/**
 * The MIME_Message:: class provides methods for creating and manipulating
 * MIME email messages.
 *
 * $Horde: framework/MIME/MIME/Message.php,v 1.76 2004/04/16 21:00:42 jan Exp $
 *
 * Copyright 1999-2004 Chuck Hagenbuch <chuck@horde.org>
 * Copyright 2002-2004 Michael Slusarz <slusarz@bigworm.colorado.edu>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Michael Slusarz <slusarz@bigworm.colorado.edu>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 1.3
 * @package Horde_MIME
 */
class MIME_Message extends MIME_Part {

    /**
     * Has the message been parsed via buildMessage()?
     *
     * @var boolean $_build
     */
    var $_build = false;

    /**
     * The server to default unqualified addresses to.
     *
     * @var string $_defaultServer
     */
    var $_defaultServer = null;

    /**
     * Constructor - creates a new MIME email message.
     *
     * @access public
     *
     * @param optional string $defaultServer  The server to default
     *                                        unqualified addresses to.
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
     * @access public
     *
     * @param object MIME_Part &$mime_part  The MIME_Part object.
     * @param optional string $server       The server to default unqualified
     *                                      addresses to.
     *
     * @return object MIME_Message  The new MIME_Message object.
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
     * Send a message.
     *
     * @access public
     *
     * @param string  $email      The address list to send to.
     * @param mixed  &$headers    The MIME_Headers object holding
     *                            this message's headers, *or* a hash
     *                            with header->value mappings.
     *
     * @return mixed  True on success, PEAR_Error object on error.
     */
    function send($email, &$headers)
    {
        global $conf;
        static $mailer;

        if (!isset($mailer)) {
            require_once 'Mail.php';
            $mailer = &Mail::factory($conf['mailer']['type'], $conf['mailer']['params']);
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

        return $mailer->send(MIME::encodeAddress($email), $headerArray, $msg);
    }

    /**
     * Take a set of headers and make sure they are encoded properly.
     *
     * @access public
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
        foreach ($headers as $key => $val) {
            if (in_array($key, $addressKeys)) {
                $text = MIME::encodeAddress($val, $charset, $this->_defaultServer);
            } else {
                $text = MIME::encode($val, $charset);
            }
            $headers[$key] = MIME::wrapHeaders($key, $text, $this->getEOL());
        }

        return $headers;
    }

    /**
     * Add the proper set of MIME headers for this message to an array.
     *
     * @access public
     *
     * @param optional array $headers  The headers to add the MIME headers to.
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
     * @access public
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
     *
     * @access public
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
     * @access public
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
     * @access public
     *
     * @return object MIME_Message  The base MIME_Part of the message.
     */
    function getBasePart()
    {
        $this->buildMessage();
        return $this;
    }

    /**
     * Retrieve a specific MIME part.
     *
     * @access public
     *
     * @param string $id  The MIME_Part ID string.
     *
     * @return object MIME_Part  The MIME_Part requested.  Returns false if
     *                           the part doesn't exist.
     */
    function getPart($id)
    {
        if ($this->_build) {
            return parent::getPart($id);
        } else {
            $this->buildMessage();
            return $this->getPart($id);
        }
    }

}
