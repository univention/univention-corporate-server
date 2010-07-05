<?php
/**
 * The MIMP_MIME_Viewer_html class renders out text/html MIME parts
 * for MIMP, stripping the HTML so that the text can be safely
 * converted to WML/CHTML/whatever is needed.
 *
 * $Horde: mimp/lib/MIME/Viewer/html.php,v 1.12.2.4 2009-01-06 15:24:54 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @package Horde_MIME_Viewer
 */
class MIMP_MIME_Viewer_html extends MIME_Viewer {

    /**
     * Render out the currently set contents in HTML or plain text
     * format. The $mime_part class variable has the information to
     * render out, encapsulated in a MIME_Part object.
     */
    function render($params)
    {
        $contents = &$params[0];

        $text = $this->mime_part->getContents();

        if ($text === false) {
            return _("There was an error displaying this message part");
        }

        require_once 'Horde/Text/Filter.php';
        $text = Text_Filter::filter($text, 'html2text');

        // Filter bad language.
        $text = IMP::filterText($text);

        return $text;
    }

    /**
     * Return the content-type.
     *
     * @return string  The content-type of the output.
     */
    function getType()
    {
        return 'text/plain';
    }

}
