<?php

require_once 'Horde/String.php';
require_once 'Horde/MIME.php';
require_once 'Horde/MIME/Headers.php';
require_once 'Horde/MIME/Message.php';
require_once 'Mail.php';

/**
 * The MIME_Mail:: class wraps around the various MIME library classes to
 * provide a simple interface for creating and sending MIME messages.
 *
 * $Horde: framework/MIME/MIME/Mail.php,v 1.8.2.7 2009-01-06 15:23:20 jan Exp $
 *
 * Copyright 2007-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @since Horde 3.2
 * @package Horde_MIME
 */
class MIME_Mail {

    /**
     * The message headers.
     *
     * @var MIME_Headers
     */
    var $_headers;

    /**
     * The main body part.
     *
     * @var MIME_Part
     */
    var $_body;

    /**
     * The main HTML body part.
     *
     * @var MIME_Part
     */
    var $_htmlBody;

    /**
     * The message recipients.
     *
     * @var array
     */
    var $_recipients = array();

    /**
     * All MIME parts except the main body part.
     *
     * @var array
     */
    var $_parts = array();

    /**
     * The Mail driver name.
     *
     * @link http://pear.php.net/Mail
     * @var string
     */
    var $_mailer_driver = 'smtp';

    /**
     * The Mail driver parameters.
     *
     * @link http://pear.php.net/Mail
     * @var array
     */
    var $_mailer_params = array();

    /**
     * Constructor.
     *
     * @param string $subject  The message subject.
     * @param string $body     The message body.
     * @param string $to       The message recipient(s).
     * @param string $from     The message sender.
     * @param string $charset  The character set of the message.
     */
    function MIME_Mail($subject = null, $body = null, $to = null,
                       $from = null, $charset = null)
    {
        /* Set SERVER_NAME. */
        if (!isset($_SERVER['SERVER_NAME'])) {
            $_SERVER['SERVER_NAME'] = php_uname('n');
        }
        if (!$charset) {
            $charset = 'iso-8859-1';
        }

        $this->_headers = new MIME_Headers();

        if ($subject) {
            $this->addHeader('Subject', $subject, $charset);
        }
        if ($to) {
            $this->addHeader('To', $to, $charset);
        }
        if ($from) {
            $this->addHeader('From', $from, $charset);
        }
        if ($body) {
            $this->setBody($body, $charset);
        }
    }

    /**
     * Adds several message headers at once.
     *
     * @see addHeader()
     *
     * @param array $header    Hash with header names as keys and header
     *                         contents as values.
     * @param string $charset  The header value's charset.
     */
    function addHeaders($headers = array(), $charset = null)
    {
        foreach ($headers as $header => $value) {
            if (is_a($added = $this->addHeader($header, $value, $charset), 'PEAR_Error')) {
                return $added;
            }
        }
    }

    /**
     * Adds a message header.
     *
     * @see addHeaders()
     *
     * @param string $header      The header name.
     * @param string $value       The header value.
     * @param string $charset     The header value's charset.
     * @param boolean $overwrite  If true, an existing header of the same name
     *                            is being overwritten; if false, multiple
     *                            headers are added; if null, the correct
     *                            behaviour is automatically chosen depending
     *                            on the header name.
     */
    function addHeader($header, $value, $charset = null, $overwrite = null)
    {
        $lc_header = String::lower($header);

        /* Only encode value if charset is explicitly specified, otherwise
         * the message's charset will be used when building the message. */
        if (!empty($charset)) {
            if (in_array($lc_header, array('to', 'from', 'cc', 'bcc', 'sender', 'reply-to'))) {
                $value = MIME::encodeAddress($value, $charset);
            } else {
                $value = MIME::encode($value, $charset);
            }
        }

        if (is_null($overwrite)) {
            /* The following header fields can only have 1 entry, so if
             * duplicate entries exist, the first value will be used:
             *   * To, From, Cc, Bcc, Date, Sender, Reply-to, Message-ID,
             *     In-Reply-To, References, Subject (RFC 2822 [3.6])
             *   * All List Headers (RFC 2369 [3]) */
            $single = array('to', 'from', 'cc', 'bcc', 'date', 'sender',
                            'reply-to', 'message-id', 'in-reply-to',
                            'references', 'subject', 'x-priority');
            $single = array_merge($single,
                                  array_keys($this->_headers->listHeaders()));
            if (in_array($lc_header, $single)) {
                $overwrite = true;
            }
        }
        if ($overwrite) {
            $this->_headers->removeHeader($header);
        }
        if ($lc_header !== 'bcc') {
            $this->_headers->addHeader($header, $value);
        }

        if (in_array($lc_header, array('to', 'cc', 'bcc'))) {
            return $this->addRecipients($value);
        }
    }

