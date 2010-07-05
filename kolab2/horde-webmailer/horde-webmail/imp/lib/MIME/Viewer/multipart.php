<?php
/**
 * The IMP_MIME_Viewer_multipart class handles multipart messages not
 * rendered by any specific MIME_Viewer.
 *
 * $Horde: imp/lib/MIME/Viewer/multipart.php,v 1.13.10.10 2009-01-06 15:24:09 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package Horde_MIME_Viewer
 */
class IMP_MIME_Viewer_multipart extends MIME_Viewer {

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

        $parts = $this->mime_part->getParts();
        foreach ($parts as $part) {
            $contents->buildMessagePart($part);
        }
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
