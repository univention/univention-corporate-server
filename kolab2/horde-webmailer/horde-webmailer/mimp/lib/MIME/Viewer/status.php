<?php
/**
 * The MIMP_MIME_Viewer_status class handles multipart/report messages
 * that refer to mail system administrative messages (RFC 3464).
 *
 * $Horde: mimp/lib/MIME/Viewer/status.php,v 1.1.2.2 2009-01-06 15:24:54 jan Exp $
 *
 * Copyright 2008-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package Horde_MIME_Viewer
 */
class MIMP_MIME_Viewer_status extends MIME_Viewer {

    /**
     * Render out the currently set contents.
     *
     * @param array $params  An array with a reference to a MIME_Contents
     *                       object.
     *
     * @return string  The rendered text in HTML.
     */
    function render($params)
    {
        $contents = &$params[0];

        /* If this is a straight message/delivery-status part, just output
           the text. */
        if ($this->mime_part->getType() == 'message/delivery-status') {
            $part = new MIME_Part('text/plain');
            $part->setContents($this->mime_part->getContents());
            return $contents->renderMIMEPart($part);
        }

        global $registry;

        /* RFC 3464 [2]: There are three parts to a delivery status
           multipart/report message:
             (1) Human readable message
             (2) Machine parsable body part (message/delivery-status)
             (3) Returned message (optional)
           MIMP only displays the human readable message. */
        $action = null;
        $part2 = $contents->getDecodedMIMEPart($this->mime_part->getRelativeMIMEId(2));
        if (empty($part2)) {
            return $this->_errorMsg($contents);
        }

        foreach (explode("\n", $part2->getContents()) as $line) {
            if (strstr($line, 'Action:') !== false) {
                $pos = strpos($line, ':') + 1;
                $action = strtolower(trim(substr($line, $pos)));
                break;
            }
        }
        if (strpos($action, ' ') !== false) {
            $action = substr($action, 0, strpos($action, ' '));
        }

        /* Get the correct text string for the action type. */
        $msg = array();
        switch ($action) {
        case 'failed':
        case 'delayed':
            $msg = array(
                _("ERROR: Your message could not be delivered."),
                _("The mail server generated the following error message:")
            );
            break;

        case 'delivered':
        case 'expanded':
        case 'relayed':
            $msg = array(
                _("Your message was successfully delivered."),
                _("The mail server generated the following message:")
            );
            break;
        }

        /* Print the human readable message. */
        $part = $contents->getDecodedMIMEPart($this->mime_part->getRelativeMIMEId(1));
        if (empty($part)) {
            return $this->_errorMsg($contents);
        }

        return implode("\n", $msg) . "\n\n" . $contents->renderMIMEPart($part);
    }


    /**
     * Return the content-type.
     *
     * @return string  The content-type of the message.
     */
    function getType()
    {
        return 'text/html; charset=' . NLS::getCharset();
    }

    /**
     * Returns an error string for a malformed RFC 3464 message.
     *
     * @param MIME_Contents &$contents  The MIME_Contents object for this
     *                                  message.
     *
     * @return string  The error message string.
     */
    function _errorMsg(&$contents)
    {
        return _("This message contains mail delivery status information, but the format of this message is unknown.");
    }

}