    /**
     * Removes a message header.
     *
     * @param string $header  The header name.
     */
    function removeHeader($header)
    {
        $value = $this->_headers->getValue($header);
        $this->_headers->removeHeader($header);
        if (in_array(String::lower($header), array('to', 'cc', 'bcc'))) {
            $this->removeRecipients($value);
        }
    }

    /**
     * Sets the message body text.
     *
     * @param string $body             The message content.
     * @param string $charset          The character set of the message.
     * @param boolean|integer $wrap    If true, wrap the message at column 76;
     *                                 If an integer wrap the message at that
     *                                 column. Don't use wrapping if sending
     *                                 flowed messages.
     */
    function setBody($body, $charset = 'iso-8859-1', $wrap = false)
    {
        if ($wrap) {
            if ($wrap === true) {
                $wrap = 76;
            }
            $body = String::wrap($body, $wrap, "\n");
        }
        $this->_body = new MIME_Part('text/plain', $body, $charset);
    }

    /**
     * Sets the HTML message body text.
     *
     * @param string $body          The message content.
     * @param string $charset       The character set of the message.
     * @param boolean $alternative  If true, a multipart/alternative message is
     *                              created and the text/plain part is
     *                              generated automatically. If false, a
     *                              text/html message is generated.
     */
    function setHTMLBody($body, $charset = 'iso-8859-1', $alternative = true)
    {
        $this->_htmlBody = new MIME_Part('text/html', $body, $charset);
        if ($alternative) {
            require_once 'Horde/Text/Filter.php';
            $body = Text_Filter::filter($body, 'html2text', array('wrap' => false));
            $this->_body = new MIME_Part('text/plain', $body, $charset);
        }
    }

    /**
     * Adds a message part.
     *
     * @param string $mime_type    The content type of the part.
     * @param string $content      The content of the part.
     * @param string $charset      The character set of the part.
     * @param string $disposition  The content disposition of the part.
     *
     * @return integer  The part number.
     */
    function addPart($mime_type, $content, $charset = 'us-ascii',
                     $disposition = null)
    {
        $part = new MIME_Part($mime_type, $content, $charset, $disposition);
        $part->transferEncodeContents();
        $this->_parts[] = $part;
        return count($this->_parts) - 1;
    }

    /**
     * Adds a MIME message part.
     *
     * @param MIME_Part $part  A MIME_Part object.
     *
     * @return integer  The part number.
     */
    function addMIMEPart($part)
    {
        $part->transferEncodeContents();
        $this->_parts[] = $part;
        return count($this->_parts) - 1;
    }

    /**
     * Adds an attachment.
     *
     * @param string $file     The path to the file.
     * @param string $name     The file name to use for the attachment.
     * @param string $type     The content type of the file.
     * @param string $charset  The character set of the part (only relevant for
     *                         text parts.
     *
     * @return integer  The part number.
     */
    function addAttachment($file, $name = null, $type = null, $charset = 'us-ascii')
    {
        if (empty($name)) {
            $name = basename($file);
        }
        if (empty($type)) {
            require_once 'Horde/MIME/Magic.php';
            $type = MIME_Magic::filenameToMIME($file, false);
        }

        $part = new MIME_Part($type, file_get_contents($file), $charset, 'attachment');
        $part->setName($name);
        $part->transferEncodeContents();
        $this->_parts[] = $part;

        return count($this->_parts) - 1;
    }

    /**
     * Removes a message part.
     *
     * @param integer $part  The part number.
     */
    function removePart($part)
    {
        if (isset($this->_parts[$part])) {
            unset($this->_parts[$part]);
        }
    }

    /**
     * Adds message recipients.
     *
     * Recipients specified by To:, Cc:, or Bcc: headers are added
     * automatically.
     *
     * @param string|array  List of recipients, either as a comma separated
     *                      list or as an array of email addresses.
     */
    function addRecipients($recipients)
    {
        $recipients = $this->_buildRecipients($recipients);
        if (is_a($recipients, 'PEAR_Error')) {
            return $recipients;
        }
        $this->_recipients = array_merge($this->_recipients, $recipients);
    }

