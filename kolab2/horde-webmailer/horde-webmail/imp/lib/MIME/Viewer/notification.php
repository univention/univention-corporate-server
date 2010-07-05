<?php
/**
 * The IMP_MIME_Viewer_notification class handles multipart/report messages
 * that refer to mail notification messages (RFC 2298).
 *
 * $Horde: imp/lib/MIME/Viewer/notification.php,v 1.14.10.12 2009-01-06 15:24:09 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package Horde_MIME_Viewer
 */
class IMP_MIME_Viewer_notification extends MIME_Viewer {

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

        /* If this is a straight message/disposition-notification part, just
           output the text. */
        if ($this->mime_part->getType() == 'message/disposition-notification') {
            $part = new MIME_Part('text/plain');
            $part->setContents($this->mime_part->getContents());
            return '<pre>' . htmlspecialchars($contents->renderMIMEPart($part)) . '</pre>';
        }

        global $registry;

        /* RFC 2298 [3]: There are three parts to a delivery status
           multipart/report message:
             (1) Human readable message
             (2) Machine parsable body part (message/disposition-notification)
             (3) Original message (optional) */

        /* Print the human readable message. */
        $part = $contents->getDecodedMIMEPart($this->mime_part->getRelativeMIMEId(1));
        $status = array(
            _("A message you have sent has resulted in a return notification from the recipient."),
            _("The mail server generated the following informational message:")
        );
        $statusimg = Horde::img('alerts/message.png', _("Attention"), 'height="16" width="16"', $registry->getImageDir('horde'));
        $text = $contents->formatStatusMsg($status, $statusimg) .
            '<blockquote>' . $contents->renderMIMEPart($part) . '</blockquote>' . "\n";

        /* Display a link to more detailed message. */
        $part = $contents->getDecodedMIMEPart($this->mime_part->getRelativeMIMEId(2));
        if ($part) {
            $statusimg = Horde::img('info_icon.png', _("Info"), 'height="16" width="16"', $registry->getImageDir('horde'));
            $status = array(sprintf(_("Additional information can be viewed %s."), $contents->linkViewJS($part, 'view_attach', _("HERE"), _("Additional information details"))));
        }

        /* Display a link to the sent message. Try to download the text of
           the message/rfc822 part first, if it exists. */
        if (($part = $contents->getDecodedMIMEPart($this->mime_part->getRelativeMIMEId('3.0'))) ||
            ($part = $contents->getDecodedMIMEPart($this->mime_part->getRelativeMIMEId(3)))) {
            $status[] = sprintf(_("The text of the sent message can be viewed %s."), $contents->linkViewJS($part, 'view_attach', _("HERE"), _("The text of the sent message")));
        }

        $text .= $contents->formatStatusMsg($status, $statusimg, false);

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

}
