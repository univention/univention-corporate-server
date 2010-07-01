<?php
/**
 * The IMP_MIME_Viewer_status class handles multipart/report messages
 * that refer to mail system administrative messages (RFC 3464).
 *
 * $Horde: imp/lib/MIME/Viewer/status.php,v 1.17.10.13 2009-01-06 15:24:09 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package Horde_MIME_Viewer
 */
class IMP_MIME_Viewer_status extends MIME_Viewer {

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
            return '<pre>' . $contents->renderMIMEPart($part) . '</pre>';
        }

        global $registry;

        /* RFC 3464 [2]: There are three parts to a delivery status
           multipart/report message:
             (1) Human readable message
             (2) Machine parsable body part (message/delivery-status)
             (3) Returned message (optional)

           Information on the message status is found in the 'Action' field
           located in part #2 (RFC 2464 [2.3.3]). It can be either 'failed',
           'delayed', 'delivered', 'relayed', or 'expanded'. */
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

        /* Get the correct text strings for the action type. */
        switch ($action) {
        case 'failed':
        case 'delayed':
            $graphic = 'alerts/error.png';
            $alt = _("Error");
            $msg = array(
                _("ERROR: Your message could not be delivered."),
                _("The mail server generated the following error message:")
            );
            $detail_msg =  _("Additional message error details can be viewed %s.");
            $detail_msg_status = _("Additional message error details");
            $msg_link = _("The text of the returned message can be viewed %s.");
            $msg_link_status = _("The text of the returned message");
            break;

        case 'delivered':
        case 'expanded':
        case 'relayed':
            $graphic = 'alerts/success.png';
            $alt = _("Success");
            $msg = array(
                _("Your message was successfully delivered."),
                _("The mail server generated the following message:")
            );
            $detail_msg =  _("Additional message details can be viewed %s.");
            $detail_msg_status = _("Additional message details");
            $msg_link = _("The text of the message can be viewed %s.");
            $msg_link_status = _("The text of the message");
            break;

        default:
            $graphic = '';
            $alt = '';
            $msg = '';
            $detail_msg = '';
            $detail_msg_status = '';
            $msg_link = '';
            $msg_link_status = '';
        }

        /* Print the human readable message. */
        $part = $contents->getDecodedMIMEPart($this->mime_part->getRelativeMIMEId(1));
        if (empty($part)) {
            return $this->_errorMsg($contents);
        }

        $statusimg = Horde::img($graphic, $alt, 'height="16" width="16"', $registry->getImageDir('horde'));
        $text = $contents->formatStatusMsg($msg, $statusimg);
        $text .= '<blockquote>' . $contents->renderMIMEPart($part) . '</blockquote>' . "\n";

        /* Display a link to more detailed error message. */
        $detailed_msg = array(
            sprintf($detail_msg, $contents->linkViewJS($part2, 'view_attach', _("HERE"), $detail_msg_status))
        );

        /* Display a link to the returned message. Try to download the
           text of the message/rfc822 part first, if it exists.
           TODO: Retrieving by part ID 3.0 is deprecated.  Remove this once
           Horde 4.0 is released. */
        if (($part = $contents->getDecodedMIMEPart($this->mime_part->getRelativeMIMEId(3))) ||
            ($part = $contents->getDecodedMIMEPart($this->mime_part->getRelativeMIMEId('3.0')))) {
            $detailed_msg[] = sprintf($msg_link, $contents->linkViewJS($part, 'view_attach', _("HERE"), $msg_link_status, null, array('ctype' => 'message/rfc822')));
        }

        $infoimg = Horde::img('info_icon.png', _("Info"), 'height="16" width="16"', $registry->getImageDir('horde'));
        $text .= $contents->formatStatusMsg($detailed_msg, $infoimg, false);

        return $text;
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
        $err_msg = array(
            _("This message contains mail delivery status information, but the format of this message is unknown."),
            _("Below is the raw text of the status information message.")
        );
        $img = Horde::img('alerts/error.png', _("Error"), 'height="16" width="16"', $GLOBALS['registry']->getImageDir('horde'));

        $text = $contents->formatStatusMsg($err_msg, $img);

        /* There is currently no BC way to obtain all parts from a message
         * and display the summary of each part.  So instead, display the
         * entire raw contents of the message. See Bug 3757. */
        $text .= '<pre>';
        if (is_a($contents, 'IMP_Contents')) {
            $contents->rebuildMessage();
            $message = $contents->getMIMEMessage();
            $text .= $contents->toString($message, true);
        } else {
            $text .= htmlspecialchars($this->mime_part->getContents());
        }

        return $text . '</pre>';
    }

}
