<?php
/**
 * The MIME_Viewer_rfc822 class renders out messages from the
 * message/rfc822 content type.
 *
 * $Horde: framework/MIME/MIME/Viewer/rfc822.php,v 1.3 2004/04/17 14:19:53 jan Exp $
 *
 * Copyright 2002-2004 Michael Slusarz <slusarz@bigworm.colorado.edu>
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@bigworm.colorado.edu>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Mime_Viewer
 */
class MIME_Viewer_rfc822 extends MIME_Viewer {

    /**
     * Render out the currently set contents.
     *
     * @access public
     *
     * @param optional array $params  An array with any parameters needed.
     *
     * @return string  The rendered text.
     */
    function render($params = array())
    {
        $part = $this->mime_part;
        $part->transferDecodeContents();

        $text = $part->getContents();
        if (!$text) {
            require_once 'Horde/MIME/Contents.php';
            $contents = &new MIME_Contents(new MIME_Part());
            return $contents->formatStatusMsg(_("There was an error displaying this message part"));
        } else {
            return $text;
        }
    }

    /**
     * Render out attachment information.
     *
     * @access public
     *
     * @param optional array $params  An array with any parameters needed.
     *
     * @return string  The rendered text in HTML.
     */
    function renderAttachmentInfo($params = array())
    {
        $msg = '';

        /* Get the text of the part.  Since we need to look for the end of
         * the headers by searching for the CRLFCRLF sequence, use
         * getCanonicalContents() to make sure we are getting the text with
         * CRLF's. */
        $text = $this->mime_part->getCanonicalContents();

        /* Search for the end of the header text (CRLFCRLF). */
        $text = substr($text, 0, strpos($text, "\r\n\r\n"));

        /* Get the list of headers now. */
        require_once 'Horde/MIME/Structure.php';
        $headers = &MIME_Structure::parseMIMEHeaders($text, true, true);

        require_once 'Horde/MIME/Contents.php';
        $contents = &new MIME_Contents(new MIME_Part());
        $msg = $contents->formatStatusMsg(_("The following are the headers for this message/rfc822 message."), '<img src="' . $GLOBALS['registry']->getParam('webroot') . '/graphics/info_icon.gif" height="16" width="16" border="0" alt="' . _("Info") . '" />', false);

        $msg .= '<span class="fixed">';

        $header_array = array(
            'date' => _("Date"),
            'subject' => _("Subject"),
            'from' => _("From"),
            'to' => _("To")
        );
        $header_output = array();
 
        foreach ($header_array as $key => $val) {
            if (isset($headers[$key])) {
                $header_output[] = '<b>' . $val . ':</b> ' . htmlspecialchars($headers[$key]);
            }
        }

        $msg .= implode("<br />\n", $header_output) . '</span>';

        return $msg;
    }

    /**
     * Return the MIME content type for the rendered data.
     *
     * @access public
     *
     * @return string  The content type of the data.
     */
    function getType()
    {
        return 'text/plain';
    }

}