    /**
     * Removes message recipients.
     *
     * @param string|array  List of recipients, either as a comma separated
     *                      list or as an array of email addresses.
     */
    function removeRecipients($recipients)
    {
        $recipients = $this->_buildRecipients($recipients);
        if (is_a($recipients, 'PEAR_Error')) {
            return $recipients;
        }
        $this->_recipients = array_diff($this->_recipients, $recipients);
    }

    /**
     * Removes all message recipients.
     */
    function clearRecipients()
    {
        $this->_recipients = array();
    }

    /**
     * Builds a recipients list.
     *
     * @param string|array  List of recipients, either as a comma separated
     *                      list or as an array of email addresses.
     *
     * @return array  Normalized list of recipients or PEAR_Error on failure.
     */
    function _buildRecipients($recipients)
    {
        if (is_string($recipients)) {
            $recipients = MIME::rfc822Explode($recipients, ',');
        }
        $recipients = array_filter(array_map('trim', $recipients));

        $addrlist = array();
        foreach ($recipients as $email) {
            if (!empty($email)) {
                $unique = MIME::bareAddress($email);
                if ($unique &&
                    ($unique != 'UNEXPECTED_DATA_AFTER_ADDRESS@.SYNTAX-ERROR.')) {
                    $addrlist[$unique] = $email;
                } else {
                    $addrlist[$email] = $email;
                }
            }
        }

        foreach (MIME::bareAddress(implode(', ', $addrlist), null, true) as $val) {
            if (MIME::is8bit($val)) {
                return PEAR::raiseError(sprintf(_("Invalid character in e-mail address: %s."), $val));
            }
        }

        return $addrlist;
    }

    /**
     * Sends this message.
     *
     * For the possible Mail drivers and parameters see the PEAR Mail
     * documentation.
     * @link http://pear.php.net/Mail
     *
     * @param string $driver   The Mail driver to use.
     * @param array $params    Any parameters necessary for the Mail driver.
     * @param boolean $resend  If true, the message id and date are re-used;
     *                         If false, they will be updated.
     * @param boolean $flowed  Send message in flowed text format. @since
     *                         Horde 3.2.1
     *
     * @return mixed  True on success, PEAR_Error on error.
     */
    function send($driver = null, $params = array(), $resend = false,
                  $flowed = true)
    {
        /* Add mandatory headers if missing. */
        if (!$resend || !$this->_headers->getString('Message-ID')) {
            $this->_headers->addMessageIdHeader();
        }
        if (!$this->_headers->getString('User-Agent')) {
            $this->_headers->addAgentHeader();
        }
        if (!$resend || !$this->_headers->getString('Date')) {
            $this->_headers->addHeader('Date', date('r'));
        }

        /* Send in flowed format. */
        if ($flowed && !empty($this->_body)) {
            require_once 'Text/Flowed.php';
            $flowed = new Text_Flowed($this->_body->getContents(),
                                      $this->_body->getCharset());
            $flowed->setDelSp(true);
            $this->_body->setContentTypeParameter('DelSp', 'Yes');
            $this->_body->setContents($flowed->toFlowed());
            $this->_body->setContentTypeParameter('format', 'flowed');
        }

        /* Build mime message. */
        $mime = new MIME_Message();
        if (!empty($this->_body) && !empty($this->_htmlBody)) {
            $basepart = new MIME_Part('multipart/alternative');
            $this->_body->setDescription(_("Plaintext Version of Message"));
            $basepart->addPart($this->_body);
            $this->_htmlBody->setDescription(_("HTML Version of Message"));
            $basepart->addPart($this->_htmlBody);
            $mime->addPart($basepart);
        } elseif (!empty($this->_htmlBody)) {
            $mime->addPart($this->_htmlBody);
        } elseif (!empty($this->_body)) {
            $mime->addPart($this->_body);
        }
        foreach ($this->_parts as $mime_part) {
            $mime->addPart($mime_part);
        }
        $this->_headers->addMIMEHeaders($mime);

        /* Check mailer configuration. */
        if (!empty($driver)) {
            $this->_mailer_driver = $driver;
        }
        if (!empty($params)) {
            $this->_mailer_params = $params;
        }

        /* Send message. */
        return $mime->send(implode(', ', $this->_recipients), $this->_headers,
                           $this->_mailer_driver, $this->_mailer_params);
    }

}
