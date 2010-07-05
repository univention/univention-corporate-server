<?php
/**
 * The MIMP_MIME_Viewer_plain class renders out text/plain MIME parts.
 *
 * $Horde: mimp/lib/MIME/Viewer/plain.php,v 1.14.2.4 2009-01-06 15:24:54 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @package Horde_MIME_Viewer
 */
class MIMP_MIME_Viewer_plain extends MIME_Viewer {

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

        // Filter bad language.
        $text = IMP::filterText(trim($text));

        return $text;
    }

}
